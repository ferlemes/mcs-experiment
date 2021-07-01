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
from AnomalyDetector import AnomalyDetector
import redis
from flask import Flask

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

if 'MONGO_URL' in os.environ:
    mongo_url = os.environ['MONGO_URL']
    logger.info('Using mongo URL: %s', mongo_url)
else:
    logger.fatal('Missing MONGO_URL environment variable.')
    sys.exit()

if 'MONGO_DATABASE' in os.environ:
    mongo_database = os.environ['MONGO_DATABASE']
    logger.info('Using mongo database: %s', mongo_database)
else:
    logger.fatal('Missing MONGO_DATABASE environment variable.')
    sys.exit()

if 'MONGO_COLLECTION' in os.environ:
    mongo_collection = os.environ['MONGO_COLLECTION']
    logger.info('Using mongo collection: %s', mongo_collection)
else:
    logger.fatal('Missing MONGO_COLLECTION environment variable.')
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

if 'RABBITMQ_QUEUE' in os.environ:
    rabbitmq_queue = os.environ['RABBITMQ_QUEUE']
    logger.info('RabbitMQ queue: %s', rabbitmq_queue)
else:
    logger.fatal('Missing RABBITMQ_QUEUE environment variable.')
    sys.exit()


service_ok = False
records_processed = 0
flask_app = Flask(__name__)


@flask_app.route('/healthcheck')
def healthcheck():
    if service_ok:
        return 'OK', 200
    else:
        return 'NOK', 400


anomaly_detector = AnomalyDetector()

def run_trainer():
    global service_ok
    while True:
        try:
            client = MongoClient(mongo_url)
            database = client[mongo_database]
            redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=0)
            service_ok = True
            while True:
                anomaly_detector.training_thread(database, mongo_collection, redis_client)
                time.sleep(300)
        except:
            service_ok = False
            logger.exception("Failure at training thread.")
            time.sleep(15)


def evaluate_message(redis_client, data):
    global records_processed
    anomaly_detector.evaluate(redis_client, data)
    records_processed += 1


def run_queue_listener():
    global service_ok
    while True:

        connected = False
        while not connected:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
                channel = connection.channel()
                channel.queue_declare(queue = rabbitmq_queue, exclusive = False)
                channel.queue_bind(exchange = rabbitmq_exchange, queue = rabbitmq_queue)
                connected = True
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
                logger.info('Waiting before retrying RabbitMQ connection...')
                time.sleep(15)

        try:
            redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=0)
            def callback(channel, method, properties, body):
                data = json.loads(body)
                evaluate_message(redis_client, data)
            channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True)
            service_ok = True
            channel.start_consuming()
        except:
            service_ok = False
            logger.exception("Failure evaluating records.")
            time.sleep(15)


def run_report_records_processed():
    global records_processed
    while True:
        if records_processed > 0:
            count = records_processed
            records_processed -= count
            logger.info("%d records evaluated.", count)
        time.sleep(60)


if __name__ == "__main__":
    try:
        training_thread = threading.Thread(target=run_trainer)
        training_thread.start()
        report_records_processed_thread = threading.Thread(target=run_report_records_processed)
        report_records_processed_thread.start()
        queue_listener_thread=threading.Thread(target=run_queue_listener)
        queue_listener_thread.start()
        flask_app.run(host='0.0.0.0', port=80)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
