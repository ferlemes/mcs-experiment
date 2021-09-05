#!/usr/local/bin/python

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
import time
import json
import gzip


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


try:
    client = MongoClient(mongo_url)
    database = client[mongo_database]
    collection = database[mongo_http_records]
    collection.create_index([('timestamp', 1)])
except:
    logger.exception('Failure creating index.')
    sys.exit()

current_file = None
current_filename = ''
current_count = 0
arguments = sys.argv
if len(arguments) > 1:
    start = int(arguments[1])
    start = start - (start  % 3600)
else:
    logger.fatal('Missing start timestamp.')
    sys.exit()
if len(arguments) > 2:
    end = int(arguments[2])
    if end % 3600 > 0:
        end = end - (end % 3600) + 3600
else:
    logger.fatal('Missing end timestamp.')
    sys.exit()
try:
    window_start = start
    window_end = window_start + 3600
    while window_start < end:
        count = 0
        current_file = None
        for each_record in collection.find({ "timestamp": { "$gte": window_start, "$lt": window_end } }).sort([('timestamp', 1)]):
            if not current_file:
                filename = time.strftime('%Y-%m-%d_%Hh%Mm.data.gz', time.localtime(window_start))
                logger.info('Writing to file: %s', filename)
                current_file = gzip.open(filename, 'wt')
            current_file.write(json.dumps(each_record) + '\n')
            count += 1
        if count > 0:
            logger.info('%d records added.', count)
        if current_file:
            current_file.close()
            current_file = None
        window_start += 3600
        window_end += 3600

except:
    logger.exception('Failure exporting records.')
    sys.exit()

