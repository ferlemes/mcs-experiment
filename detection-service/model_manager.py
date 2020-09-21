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

from model import Model


class ModelManager:

    def __init__(self):
        self.model_library = {}

    def create_model(self, model_name, model_specs):
        new_model = Model(model_specs)
        self.model_library[model_name] = new_model
        return new_model

    def get_model(self, model_name):
        return self.model_library.get(model_name)

    def delete_model(self, model_name):
        del self.model_library[model_name]
