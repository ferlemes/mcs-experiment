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
from prometheus_flask_exporter import PrometheusMetrics


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
else:
    mongo_database = 'kubeowl'
logger.info('Using mongo database: %s', mongo_database)

if 'MONGO_HTTP_RECORDS' in os.environ:
    mongo_http_records = os.environ['MONGO_HTTP_RECORDS']
else:
    mongo_http_records = 'http_records'
logger.info('HTTP records collection is: %s', mongo_http_records)

if 'MONGO_ANOMALIES' in os.environ:
    mongo_anomalies = os.environ['MONGO_ANOMALIES']
else:
    mongo_anomalies = "anomalies"
logger.info('Anomalies collection is: %s', mongo_anomalies)

if 'RABBITMQ_HOST' in os.environ:
    rabbitmq_host = os.environ['RABBITMQ_HOST']
    logger.info('Using RabbitMQ host: %s', rabbitmq_host)
else:
    logger.fatal('Missing RABBITMQ_HOST environment variable.')
    sys.exit()

if 'RABBITMQ_EXCHANGE' in os.environ:
    rabbitmq_exchange = os.environ['RABBITMQ_EXCHANGE']
else:
    rabbitmq_exchange = "http_enriched_records"
logger.info('RabbitMQ exchange: %s', rabbitmq_exchange)

if 'RABBITMQ_QUEUE' in os.environ:
    rabbitmq_queue = os.environ['RABBITMQ_QUEUE']
else:
    rabbitmq_queue = 'evaluate_response_time'
logger.info('RabbitMQ queue: %s', rabbitmq_queue)


service_ok = False
records_processed = 0
flask_app = Flask(__name__)
metrics = PrometheusMetrics(flask_app)
counter = metrics.info('evaluated_records', 'Number of evaluated records')
counter.set(0)
anomaly_counter = metrics.info('abnormal_records', 'Number of abnormal records')
anomaly_counter.set(0)

@flask_app.route('/healthcheck')
@metrics.do_not_track()
def healthcheck():
    if service_ok:
        return 'OK', 200
    else:
        return 'NOK', 400


anomaly_detector = AnomalyDetector()


# Create indexes
client = MongoClient(mongo_url)
database = client[mongo_database]
collection = database[mongo_http_records]
collection.create_index([("aggregate_id", 1)])
collection.create_index([("aggregate_id", 1), ("random", 1)])


def run_trainer():
    global service_ok
    while True:
        try:
            client = MongoClient(mongo_url)
            database = client[mongo_database]
            http_records_collection = database[mongo_http_records]
            redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=0)
            service_ok = True
            while True:
                anomaly_detector.training_thread(http_records_collection, redis_client)
                time.sleep(300)
        except:
            service_ok = False
            logger.exception("Failure at training thread.")
            time.sleep(15)


def evaluate_message(anomalies_collection, redis_client, data):
    global counter, records_processed
    if anomaly_detector.is_anomalous(redis_client, data):
        anomaly_counter.inc()
        anomalies_collection.insert_one(data)
    counter.inc()
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
            client = MongoClient(mongo_url)
            database = client[mongo_database]
            anomalies_collection = database[mongo_anomalies]
            redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=0)
            def callback(channel, method, properties, body):
                data = json.loads(body)
                evaluate_message(anomalies_collection, redis_client, data)
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
            logger.info("%d records evaluated during last minute.", count)
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
