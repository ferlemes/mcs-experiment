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
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

#
# Retrieve syslog listener settings
#
if 'LISTEN_HOST' in os.environ:
	listen_host = os.environ['LISTEN_HOST']
else:
	listen_host = "0.0.0.0"

if 'LISTEN_PORT' in os.environ:
	listen_port = os.environ['LISTEN_PORT']
else:
	listen_port = 514
logger.info('Listening messages at: %s:%s', listen_host, listen_port)

#
# Retrieve RabbitMQ settings
#
if 'RABBITMQ_HOST' in os.environ:
	rabbitmq_host = os.environ['RABBITMQ_HOST']
	logger.info('Using RabbitMQ host: %s', rabbitmq_host)
else:
	logger.fatal('Missing RABBITMQ_HOST environment variable.')
	sys.exit()

if 'RABBITMQ_QUEUE' in os.environ:
	rabbitmq_queue = os.environ['RABBITMQ_QUEUE']
	logger.info('RabbitMQ queue: %s', rabbitmq_queue)
else:
	logger.fatal('Missing RABBITMQ_QUEUE environment variable.')
	sys.exit()

ignore_paths = []
if 'IGNORE_PATHS' in os.environ:
	for path in os.environ['IGNORE_PATHS'].split(','):
		ignore_paths.append(path.strip())
	logger.info('Ignoring HTTP paths: %s', str(ignore_paths))



haproxy_log_format = re.compile(r"^.* \[([^ ]+)\] ([^ ]+) ([^ ]+)/([^ ]+) ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+) ([0-9]+) [^ ]+ [^ ]+ [^ ]+ ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+)/([0-9]+) \"([A-Z]+) ([^ ]+) ([^ ]+)\".*$")

connected = False
while not connected:
	try:
		connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
		channel = connection.channel()
		if rabbitmq_queue != "null":
			channel.queue_declare(queue=rabbitmq_queue)
		connected = True
	except pika.exceptions.AMQPConnectionError:
		logger.info('Waiting before retrying RabbitMQ connection...')
		time.sleep(5)

def publish_message(data):
	if rabbitmq_queue == "null":
		return
	message = json.dumps(data)
	logger.debug('Sendind document to RabbitMQ: %s', message)
	try:
		channel.basic_publish(exchange='',
							  routing_key=rabbitmq_queue,
							  body=message,
							  properties=pika.BasicProperties(delivery_mode = 2))
	except:
		logger.error('Error publishing document to RabbitMQ.')

class SyslogUDPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		data = str(bytes.decode(self.request[0].strip()))
		search = haproxy_log_format.search(data)
		if search:
			record = search.groups()
			if record[19] in ignore_paths:
				return
			haproxy_record = {
				"timestamp":								record[0],
				"frontend":									record[1],
				"backend":									record[2],
				"server":									record[3],
				"http_protocol":							record[20],
				"http_verb":								record[18],
				"http_path":								record[19],
				"bytes_count":								record[10],
				"http_status":								record[9],
				"request_time":								record[7]
			}
			publish_message(haproxy_record)
		else:
			logger.info("Ignoring data: %s", data)

if __name__ == "__main__":
	try:
		server = socketserver.UDPServer((listen_host, int(listen_port)), SyslogUDPHandler)
		server.serve_forever(poll_interval=0.1)
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		logger.info("Shutting down.")
		connection.close()
