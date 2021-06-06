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

HOST, PORT = "0.0.0.0", 514

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

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

# connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
# channel = connection.channel()
# channel.queue_declare(queue='http_requests')
#
# def publish_message(message):
# 	channel.basic_publish(exchange='',
# 						  routing_key='http_requests',
# 						  body=message,
# 						  properties=pika.BasicProperties(delivery_mode = 2))
#
def insert_into_database(data):
	message = json.dumps(data)
	logger.info('Sendind document to MongoDB: %s', message)
	try:
		collection.insert_one(data)
	except:
		logger.error('Error sending data to MongoDB.')


def main():
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
	channel = connection.channel()

	channel.queue_declare(queue='hello')

	def callback(channel, method, properties, body):
		data = json.loads(body)
		insert_into_database(data)

	channel.basic_consume(queue='http_requests', on_message_callback=callback, auto_ack=True)

	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()

if __name__ == "__main__":
	try:
		main()
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		logger.info("Shutting down.")
		connection.close()
