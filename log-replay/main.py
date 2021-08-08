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
else:
	rabbitmq_queue = 'http_records'
logger.info('RabbitMQ queue: %s', rabbitmq_queue)

replay_files = []
if 'REPLAY_FILES' in os.environ:
	for path in os.environ['REPLAY_FILES'].split(','):
		replay_files.append(path.strip())
else:
	logger.error('Missing REPLAY_FILES environment variable.')
	sys.exit()


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
	logger.debug('Sendind record to RabbitMQ: %s', message)
	try:
		channel.basic_publish(exchange='',
							  routing_key=rabbitmq_queue,
							  body=message,
							  properties=pika.BasicProperties(delivery_mode = 2))
	except:
		logger.error('Error publishing record to RabbitMQ.')


if __name__ == "__main__":
	try:
		offset = None
		for filename in replay_files:
			logger.info('Replaying file: %s', filename)
			with open(filename, 'r') as file:
				lines = file.read().splitlines()
				for line in lines:
					data = json.loads(line)
					timestamp = data.get('timestamp')
					if not offset:
						offset = time.time() - timestamp
					while time.time() - offset < timestamp:
						time.sleep(0.1)
					record = {
						"timestamp":		time.time(),
						"http_host":        data.get('http_host'),
						"labels":			data.get('labels'),
						"http_protocol":	data.get('http_protocol'),
						"http_verb":		data.get('http_verb'),
						"http_path":		data.get('http_path'),
						"http_status":		data.get('http_status'),
						"bytes_sent":		data.get('bytes_sent'),
						"bytes_received":	data.get('bytes_received'),
						"duration":			data.get('duration'),
					}
					publish_message(record)
	except:
		logger.exception("Failure replaying logs.")
		connection.close()
