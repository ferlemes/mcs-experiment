#!/usr/local/bin/python

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
import sys
import logging
from pymongo import MongoClient
import time
import json
import re
import uuid
import random


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


if 'MONGO_URL' in os.environ:
    mongo_url = os.environ['MONGO_URL']
    logger.info('Using mongo URL: %s', mongo_url)
else:
    logger.fatal('Missing MONGO_URL environment variable.')
    sys.exit()

if 'MONGO_DATABASE' in os.environ:
    mongo_database = os.environ['MONGO_DATABASE']
else:
    mongo_database = 'kubeowl'
logger.info('Using mongo database: %s', mongo_database)

if 'MONGO_HTTP_RECORDS' in os.environ:
    mongo_http_records = os.environ['MONGO_HTTP_RECORDS']
else:
    mongo_http_records = 'http_records'
logger.info('HTTP records collection is: %s', mongo_http_records)


# Make words anonymous
with open("/tmp/words_list.txt", 'r') as file:
    words_list = file.read().splitlines()
if not words_list:
    logger.fatal('Missing words dictionary from /tmp/words_list.txt.')
    sys.exit()

anonymous_dict = {}
def get_anonymous(word):
    anonymous = anonymous_dict.get(word)
    if not anonymous:
        if re.compile(r"^[0-9]+$").search(word):
            anonymous = str(random.randint(1000000000, 9999999999))
        elif re.compile(r"^[0-9a-f]+$").search(word):
            anonymous = hex(random.randint(1000000000, 9999999999))[2:]
        elif re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$").search(word):
            anonymous = str(uuid.uuid4())
        else:
            anonymous = words_list[0]
            del words_list[0]
        anonymous_dict[word] = anonymous
    return anonymous


#
# Data structure for path storage
#
class PathTranslator:

    def __init__(self):
        self.root = PathNode('')

    def get_anonymous_path(self, http_path):
        path = http_path + '?'
        path_parts = path.split('?')
        resource = path_parts[0]
        if resource[0] == '/':
            resource = resource[1:]
        current_node = self.root
        for resource_part in resource.split('/'):
            current_node = current_node.get_child(resource_part)
        return current_node.get_name()

class PathNode:

    def __init__(self, name):
        self.name = name
        self.child_nodes = {}

    def get_child(self, node_name):
        if node_name not in self.child_nodes:
            self.child_nodes[node_name] = PathNode(self.name + '/' + get_anonymous(node_name))
        return self.child_nodes[node_name]

    def get_name(self):
        return self.name

translator = PathTranslator()

try:
    client = MongoClient(mongo_url)
    database = client[mongo_database]
    collection = database[mongo_http_records]
    collection.create_index([('timestamp', 1)])
except:
    logger.exception('Failure creating index.')
    sys.exit()


current_file = None
current_filename = ''
current_count = 0
arguments = sys.argv
if len(arguments) > 1:
    start = int(arguments[1])
    start = start - (start  % 3600)
else:
    logger.exception('Missing start timestamp.')
    sys.exit()
if len(arguments) > 2:
    end = int(arguments[2])
    end = end - (end % 3600) + 3599
else:
    logger.exception('Missing end timestamp.')
    sys.exit()
try:
    window_start = start
    window_end = window_start + 3600
    while window_start < end:
        count = 0
        current_file = None
        for each_record in collection.find({ "timestamp": { "$gte": window_start, "$lt": window_end } }).sort([('timestamp', 1)]):
            if not current_file:
                filename = time.strftime('%Y-%m-%d_%Hh%Mm.data', time.localtime(window_start))
                logger.info('Writing to file: %s', filename)
                current_file = open(filename, 'w')
            labels = []
            if each_record.get('labels', []):
                for label in each_record.get('labels', []):
                    labels.append(get_anonymous(label))
            each_record = {
                'timestamp': each_record.get('timestamp'),
                'http_host': get_anonymous(each_record.get('http_host')),
                'labels': labels,
                'http_protocol': each_record.get('http_protocol'),
                'http_verb': each_record.get('http_verb'),
                'http_path': translator.get_anonymous_path(each_record.get('http_path')),
                'http_status': each_record.get('http_status'),
                'bytes_sent': each_record.get('bytes_sent'),
                'bytes_received': each_record.get('bytes_received'),
                'duration': each_record.get('duration')
            }
            current_file.write(json.dumps(each_record) + '\n')
            count += 1
        if count > 0:
            logger.info('%d records added.', count)
        if current_file:
            current_file.close()
            current_file = None
        window_start += 3600
        window_end += 3600

except:
    logger.exception('Failure exporting records.')
    sys.exit()
