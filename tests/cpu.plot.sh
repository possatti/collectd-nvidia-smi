#!/usr/bin/env bash

rrdtool graph $PWD/cpu.png \
    DEF:cpu-0=/tmp/collectd_cpu_test/nibelheim/cpu-0/cpu-user.rrd:value:AVERAGE \
    LINE1:cpu-0#FF0000:"CPU 0"


if [[ "$?" == "0" ]]; then
    feh cpu.png
fi