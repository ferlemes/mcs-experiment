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

class PathNode:

    def __init__(self):
        self.child_nodes_by_regexp = {}
        self.child_nodes_by_string = {}
        self.requests_data = []

    def get_child(self, node_name):
        print("Getting child with name: %s", node_name)
        for regexp, node in self.child_nodes_by_regexp.items():
            if regexp.search(node_name):
                return node
        if node_name not in self.child_nodes_by_string:
            self.child_nodes_by_string[node_name] = PathNode()
        return self.child_nodes_by_string[node_name]

    def feed(self, data):
        self.requests_data.append(data)

    def evaluate(self, data):
        print("evaluating data")
        if len(self.requests_data) > 5:
            return "I didn't check the data, but it seems ok."
        else:
            return None

    def compress(self):
        if len(self.child_nodes_by_string) > 10:
            print("Compressing nodes")
            number = re.compile(r"^[0-9]+$")
            use_number = True
            for node_name in self.child_nodes_by_string:
                if not number.search(node_name):
                    use_number = False
                    break
            if use_number:
                new_node = PathNode()
                self.child_nodes_by_regexp[number] = new_node
                for node_name, each_node in self.child_nodes_by_string.items():
                    new_node.merge(each_node)
                self.child_nodes_by_string.clear()

    def merge(self, another_node):
        self.requests_data.append(another_node.requests_data)
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
