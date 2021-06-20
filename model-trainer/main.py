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
import time
import threading
import pika
import json
from pymongo import MongoClient
from bson.son import SON
import redis

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

train_namespace = "response_time_per_endpoint"

if 'REDIS_HOST' in os.environ:
    redis_host = os.environ['REDIS_HOST']
else:
    redis_host = 'localhost'
if 'REDIS_PORT' in os.environ:
    redis_port = os.environ['REDIS_PORT']
else:
    redis_port = '6379'
logger.info('Using Redis at: %s:%s', redis_host, redis_port)
redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=0)

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

if 'RABBITMQ_HOST' in os.environ:
    rabbitmq_host = os.environ['RABBITMQ_HOST']
    logger.info('Using RabbitMQ host: %s', rabbitmq_host)
else:
    logger.fatal('Missing RABBITMQ_HOST environment variable.')
    sys.exit()

if 'RABBITMQ_EXCHANGE' in os.environ:
    rabbitmq_exchange = os.environ['RABBITMQ_EXCHANGE']
    logger.info('RabbitMQ exchange: %s', rabbitmq_exchange)
else:
    logger.fatal('Missing RABBITMQ_EXCHANGE environment variable.')
    sys.exit()

connected = False
while not connected:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
        channel = connection.channel()
        result = channel.queue_declare(queue = '', exclusive = True)
        queue_name = result.method.queue
        channel.queue_bind(exchange = rabbitmq_exchange, queue = queue_name)
        connected = True
    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
        logger.info('Waiting before retrying RabbitMQ connection...')
        time.sleep(5)



def training_thread():
    while True:
        try_train_aggregates()
        time.sleep(2)

def try_train_aggregates():
    try:
        with redis_client.lock(train_namespace + "/train_mutex", blocking_timeout=5):
            train_aggregates()
            time.sleep(60)
    except redis.exceptions.LockError:
        logger.info("Could not acquire lock for training.")

def train_aggregates():
    logger.info("train_aggregates():")
    pipeline = [
        {"$group": {"_id": "$aggregated_http_path", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]
    aggregates = list(collection.aggregate(pipeline))
    for aggregate in aggregates:
        if aggregate['count'] > 100:
            id = aggregate['_id']
            count = aggregate['count']
            if id and count:
                redis_client.set(id, count)
                logger.info("aggregate: %s  -> %d", aggregate['_id'], aggregate['count'])

def evaluate_message(data):
    aggregated_http_path = data.get('aggregated_http_path')
    http_path = data.get('http_path')
    if aggregated_http_path:
        redis_info = redis_client.get(aggregated_http_path)
        if redis_info:
            logger.info("Value from Redis = %d", int(redis_info))
            if int(redis_info) > 1000:
                logger.info("Evaluated %s as normal", http_path)
            else:
                logger.info("Unknown evaluation for %s ", http_path)

def run_queue_listener():

    def callback(channel, method, properties, body):
        data = json.loads(body)
        evaluate_message(data)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    try:
        training_thread = threading.Thread(target=training_thread)
        training_thread.start()
        run_queue_listener()
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
