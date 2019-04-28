"""
This is for debugging. Use with `collectd -fC <CONF>`.
"""

import collectd
import sys
import re

def cb_write(values):
	collectd.info('write_info: {}'.format(repr(values)))

collectd.register_write(cb_write)
