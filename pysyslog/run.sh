#!/usr/bin/env python

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

HOST, PORT = "0.0.0.0", 514

import os
import sys
import logging
import json
import re
import socketserver
import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

haproxy_log_format = re.compile(r"^.* ([^ ]+) ([^ ]+)/([^ ]+) ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+) ([0-9]+) [^ ]+ [^ ]+ [^ ]+ ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+)/([0-9]+) \"([A-Z]+) ([^ ]+) ([^ ]+)\".*$")


if 'DETECTOR_HOST' in os.environ:
	detector_host = os.environ['DETECTOR_HOST']
	logger.info("Sending data to: " + detector_host)
else:
	logger.fatal("Missing DETECTOR_HOST environment variable.")
	sys.exit()

class SyslogUDPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		data = bytes.decode(self.request[0].strip())
		socket = self.request[1]
		search = haproxy_log_format.search(str(data))
		if search:
			data = search.groups()
			log_entry = {
				"frontend":									data[0],
				"backend":									data[1],
				"server":									data[2],
				"time_to_receive_request":					data[3],
				"time_in_queue":							data[4],
				"time_to_tcp_connect":						data[5],
				"time_to_get_response":						data[6],
				"total_time_active":						data[7],
				"http_status":								data[8],
				"bytes_count":								data[9],
				"concurrent_connections_haproxy":			data[10],
				"concurrent_connections_frontend":			data[11],
				"concurrent_connections_backend":			data[12],
				"concurrent_active_connections_on_server":	data[13],
				"connection_retry_attempts":				data[14],
				"queue1":									data[15],
				"queue2":									data[16],
				"http_verb":								data[17],
				"http_path":								data[18],
				"http_protocol":							data[19]
			}
			try:
				response = requests.post('http://' + detector_host + '/evaluate', data = log_entry)
			except:
				logger.debug("Error: Could not send data to " + detector_host)
		else:
			logger.warning("Ignoring data: " + str(data))

if __name__ == "__main__":
	try:
		server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
		server.serve_forever(poll_interval=0.5)
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		logger.info("Shutting down.")
