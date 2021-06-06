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

import os
import sys
import logging
import re
import socketserver
import json
import pika

HOST, PORT = "0.0.0.0", 514

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

ignore_paths = []
if 'IGNORE_PATHS' in os.environ:
	for path in os.environ['IGNORE_PATHS'].split(','):
		ignore_paths.append(path.strip())
	logger.info('Ignoring HTTP paths: %s', str(ignore_paths))

haproxy_log_format = re.compile(r"^.* \[([^ ]+)\] ([^ ]+) ([^ ]+)/([^ ]+) ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+) ([0-9]+) [^ ]+ [^ ]+ [^ ]+ ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+)/([0-9]+) \"([A-Z]+) ([^ ]+) ([^ ]+)\".*$")

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='http_requests')

def insert_into_database(data):
	message = json.dumps(data)
	logger.info('Sendind document to RabbitMQ: %s', message)
	try:
		channel.basic_publish(exchange='',
							  routing_key='http_requests',
							  body=message,
							  properties=pika.BasicProperties(delivery_mode = 2))
	except:
		logger.error('Error publishing document to RabbitMQ.')

class SyslogUDPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		data = bytes.decode(self.request[0].strip())
		socket = self.request[1]
		logger.info("String= %s", str(data))
		search = haproxy_log_format.search(str(data))
		if search:
			data = search.groups()
			if data[19] in ignore_paths:
				return
			log_entry = {
				"timestamp":								data[0],
				"frontend":									data[1],
				"backend":									data[2],
				"server":									data[3],
				"time_to_receive_request":					data[4],
				"time_in_queue":							data[5],
				"time_to_tcp_connect":						data[6],
				"time_to_get_response":						data[7],
				"total_time_active":						data[8],
				"http_status":								data[9],
				"bytes_count":								data[10],
				"concurrent_connections_haproxy":			data[11],
				"concurrent_connections_frontend":			data[12],
				"concurrent_connections_backend":			data[13],
				"concurrent_active_connections_on_server":	data[14],
				"connection_retry_attempts":				data[15],
				"queue1":									data[16],
				"queue2":									data[17],
				"http_verb":								data[18],
				"http_path":								data[19],
				"http_protocol":							data[20]
			}
			insert_into_database(log_entry)
		else:
			logger.warning("Ignoring data: %s", str(data))

if __name__ == "__main__":
	try:
		server = socketserver.UDPServer((HOST, PORT), SyslogUDPHandler)
		server.serve_forever(poll_interval=0.1)
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		logger.info("Shutting down.")
		connection.close()
