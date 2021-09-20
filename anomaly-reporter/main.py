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
from pymongo import MongoClient
from bson.son import SON
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


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


service_ok = False
records_processed = 0
flask_app = Flask(__name__)
metrics = PrometheusMetrics(flask_app)
aggregated_http_path_dict = {}
anomaly_gauge = Gauge('kubeowl_anomalies',
                      'Percentage of anomalies for a given endpoint.',
                      ['aggregate_id', 'aggregated_http_path'])
metrics_dict = {}


@flask_app.route('/healthcheck')
@metrics.do_not_track()
def healthcheck():
    if service_ok:
        return 'OK', 200
    else:
        return 'NOK', 400


# Create indexes
client = MongoClient(mongo_url)
database = client[mongo_database]
http_records_collection = database[mongo_http_records]
http_records_collection.create_index([("aggregate_id", 1), ("timestamp", 1)])
http_records_collection.create_index([("timestamp", 1)])
anomalies_collection = database[mongo_anomalies]
anomalies_collection.create_index([("aggregate_id", 1)])
anomalies_collection.create_index([("timestamp", 1)])
anomalies_collection.create_index([("aggregate_id", 1), ("timestamp", 1)])


def get_aggregated_http_path(id, collection):
    result = aggregated_http_path_dict.get(id)
    if not result:
        a_record = collection.find_one({ "aggregate_id": id })
        result = a_record.get("aggregated_http_path")
        aggregated_http_path_dict[id] = result
    return result

def report_anomaly_rate(anomalies_to_report):

    # Set to zero metrics that were not sent to update
    for key, value in metrics_dict.items():
        anomaly = value.get('anomaly')
        if not anomalies_to_report.get(key + '/' + anomaly):
            value.set(0)

    # Update anomalies values
    for key, value in anomalies_to_report.items():
        path = value.get('path')
        anomaly = value.get('anomaly')
        rate = value.get('rate')
        percentage = round(rate * 100, 2)
        logger.info('Anomaly detected for aggregate_id=%s (aggregated_http_path %s) with %.2f%%', key, path, percentage)
        metric = metrics_dict.get(key + '/' + anomaly)
        if not metric:
            metric = anomaly_gauge.labels(aggregate_id=key, aggregated_http_path=path, anomaly=anomaly)
            metrics_dict[key] = metric
        metric.set(percentage)


def run_reporter():
    global service_ok
    while True:
        next_execution_timestamp = int(time.time()) - (int(time.time()) % 60)
        try:
            window_sizes = [180, 240, 300]
            client = MongoClient(mongo_url)
            database = client[mongo_database]
            anomalies_collection = database[mongo_anomalies]
            http_records_collection = database[mongo_http_records]
            service_ok = True
            while True:
                logger.info('Starting evaluating anomalies.')
                anomalies_to_report = {}
                for window_size in window_sizes:
                    now = time.time()
                    pipeline = [
                        { "$match": { "timestamp": { "$gte": now - window_size, "$lt": now } } },
                        { "$group": {"_id": { "aggregate_id": "$aggregate_id", "anomaly": "$anomaly" }, "count": {"$sum": 1} } },
                        { "$sort": SON([ ("count", -1), ("_id", -1) ]) }
                    ]
                    anomalies_aggregates = list(anomalies_collection.aggregate(pipeline))
                    logger.info("anomalues_aggregates=%s", str(anomalies_aggregates))
                    http_requests_aggregates = list(http_records_collection.aggregate(pipeline))
                    http_requests_aggregates_dict = {}
                    for http_requests_aggregate in http_requests_aggregates:
                        http_requests_aggregates_dict[http_requests_aggregate.get("_id").get("aggregate_id")] = http_requests_aggregate.get("count")
                    for anomalies_aggregate in anomalies_aggregates:
                        aggregate_id = anomalies_aggregate.get("_id").get("aggregate_id")
                        anomaly = anomalies_aggregate.get("anomaly")
                        count = anomalies_aggregate.get("count")
                        if count > 5 and not anomalies_to_report.get(aggregate_id):
                            rate = count / http_requests_aggregates_dict.get(aggregate_id)
                            anomalies_to_report[aggregate_id] = {
                                'path': get_aggregated_http_path(aggregate_id, anomalies_collection),
                                'anomaly': anomaly,
                                'rate': rate
                            }
                logger.info('Done evaluating anomalies.')
                report_anomaly_rate(anomalies_to_report)
                next_execution_timestamp += 60
                nap_time = next_execution_timestamp - int(time.time())
                if nap_time > 0:
                    time.sleep(nap_time)
        except:
            service_ok = False
            logger.exception("Failure at reporter thread.")
            time.sleep(15)


if __name__ == "__main__":
    try:
        training_thread = threading.Thread(target=run_reporter)
        training_thread.start()
        flask_app.run(host='0.0.0.0', port=80)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
