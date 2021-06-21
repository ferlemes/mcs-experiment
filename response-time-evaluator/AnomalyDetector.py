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

import logging
import redis

import time
from bson.son import SON

logger = logging.getLogger()

class AnomalyDetector:

    def __init__(self, mongo_database, mongo_collection, redis_client):
        logger.info('Initializing anomaly detector.')
        self.namespace = 'response_time_per_endpoint'
        self.mongo_collection = mongo_database[mongo_collection]
        self.redis_client = redis_client

    def training_thread(self):
        while True:
            try:
                with self.redis_client.lock(self.namespace + "/train_mutex", blocking_timeout=5):
                    self.do_train()
                    time.sleep(60)
            except redis.exceptions.LockError:
                logger.info("Could not acquire lock for training.")
                time.sleep(15)

    def do_train(self):
        logger.info("train_aggregates():")
        pipeline = [
            {"$group": {"_id": "$aggregated_http_path", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]
        aggregates = list(self.mongo_collection.aggregate(pipeline))
        for aggregate in aggregates:
            if aggregate['count'] > 100:
                id = aggregate['_id']
                count = aggregate['count']
                if id and count:
                    self.redis_client.set(id, count)
                    logger.info("aggregate: %s  -> %d", aggregate['_id'], aggregate['count'])

    def evaluate(self, data):
        aggregated_http_path = data.get('aggregated_http_path')
        http_path = data.get('http_path')
        if aggregated_http_path:
            redis_info = self.redis_client.get(aggregated_http_path)
            if redis_info:
                logger.info("Value from Redis = %d", int(redis_info))
                if int(redis_info) > 1000:
                    logger.info("Evaluated %s as normal", http_path)
                else:
                    logger.info("Unknown evaluation for %s ", http_path)
