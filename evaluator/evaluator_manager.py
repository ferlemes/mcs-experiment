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

import re
from evaluator import Evaluator


class EvaluatorManager:

    def __init__(self, childs_to_compress = 1000):
        self.root = PathNode('root')
        EvaluatorManager.childs_to_compress = childs_to_compress

    def get_evaluator_for(self, http_path):
        path = http_path + '?'
        path_parts = path.split('?')
        resource = path_parts[0]
        if resource[0] == '/':
            resource = resource[1:]
        parameters = path_parts[1]
        current_node = self.root
        for resource_part in resource.split('/'):
            current_node = current_node.get_child(resource_part)
            current_node.compress()                                # TODO Should compress async based on req count or time interval
        return current_node.evaluator

class PathNode:

    def __init__(self, name):
        self.name = name
        self.child_nodes_by_regexp = {}
        self.child_nodes_by_string = {}
        self.evaluator = Evaluator()

    def get_child(self, node_name):
        for regexp, node in self.child_nodes_by_regexp.items():
            if regexp.search(node_name):
                return node
        if node_name not in self.child_nodes_by_string:
            self.child_nodes_by_string[node_name] = PathNode(node_name)
        return self.child_nodes_by_string[node_name]

    def compress(self):
        if len(self.child_nodes_by_string) > EvaluatorManager.childs_to_compress:
            groups = [
                { 'name': '<number>',            'regexp': re.compile(r"^[0-9]+$")                                                       },
                { 'name': '<hexadecimal>',       'regexp': re.compile(r"^[0-9a-f]+$")                                                    },
                { 'name': '<uuid>',              'regexp': re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$") },
                { 'name': '<letters>',           'regexp': re.compile(r"^[A-Za-z]+$")                                                    },
                { 'name': '<lettersAndNumbers>', 'regexp': re.compile(r"^[A-Za-z0-9]+$")                                                 },
                { 'name': '<anything>',          'regexp': re.compile(r"^.+$")                                                           },
            ]
            for group in groups:
                group_name = group.get('name')
                group_regexp = group.get('regexp')
                use_group = True
                for node_name in self.child_nodes_by_string:
                    if not group_regexp.search(node_name):
                        use_group = False
                        break
                if use_group:
                    new_node = PathNode(group_name)
                    self.child_nodes_by_regexp[group_regexp] = new_node
                    for node_name, each_node in self.child_nodes_by_string.items():
                        new_node.merge(each_node)
                    self.child_nodes_by_string.clear()

    def merge(self, another_node):
        self.evaluator.merge(another_node.evaluator)
        for node_name, node in another_node.child_nodes_by_string.items():
            if node_name in self.child_nodes_by_string:
                self.child_nodes_by_string[node_name].merge(node)
            else:
                self.child_nodes_by_string[node_name] = node
        for regexp, node in another_node.child_nodes_by_regexp.items():
            if regexp in self.child_nodes_by_regexp:
                self.child_nodes_by_regexp[regexp].merge(node)
            else:
                self.child_nodes_by_regexp[regexp] = node
