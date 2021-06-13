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
import redis
import pika
import time
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

if 'REDIS_HOST' in os.environ:
    redis_host = os.environ['REDIS_HOST']
else:
    redis_host = 'localhost'
if 'REDIS_PORT' in os.environ:
    redis_port = os.environ['REDIS_PORT']
else:
    redis_port = '6379'
logger.info('Using Redis at: %s:%s', redis_host, redis_port)
redis = redis.Redis(host=redis_host, port=int(redis_port), db=0)

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



connected = False
while not connected:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_queue)
        connected = True
    except pika.exceptions.AMQPConnectionError:
        time.sleep(5)

def evaluate_message(data):
    aggregated_http_path = data.get('aggregated_http_path')
    http_path = data.get('http_path')
    if aggregated_http_path:
        redis_info = redis.get(aggregated_http_path)
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

    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    try:
        run_queue_listener()
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        connection.close()
