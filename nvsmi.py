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
	'converters_dict': {},
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

# All converters should return a string.
CONVERTERS = {
	'hex_to_dec': lambda x: str(int(x, 16)),
	'pstate': lambda x: re.match(r'P(\d+)', x).group(1),

	# "Enabled" or "Disabled"
	'enabled': lambda x: '1' if x.lower()=='enabled' else '0',

	# "Active" or "Not Active"
	'active': lambda x: '1' if x.lower()=='active' else '0',

	# This is a little ugly. Not sure if there is any legit use for this.
	'identity': lambda x: x,
}

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

	# Previously, a list of converters was used. With one converter for each
	# query, necessarily. Since most values don't need a converter, I think a
	# dictionary is better.

	_CONFIG['type_list'] = [ QUERY_TYPES[q] if q in QUERY_TYPES else 'gauge' for q in _CONFIG['query_list'] ]
	_CONFIG['converters_dict'] = { q: QUERY_CONVERTERS[q] for q in _CONFIG['query_list'] if q in QUERY_CONVERTERS }

	info('bin: {}'.format(_CONFIG['bin']))
	info('query_list: {}'.format(','.join(_CONFIG['query_list'])))
	info('type_list: {}'.format(','.join(_CONFIG['type_list'])))
	info('queries that need conversion: {}'.format(','.join(list(_CONFIG['converters_dict']))))

def nvidia_smi_query_gpu(bin_path, query_list, converters_dict, id_query='pci.bus', id_converter='hex_to_dec'):
	"""Use `nvidia-smi --query-gpu` to query devices.

	Arguments:
		bin: Path to `nvidia-smi`.
		query_list: List of queries.
		converters_dict: Dictionary with list of converters, one converter for each query.
		id_query: Query that will identify which GPU it is.
		id_converter: Function used to convert the result from `id_query`. May be `None`.
	"""

	query_string = '--query-gpu={},'.format(id_query) + ','.join(query_list)
	cmd_list = [bin_path, query_string, '--format=csv,noheader,nounits']
	process = Popen(cmd_list, stdout=PIPE)
	output, err = process.communicate()

	assert process.returncode==0, '{} exited with error code "{}"'.format(bin_path, process.returncode)

	# I don't know why, the return code doesn't seem to be enough to check if it
	# worked, so we have to check the output too. It should always start with a
	# `0` because of `pci.bus`. But that may not be the case when we use another
	# query as id.
	# FIXME: A better and more generic way to check the output might be to check
	#        if `values` from the `split` has all the queries.
	assert output.startswith('0'), 'The output from {} does not seem right'.format(bin_path)

	result = {}
	for line in output.decode().strip().split('\n'):
		values = re.split(r'\s*,\s*', line)

		# Grab GPU ID.
		gpu_id = values.pop(0)
		if id_converter is not None:
			gpu_id = CONVERTERS[id_converter](gpu_id)

		# Convert whatever needs to be converted.
		for query in converters_dict:
			converter_func = converters_dict[query]
			idx = query_list.index(query)
			values[idx] = converter_func(values[idx])

		result[gpu_id] = {
			'values': values,
		}

	return result

def cb_read(data=None):
	if not _CONFIG['query_list']:
		print('Nothing to query with.', file=sys.stderr)
		return

	readings = nvidia_smi_query_gpu(_CONFIG['bin'], _CONFIG['query_list'], _CONFIG['converters_dict'])

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

