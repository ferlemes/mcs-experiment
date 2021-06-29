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
import numpy as np
from sklearn import svm
import pickle

logger = logging.getLogger()

class AnomalyDetector:

    def __init__(self):
        logger.info('Initializing anomaly detector.')
        self.namespace = 'anomaly-detector'

    def training_thread(self, mongo_database, mongo_collection, redis_client):
        try:
            with redis_client.lock(self.namespace + "/train_mutex", blocking_timeout=5):
                self.do_train(mongo_database, mongo_collection, redis_client)
        except redis.exceptions.LockError:
            logger.info("Could not acquire lock for training.")
            time.sleep(15)

    def do_train(self, mongo_database, mongo_collection, redis_client):
        logger.info("train_aggregates():")
        mongo_collection = mongo_database[mongo_collection]
        pipeline = [
            {"$group": {"_id": "$aggregated_http_path", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]
        aggregates = list(mongo_collection.aggregate(pipeline))
        for aggregate in aggregates:
            id = aggregate['_id']
            count = aggregate['count']
            training_data = []
            if id and count > 1000:
                for http_record in mongo_collection.find({ "aggregated_http_path": id}):
                    line = self.prepare_data(http_record)
                    training_data.append(line)
                training_data = np.matrix(training_data)
                logger.info("Training aggregated path %s", id)
                model = svm.OneClassSVM(nu=0.001, kernel="rbf", gamma='scale')
                model.fit(training_data)
                redis_client.set(id, pickle.dumps(model))

    def evaluate(self, redis_client, data):
        aggregated_http_path = data.get('aggregated_http_path')
        if aggregated_http_path:
            serialized_model = redis_client.get(aggregated_http_path)
            if serialized_model:
                model = pickle.loads(serialized_model)
                data_to_evaluate = np.matrix(self.prepare_data(data))
                result = model.predict(data_to_evaluate)
                if result[0] == -1:
                    logger.info("Abnormal data found: %s", str(data))

    def prepare_data(self, data):
        processed_data = [
            int(data.get("bytes_sent", 0)),
            int(data.get("bytes_received", 0)),
            int(data.get("http_status", 0)),
            int(data.get("request_time", 0))
        ]
        return processed_data
