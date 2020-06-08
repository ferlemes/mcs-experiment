#!/bin/sh

#
# Copyright 2020, Fernando Lemes da Silva
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

echo "Starting rsyslog service in interactive mode.."
/usr/sbin/rsyslogd

touch /var/log/haproxy-traffic.log
tail -f /var/log/haproxy-traffic.log |
while read logLine; do
    outputFile="/logs/haproxy-traffic-`date +%Y-%m-%d-%Hh%Mm`.log"
    echo "${logLine}" >> ${outputFile}
done
