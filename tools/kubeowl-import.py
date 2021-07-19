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
except:
    logger.exception('Failure connecting to database.')
    sys.exit()


files = sys.argv
del files[0]
try:
    for each_file in files:
        logger.info('Importing file: %s', each_file)
        added = 0
        duplicates = 0
        with open(each_file, 'r') as file:
            lines = file.read().splitlines()
            for line in lines:
                data = json.loads(line)
                id = data.get('_id')
                if id:
                    exists = collection.count_documents({ "_id": id })
                    if exists == 0:
                        collection.insert_one(data)
                        added += 1
                    else:
                        duplicates += 1
                else:
                    collection.insert_one(data)
                    added += 1
        if duplicates == 0:
            logger.info("Loaded %d records.", added)
        else:
            logger.info("Loaded %d records. %d were skipped due to duplicate id.", added, duplicates)

except:
    logger.exception('Failure importing records.')
    sys.exit()
