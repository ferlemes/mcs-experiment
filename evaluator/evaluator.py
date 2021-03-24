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

from status_rate_detector import StatusRateDetector
import exceptions


class Evaluator:

    def __init__(self):
        self.anomaly_detectors = [ StatusRateDetector() ]
        self.requests_data = []
        self.new_data = 0

    def feed(self, data):
        self.requests_data.append(data)
        if len(self.requests_data) > 10000:
            self.requests_data.pop(0)
        self.new_data += 1

    def evaluate(self, data):

        if self.new_data > 1000:
            for detector in self.anomaly_detectors:
                detector.train(self.requests_data)
                self.new_data = 0

        probability = 1
        try:
            for detector in self.anomaly_detectors:
                probability *= 1 - detector.is_anomalous(data)
        except exceptions.NoTrainingException:
            return "No training available yet.", 0
        except exceptions.MissingRequiredData:
            return "Missing data.", 1
        else:
            return "Evaluated.", (1 - probability)

    def merge(self, another):
        self.requests_data += another.requests_data
        another.requests_data = []
