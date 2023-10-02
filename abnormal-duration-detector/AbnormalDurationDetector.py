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
import logging
import redis
import redis_lock
import time
from bson.son import SON
import numpy as np
from sklearn.linear_model import LogisticRegression
import pickle
import random

logger = logging.getLogger()

if 'ABNORMAL_DURATION_MIN_SECS' in os.environ:
    abnormal_duration_min_msecs = float(os.environ['ABNORMAL_DURATION_MIN_SECS'])
else:
    abnormal_duration_min_msecs = 5
logger.info('Minimal abnormal duration difference in milliseconds to consider as anomaly: %s milliseconds', abnormal_duration_min_msecs)

if 'ABNORMAL_DURATION_MIN_PERCENTAGE' in os.environ:
    abnormal_duration_min_percentage = float(os.environ['ABNORMAL_DURATION_MIN_PERCENTAGE'])
else:
    abnormal_duration_min_percentage = 5.0
logger.info('Minimal abnormal duration difference in percentage to consider as anomaly: %s %', abnormal_duration_min_percentage)
abnormal_duration_min_percentage %= 100

class AbnormalDurationDetector:

    def __init__(self):
        logger.info('Initializing anomaly detector.')
        self.namespace = 'abnormal-duration-detector'

    def training_thread(self, http_records_collection, anomalies_collection, samples_collection, redis_client):
        try:
            with redis_lock.Lock(redis_client, name=self.namespace + "/train_mutex", expire=1800, auto_renewal=True):
                self.do_train(http_records_collection, anomalies_collection, samples_collection, redis_client)
        except redis.exceptions.LockError:
            logger.info("Could not acquire lock for training.")
            time.sleep(15)

    def do_train(self, http_records_collection, anomalies_collection, samples_collection, redis_client):
        logger.info("train_aggregates():")
        now = int(time.time())
        pipeline = [
            { "$match": { "timestamp": { "$gte": now - 3600, "$lt": now } } },
            { "$group": {"_id": "$aggregate_id", "count": {"$sum": 1} } }
        ]
        last_training_annomalies = {}
        for aggregated_anomaly in anomalies_collection.aggregate(pipeline, allowDiskUse=True):
            last_training_annomalies[aggregated_anomaly.get('_id')] = aggregated_anomaly.get('count')
        pipeline = [
            {"$group": {"_id": "$aggregate_id", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]
        for aggregate in http_records_collection.aggregate(pipeline, allowDiskUse=True):
            id = aggregate['_id']
            count = aggregate['count']
            model = redis_client.get(self.namespace + '/' + id)
            if id and count > 1000 and (last_training_annomalies.get(id, 0) > 10 or not model):
                sample_percentage = 1000 / count
                chunk_range = int(sample_percentage * 65535)
                chunk_start = random.randint(0, int((1 - sample_percentage) * 65535))
                chunk_end = chunk_start + chunk_range
                samples_collection.delete_many({ "aggregate_id": id })
                training_data = []
                for http_record in http_records_collection.find({ "aggregate_id": id, "random": { "$gte": chunk_start, "$lte": chunk_end } }):
                    line = self.prepare_data(http_record)
                    training_data.append(line)
                    samples_collection.insert_one(http_record)
                training_data = np.array(training_data)
                logger.info("Training aggregated path '%s' with %d samples", id, training_data.shape[0])
                model = LogisticRegression()
                model.fit(training_data[:,0:3],training_data[:,3])
                redis_client.set(self.namespace + '/' + id, pickle.dumps(model))

    def is_anomalous(self, redis_client, data):
        aggregate_id = data.get('aggregate_id')
        if aggregate_id:
            serialized_model = redis_client.get(self.namespace + '/' + aggregate_id)
            if serialized_model:
                model = pickle.loads(serialized_model)
                data_to_evaluate = np.array([self.prepare_data(data)])
                expected_result = data_to_evaluate[:,3][0]
                result = model.predict(data_to_evaluate[:,0:3])[0]
                difference = abs(expected_result - result)
                logger.info("Request took %d ms and the predicted as %d", expected_result, result)
                if  difference > abnormal_duration_min_msecs and (difference / expected_result) > abnormal_duration_min_percentage:
                    logger.info("Request was considered anomalous!", expected_result, result)
                    return True
        return False

    def prepare_data(self, data):
        kbytes_sent = float(data.get("bytes_sent", 0))         / 1024
        kbytes_received = float(data.get("bytes_received", 0)) / 1024
        http_status = float(data.get("http_status", 0))        / 100
        duration = int(data.get("duration", 0))
        processed_data = [
            kbytes_sent,
            kbytes_received,
            http_status,
            duration
        ]
        return processed_data
