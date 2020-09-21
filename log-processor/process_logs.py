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

import time
import re
from pymongo import MongoClient

mongo_client = MongoClient('mongodb://mongodb:27017/')
mongo_database = mongo_client.monitoring
mongo_collection = mongo_database.log_records

#db.log_records.aggregate([{ $group: { _id: "$label", count: { $sum: 1 } }   }])

labels_table = {}

def read_labels():
    file_handler = open(each_file, "r")
    for each_line in file_handler:
        labels_table[]

def process_labels():
    pending_records = mongo_collection.find( { "label": { "$exists": False } } )
    for each_record in pending_records:
        mongo_collection.update_one({ '_id': each_record['_id'] }, { '$set': { 'label': each_record['http_verb'] + ":" + each_record['http_path'] } })


read_labels()
while True:
    process_labels()
    time.sleep(5)