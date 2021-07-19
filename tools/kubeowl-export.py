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



try:
    client = MongoClient(mongo_url)
    database = client[mongo_database]
    collection = database[mongo_collection]
    collection.create_index([('timestamp', 1)])
except:
    logger.exception('Failure creating index.')
    sys.exit()

current_file = None
current_filename = ''
current_count = 0
try:
    for each_record in collection.find().sort([('timestamp', 1)]):
        timestamp = each_record.get('timestamp')
        filename = time.strftime('%Y-%m-%d_%Hh%Mm.data', time.localtime(timestamp - (timestamp % 300)))
        if filename != current_filename:
            current_filename = filename
            if current_file:
                logger.info('%d records added.', current_count)
                current_file.close()
            logger.info('Writing to file: %s', filename)
            current_file = open(filename, 'w')
            current_count = 0
        current_file.write(json.dumps(each_record) + '\n')
        current_count += 1

except:
    logger.exception('Failure exporting records.')
    sys.exit()

# Close current file if defined.
if current_file:
    logger.info('%d records added.', current_count)
    current_file.close()
