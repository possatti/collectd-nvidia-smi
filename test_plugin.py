#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division

import argparse
import pprint
import sys
import os
import re

import collectd_nvidia_smi as cn

def parse_args():
	parser = argparse.ArgumentParser(description='')
	# parser.add_argument('arg')
	# parser.add_argument('-o', '--opt')
	args = parser.parse_args()
	return args

def main():
	args = parse_args()

	queries = ['pci.device', 'utilization.gpu', 'utilization.memory']
	converters = [None] * len(queries)
	result = cn.nvidia_smi_query_gpu('nvidia-smi', queries, converters)
	pprint.pprint(result)

if __name__ == '__main__':
	main()
