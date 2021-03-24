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

from anomaly_detector import AnomalyDetector
import exceptions
import math

class StatusRateDetector(AnomalyDetector):

    def __init__(self):
        self.table_of_status = {}
        self.table_of_status_count = 0
        self.table_of_last_seen = {}
        self.last_seen = []

    def train(self, data_array):
        self.table_of_status = self.process_table(data_array)
        self.table_of_status_count = 0
        for count in self.table_of_status.values():
            self.table_of_status_count += count

    def is_anomalous(self, data):
        if 'http_status' in data:
            http_status = data.get('http_status')

            # Update last seen table
            self.last_seen.append(data)
            self.table_of_last_seen.update({http_status: self.table_of_last_seen.get(http_status, 0) + 1})
            if len(self.last_seen) > 100:
                popped_status = self.last_seen.pop(0).get('http_status')
                self.table_of_last_seen.update({popped_status: self.table_of_last_seen.get(popped_status, 0) - 1})

            # Evaluate
            if self.table_of_status_count > 0:
                trained_status_percentage = self.table_of_status.get(http_status) / self.table_of_status_count
                last_seen_status_percentage = self.table_of_last_seen.get(http_status) / len(self.last_seen)
                return round(abs(trained_status_percentage - last_seen_status_percentage), 2)

            else:
                raise  exceptions.NoTrainingException()
        else:
            raise exceptions.MissingRequiredData()

    def process_table(self, data_array):
        new_table = {}
        for data in data_array:
            status = data.get('http_status')
            if status:
                new_table.update({status: new_table.get(status, 0) + 1})
        return new_table
