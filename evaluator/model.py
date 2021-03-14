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

from errors import InvalidPayloadException
import numpy as np
import math


class Model:

    def __init__(self, specs):
        self.parameters = {}
        self.sampleCache = []
        self.dim = None
        self.mu = None
        self.sigma = None
        self.sigmaInv = None
        self.coefficient = 0
        if 'min_samples' in specs:
            self.parameters['min_samples'] = specs['min_samples']
        else:
            self.parameters['min_samples'] = 1000
        if 'dimension' in specs:
            self.dim = specs['dimension']

    def get_parameters(self):
        return self.parameters

    def evaluate(self, payload):
        if 'data' in payload:
            data = payload['data']
        else:
            raise InvalidPayloadException("Missing 'data' field.")
        if self.dim:
            if self.dim != len(data):
                raise InvalidPayloadException("The 'data' field has an invalid dimension.")
        else:
            self.dim = len(data)
        np_data = np.array(data)
        self.update_sample_cache(np_data)
        if np.ndim(self.sigmaInv) > 0:
            p = self.coefficient * math.exp(-0.5 * np.dot(np.dot(np_data, self.sigmaInv), np_data))
            return {"status": "ok", "p": p}
        else:
            return None

    def update_sample_cache(self, np_data):
        self.sampleCache.append(np_data)
        if len(self.sampleCache) >= self.parameters['min_samples']:
            np_sample_cache = np.array(self.sampleCache)
            n = len(np_sample_cache)
            self.mu = np_sample_cache.sum(0) / n
            sigma = np.zeros((len(self.mu), len(self.mu)))
            for eachLine in (np_sample_cache - self.mu):
                partial = np.outer(eachLine, eachLine)
                print("partial:")
                print(partial)
                sigma = sigma + partial
                print("sigma:")
                print(sigma)
            self.sigma = sigma / n
            self.sigmaInv = np.linalg.inv(self.sigma)
            self.coefficient = 1 / (((2 * math.pi) ** (self.dim / 2)) * math.sqrt(np.linalg.det(self.sigma)))
