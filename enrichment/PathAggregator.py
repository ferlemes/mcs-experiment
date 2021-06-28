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
import logging
import uuid

logger = logging.getLogger()

#
# Data structure for path storage
#
class PathAggregator:

    def __init__(self):
        self.root = PathNode('')

    def get_path_aggregator(self, http_path):
        path = http_path + '?'
        path_parts = path.split('?')
        resource = path_parts[0]
        if resource[0] == '/':
            resource = resource[1:]
        current_node = self.root
        for resource_part in resource.split('/'):
            current_node = current_node.get_child(resource_part)
            current_node.compress()
        return current_node.get_uuid(), current_node.get_name()

class PathNode:

    def __init__(self, name):
        self.name = name
        self.uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        self.child_nodes_by_regexp = {}
        self.child_nodes_by_string = {}
        self.compressed = False

    def get_child(self, node_name):
        for regexp, node in self.child_nodes_by_regexp.items():
            if regexp.search(node_name):
                return node
        if node_name not in self.child_nodes_by_string:
            self.child_nodes_by_string[node_name] = PathNode(self.name + '/' + node_name)
        return self.child_nodes_by_string[node_name]

    def compress(self):
        if self.compressed:
            return
        if len(self.child_nodes_by_string) > 100:
            groups = [
                { 'name': '<number>',              'regexp': re.compile(r"^[0-9]+$")                                                       },
                { 'name': '<hexadecimal>',         'regexp': re.compile(r"^[0-9a-f]+$")                                                    },
                { 'name': '<uuid>',                'regexp': re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$") },
                { 'name': '<letters>',             'regexp': re.compile(r"^[A-Za-z]+$")                                                    },
                { 'name': '<letters_and_numbers>', 'regexp': re.compile(r"^[A-Za-z0-9]+$")                                                 },
                { 'name': '<anything>',            'regexp': re.compile(r"^.+$")                                                           },
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
                    new_node = PathNode(self.name + '/' + group_name)
                    self.child_nodes_by_regexp[group_regexp] = new_node
                    for node_name, each_node in self.child_nodes_by_string.items():
                        new_node.merge(each_node)
                    self.child_nodes_by_string.clear()
                    self.compressed = True
                    break

    def merge(self, another_node):
        for node_name, node in another_node.child_nodes_by_string.items():
            if node_name in self.child_nodes_by_string:
                self.child_nodes_by_string[node_name].merge(node)
                self.child_nodes_by_string[node_name].compress()
            else:
                self.child_nodes_by_string[node_name] = node
        for regexp, node in another_node.child_nodes_by_regexp.items():
            if regexp in self.child_nodes_by_regexp:
                self.child_nodes_by_regexp[regexp].merge(node)
                self.child_nodes_by_regexp[regexp].compress()
            else:
                self.child_nodes_by_regexp[regexp] = node

    def get_uuid(self):
        return self.uuid

    def get_name(self):
        return self.name
