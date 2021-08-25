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
import random

logger = logging.getLogger()

class AnomalyDetector:

    def __init__(self):
        logger.info('Initializing anomaly detector.')
        self.namespace = 'anomaly-detector'

    def training_thread(self, http_records_collection, redis_client):
        try:
            with redis_client.lock(self.namespace + "/train_mutex", blocking_timeout=5):
                self.do_train(http_records_collection, redis_client)
        except redis.exceptions.LockError:
            logger.info("Could not acquire lock for training.")
            time.sleep(15)

    def do_train(self, http_records_collection, redis_client):
        logger.info("train_aggregates():")
        pipeline = [
            {"$group": {"_id": "$aggregate_id", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]
        aggregates = list(http_records_collection.aggregate(pipeline))
        for aggregate in aggregates:
            id = aggregate['_id']
            count = aggregate['count']
            if id and count > 10000:
                sample_percentage = 10000 / count
                chunk_range = int(sample_percentage * 65535)
                chunk_start = random.randint(0, int((1 - sample_percentage) * 65535))
                chunk_end = chunk_start + chunk_range
                training_data = []
                for http_record in http_records_collection.find({ "aggregate_id": id, "random": { "$gte": chunk_start, "$lte": chunk_end } }):
                    line = self.prepare_data(http_record)
                    training_data.append(line)
                training_data = np.matrix(training_data)
                logger.info("Training aggregated path '%s' with %d samples", id, training_data.shape[0])
                model = svm.OneClassSVM(nu=0.01, kernel="rbf", gamma='scale')
                model.fit(training_data)
                redis_client.set(self.namespace + '/' + id, pickle.dumps(model))

    def is_anomalous(self, redis_client, data):
        aggregate_id = data.get('aggregate_id')
        if aggregate_id:
            serialized_model = redis_client.get(self.namespace + '/' + aggregate_id)
            if serialized_model:
                model = pickle.loads(serialized_model)
                data_to_evaluate = np.matrix(self.prepare_data(data))
                result = model.predict(data_to_evaluate)
                if result[0] == -1:
                    return True
        return False

    def prepare_data(self, data):
        processed_data = [
            int(data.get("bytes_sent", 0)),
            int(data.get("bytes_received", 0)),
            int(data.get("http_status", 0)),
            int(data.get("duration", 0))
        ]
        return processed_data
