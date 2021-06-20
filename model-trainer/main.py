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
from pymongo import MongoClient
from bson.son import SON
import redis

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
                redis.set(id, count)
                logger.info("aggregate: %s  -> %d", aggregate['_id'], aggregate['count'])


if __name__ == "__main__":
    try:
        while True:
            train_aggregates()
            time.sleep(15)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info("Shutting down.")
