#!/bin/bash

set -e

freeMemory=`awk '/MemFree/ { print int($2/1024) }' /proc/meminfo`
XMN=$[ $freeMemory * 2 / 10 ]
XMX=$[ $freeMemory * 8 / 10 ]
XMS=$[ $freeMemory * 8 / 10 ]
export JVM_ARGS="-Xmn${XMN}m -Xms${XMS}m -Xmx${XMX}m"

sleep 60

echo "Starting Jmeter test: test_1.jmx"
jmeter -n -t /tests/test_1.jmx -l /results/test_1.jtl -j /results/test_1.log
