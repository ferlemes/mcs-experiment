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
import json
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

if 'ARCHIVE_FOLDER' in os.environ:
    archive_folder = os.environ['ARCHIVE_FOLDER']
else:
    archive_folder = "/tmp"
if archive_folder[-1:] == '/':
    archive_folder = archive_folder[:-1]
logger.info('Archiving records to folder: %s', archive_folder)

if 'ARCHIVE_RECORDS_AFTER' in os.environ:
    archive_records_after = int(os.environ['ARCHIVE_RECORDS_AFTER'])
else:
    archive_records_after = 31536000 # One year
logger.info('Archiving records from MongoDB after: %d seconds', archive_records_after)

if 'REMOVE_ARCHIVED_RECORDS' in os.environ:
    remove_archive_records = os.environ['REMOVE_ARCHIVED_RECORDS'].lower() == "true"
else:
    remove_archive_records = True
logger.info('Removing archived records: %s', str(remove_archive_records))


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
            collection = database[mongo_collection]
            collection.find_one()
            service_ok = True
            while True:
                archive_records(collection)
                time.sleep(300)
        except:
            service_ok = False
            logger.exception("Failure archiving records!")
            time.sleep(15)
            raise


epoch_start = 0
epoch_end = 0
def archive_records(collection):
    global epoch_start, epoch_end
    epoch_end = int(time.time()) - archive_records_after
    epoch_end = epoch_end - (epoch_end % 300) - 1
    records = list(collection.find({ "timestamp": { "$gte": epoch_start, "$lt": epoch_end } }))
    if records:
        grouped_records = {}
        for record in records:
            timestamp = record.get('timestamp')
            filename = time.strftime('%Y-%m-%d_%Hh%Mm.data', time.localtime(timestamp - (timestamp % 300)))
            if not grouped_records.get(filename):
                grouped_records[filename] = []
            grouped_records.get(filename).append(json.dumps(record))
            counter.inc()
        dump_groups_to_file(grouped_records)
    else:
        logger.info("No records to archive.")
    if remove_archive_records:
        collection.delete_many({ "timestamp": { "$gte": epoch_start, "$lt": epoch_end } })
    epoch_start = epoch_end


def dump_groups_to_file(grouped_records):
    for filename, data_array in grouped_records.items():
        records_count = 0
        filename = archive_folder + '/' + filename
        with open(filename, 'a') as file_handler:
            for each_record in data_array:
                file_handler.write(each_record + '\n')
                records_count += 1
        logger.info("Added %d records to file %s", records_count, filename)


if __name__ == "__main__":
    try:
        training_thread = threading.Thread(target=run_archiver)
        training_thread.start()
        flask_app.run(host='0.0.0.0', port=80)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
