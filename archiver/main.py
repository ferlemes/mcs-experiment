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
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics


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
    mongo_anomalies = 'anomalies'
logger.info('HTTP anomalies collection is: %s', mongo_anomalies)

if 'ARCHIVE_RECORDS_AFTER' in os.environ:
    archive_records_after = int(os.environ['ARCHIVE_RECORDS_AFTER'])
else:
    archive_records_after = 31536000 # One year
logger.info('Archiving records from MongoDB after: %d seconds', archive_records_after)


service_ok = False
flask_app = Flask(__name__)
metrics = PrometheusMetrics(flask_app)
counter = metrics.info('archived_records', 'Number of archived records')
counter.set(0)


@flask_app.route('/healthcheck')
@metrics.do_not_track()
def healthcheck():
    if service_ok:
        return 'OK', 200
    else:
        return 'NOK', 400


def run_archiver():
    global service_ok
    while True:
        try:
            client = MongoClient(mongo_url)
            database = client[mongo_database]
            service_ok = True
            while True:
                archive_records(mongo_http_records, database)
                archive_records(mongo_anomalies, database)
                time.sleep(300)
        except:
            service_ok = False
            logger.exception("Failure archiving records!")
            time.sleep(15)
            raise


def archive_records(collection_name, database):
    collection = database[collection_name]
    remove_older_than = int(time.time()) - archive_records_after
    result = collection.delete_many({ "timestamp": { "$lt": remove_older_than } })
    if result:
        counter.inc(result.deleted_count)
        logger.info("Removed %d records from %s.", result.deleted_count, collection_name)
    else:
        logger.info("No records to remove from %s.", collection_name)


if __name__ == "__main__":
    try:
        training_thread = threading.Thread(target=run_archiver)
        training_thread.start()
        flask_app.run(host='0.0.0.0', port=80)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
