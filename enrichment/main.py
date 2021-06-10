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
from pymongo import MongoClient
import json
import pika

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

#
# Retrieve RabbitMQ settings
#
if 'RABBITMQ_HOST' in os.environ:
	rabbitmq_host = os.environ['RABBITMQ_HOST']
	logger.info('Using RabbitMQ host: %s', rabbitmq_host)
else:
	logger.fatal('Missing RABBITMQ_HOST environment variable.')
	sys.exit()

if 'RABBITMQ_INPUT_QUEUE' in os.environ:
	rabbitmq_input_queue = os.environ['RABBITMQ_INPUT_QUEUE']
	logger.info('RabbitMQ input queue: %s', rabbitmq_input_queue)
else:
	logger.fatal('Missing RABBITMQ_INPUT_QUEUE environment variable.')
	sys.exit()

if 'RABBITMQ_OUTPUT_QUEUE' in os.environ:
	rabbitmq_output_queue = os.environ['RABBITMQ_OUTPUT_QUEUE']
	logger.info('RabbitMQ output queue: %s', rabbitmq_output_queue)
else:
	logger.fatal('Missing RABBITMQ_OUTPUT_QUEUE environment variable.')
	sys.exit()

if 'MONGO_URL' in os.environ:
	mongo_url = os.environ['MONGO_URL']
	client = MongoClient(mongo_url)
	logger.info('Using mongo URL: %s', mongo_url)
else:
	logger.fatal('Missing MONGO_URL environment variable.')
	sys.exit()

if 'MONGO_DATABASE' in os.environ:
	mongo_database = os.environ['MONGO_DATABASE']
	database = client[mongo_database]
	collection = database.haproxy_records
	logger.info('Using mongo database: %s', mongo_database)
else:
	logger.fatal('Missing MONGO_DATABASE environment variable.')
	sys.exit()



connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_input_queue)
if rabbitmq_output_queue != "null":
	channel.queue_declare(queue=rabbitmq_output_queue)

def publish_message(data):
	if rabbitmq_output_queue == "null":
		return
	message = json.dumps(data)
	logger.debug('Sending processed document to RabbitMQ: %s', message)
	try:
		channel.basic_publish(exchange='',
							  routing_key=rabbitmq_output_queue,
							  body=message,
							  properties=pika.BasicProperties(delivery_mode = 2))
	except:
		logger.error('Error sending data to RabbitMQ.')

def insert_into_database(data):
	logger.debug('Sending processed document to MongoDB: %s', json.dumps(data))
	try:
		collection.insert_one(data)
	except:
		logger.error('Error sending data to MongoDB.')

def enrich_data(data):
	data['enriched'] = True
	return data

def run_queue_listener():

	def callback(channel, method, properties, body):
		data = json.loads(body)
		data = enrich_data(data)
		insert_into_database(dict(data))
		publish_message(data)

	channel.basic_consume(queue=rabbitmq_input_queue, on_message_callback=callback, auto_ack=True)
	channel.start_consuming()

if __name__ == "__main__":
	try:
		run_queue_listener()
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		logger.info("Shutting down.")
		connection.close()