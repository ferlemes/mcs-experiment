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

from path_node import PathNode

class Evaluator:

    def __init__(self):
        self.root = PathNode()

    def evaluate(self, data):
        if 'http_path' in data:
            path = data['http_path'] + '?'
            path_parts = path.split('?')
            resource = path_parts[0]
            parameters = path_parts[1]
            current_node = self.root
            for resource_part in resource.split('/'):
                current_node = current_node.get_child(resource_part)
            current_node.feed(data)
            result = current_node.evaluate(data)
            if result:
                return result, 200
            else:
                return "Unable to evaluate.", 202
        else:
            return "Missing 'http_path' at payload.", 400