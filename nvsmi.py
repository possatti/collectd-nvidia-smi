#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division
from subprocess import Popen, PIPE

import collectd
import sys
import os
import re

_CONFIG = {
	'bin': 'nvidia-smi',
	'query_list': [],
	'converters': [],
	'type_list': [],
}

_PLUGIN_NAME = 'nvsmi'

# From https://developer.download.nvidia.com/compute/DCGM/docs/nvidia-smi-367.38.pdf:
#     "It is recommended
#     that users desiring consistency use either UUID or PCI bus ID, since
#     device enumeration ordering is not guaranteed to be consistent between
#     reboots and board serial number might be shared between multiple GPUs
#     on the same board."
#
# Even though it's talking about the `--id` option. I don't think I should rely
# on the ordering from the output. Using `pci.bus` should be more realiable.

CONVERTERS = {
	'hex_to_dec': lambda x: str(int(x, 16)),
	'pstate': lambda x: re.match(r'P(\d+)', x).group(1),

	# "Enabled" or "Disabled"
	'enabled': lambda x: '1' if x.lower()=='enabled' else '0',

	# "Active" or "Not Active"
	'active': lambda x: '1' if x.lower()=='active' else '0',

	# FIXME: Wish I'd come with something more clever than this.
	'identity': lambda x: x,
}
# TODO: Check if more need to be added.
QUERY_CONVERTERS = {
	'pci.bus': CONVERTERS['hex_to_dec'],
	'pci.device': CONVERTERS['hex_to_dec'],
	'pci.device_id': CONVERTERS['hex_to_dec'],
	'pci.domain': CONVERTERS['hex_to_dec'],
	'pci.sub_device_id': CONVERTERS['hex_to_dec'],

	'clocks_throttle_reasons.supported': CONVERTERS['hex_to_dec'],
	'clocks_throttle_reasons.active': CONVERTERS['hex_to_dec'],
	'clocks_throttle_reasons.gpu_idle': CONVERTERS['active'],
	'clocks_throttle_reasons.applications_clocks_setting': CONVERTERS['active'],
	'clocks_throttle_reasons.sw_power_cap': CONVERTERS['active'],
	'clocks_throttle_reasons.hw_slowdown': CONVERTERS['active'],
	'clocks_throttle_reasons.hw_thermal_slowdown': CONVERTERS['active'],
	'clocks_throttle_reasons.hw_power_brake_slowdown': CONVERTERS['active'],
	'clocks_throttle_reasons.sw_thermal_slowdown': CONVERTERS['active'],
	'clocks_throttle_reasons.sync_boost': CONVERTERS['active'],

	'accounting.mode': CONVERTERS['enabled'],
	'display_active': CONVERTERS['enabled'],
	'display_mode': CONVERTERS['enabled'],
	'persistence_mode': CONVERTERS['enabled'],
	'power.management': CONVERTERS['enabled'],

	'pstate': CONVERTERS['pstate'],
}
# Assume type 'gauge' as default, but use other specific types when fit.
# I would like to only use types that are default on '/usr/share/collectd/types.db'
# to keep things simple.
QUERY_TYPES = {
	'fan.speed': 'percent',
	'utilization.gpu': 'percent',
	'utilization.memory': 'percent',

	'temperature.gpu': 'temperature',
	'temperature.memory': 'temperature',
}

def info(s):
	collectd.info('{}: {}'.format(_PLUGIN_NAME, s))

def error(s):
	collectd.error('{}: {}'.format(_PLUGIN_NAME, s))

def cb_config(config):
	global _CONFIG
	for node in config.children:
		if node.key.lower() == 'bin':
			_CONFIG['bin'] = node.values[0]
			if not os.path.isfile(_CONFIG['bin']):
				# FIXME: Is that how you do it? Maybe should throw an exception.
				collectd.error('collectd_nvidia_smi: The path ({}) provided for {} does not exist.'.format(_CONFIG['bin'], node.key))
		elif node.key.lower() == 'querygpu':
			_CONFIG['query_list'] += node.values
		else:
			info('collectd_nvidia_smi: Unknown config key "{}". Ignoring.'.format(node.key))

	_CONFIG['converters'] = [ QUERY_CONVERTERS[q] if q in QUERY_CONVERTERS else CONVERTERS['identity'] for q in _CONFIG['query_list'] ]
	_CONFIG['type_list'] = [ QUERY_TYPES[q] if q in QUERY_TYPES else 'gauge' for q in _CONFIG['query_list'] ]

	info('bin: {}'.format(_CONFIG['bin']))
	info('query_list: {}'.format(','.join(_CONFIG['query_list'])))
	info('type_list: {}'.format(','.join(_CONFIG['type_list'])))

# TODO: Instead of a list of converters, a dict of (query_name, converter). A subset of QUERY_CONVERTERS.
def nvidia_smi_query_gpu(bin, query_list, converters, id_query='pci.bus', id_converter='hex_to_dec'):
	"""Use `nvidia-smi --query-gpu` to query devices.

	Arguments:
		bin: nvidia-smi binary file.
		query_list: list of queries.
		converters: list of converters, one converter for each query.
		id_query: query that will identify which GPU it is.
		id_converter: function used to convert the result from `id_query`. May be `None`.
	"""

	assert len(query_list) == len(converters), '`query_list` and `converters` should have the same length'
	query_string = '--query-gpu={},'.format(id_query) + ','.join(query_list)
	cmd_list = [_CONFIG['bin'], query_string, '--format=csv,noheader,nounits']
	process = Popen(cmd_list, stdout=PIPE)
	output, err = process.communicate()
	# has_terminated = process.poll()
	exit_code = process.wait()

	result = {}
	for line in output.decode().strip().split('\n'):
		values = re.split(r'\s*,\s*', line)
		gpu_id = values.pop(0)
		if id_converter is not None:
			gpu_id = CONVERTERS[id_converter](gpu_id)
		converted_values = map(lambda x: x[1] if x[0] is None else x[0](x[1]), zip(converters, values))
		if type(converted_values) is not list:
			converted_values = list(converted_values)
		result[gpu_id] = {
			'values': converted_values,
		}

	return result

def cb_read(data=None):
	if not _CONFIG['query_list']:
		print('Nothing to query with.', file=sys.stderr)
		return

	readings = nvidia_smi_query_gpu(_CONFIG['bin'], _CONFIG['query_list'], _CONFIG['converters'])

	vl = collectd.Values()
	for gpu_id in readings:
		for query, value, type_ in zip(_CONFIG['query_list'], readings[gpu_id]['values'], _CONFIG['type_list']):
			# type_instance = 'gpu-{}.{}'.format(gpu_id, query)
			vl.dispatch(
				plugin=_PLUGIN_NAME,
				plugin_instance=gpu_id,
				type=type_,
				type_instance=query,
				values=[value],
			)

collectd.register_config(cb_config)
collectd.register_read(cb_read)

