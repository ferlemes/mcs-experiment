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


class Evaluator:

    def __init__(self):
        self.requests_data = []

    def feed(self, data):
        self.requests_data.append(data)

    def evaluate(self, data):
        print("evaluating data")
        if len(self.requests_data) > 5:
            return "I didn't check the data, but it seems ok.", 1
        else:
            return None, 0

    def merge(self, another):
        self.requests_data.append(another.requests_data)
        another.requests_data = []
