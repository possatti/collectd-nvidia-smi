#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division

import argparse
import pprint
import sys
import os
import re

import nvsmi

def parse_args():
	parser = argparse.ArgumentParser(description='')
	# parser.add_argument('arg')
	# parser.add_argument('-o', '--opt')
	args = parser.parse_args()
	return args

def main():
	args = parse_args()

	queries = ['pci.device', 'utilization.gpu', 'utilization.memory']
	converters_dict = { q: nvsmi.QUERY_CONVERTERS[q] for q in queries if q in nvsmi.QUERY_CONVERTERS }
	result = nvsmi.nvidia_smi_query_gpu('nvidia-smi', queries, converters_dict)
	pprint.pprint(result)

if __name__ == '__main__':
	main()
