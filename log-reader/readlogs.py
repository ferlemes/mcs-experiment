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
from os import listdir, remove
from os.path import isfile, join
from pymongo import MongoClient

haproxy_log_format = re.compile(r"^.* ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+) ([0-9]+) [^ ]+ [^ ]+ [^ ]+ ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+)/([0-9]+) \"([A-Z]+) ([^ ]+) ([^ ]+)\".*$")

mongo_client = MongoClient('mongodb://mongodb:27017/')
mongo_database = mongo_client.monitoring
mongo_collection = mongo_database.log_records

def add_haproxy_entry_to_db(data):
  log_entry = {
    "time_to_receive_request":                 data[0],
    "time_in_queue":                           data[1],
    "time_to_tcp_connect":                     data[2],
    "time_to_get_response":                    data[3],
    "total_time_active":                       data[4],
    "http_status":                             data[5],
    "bytes_count":                             data[6],
    "concurrent_connections_haproxy":          data[7],
    "concurrent_connections_frontend":         data[8],
    "concurrent_connections_backend":          data[9],
    "concurrent_active_connections_on_server": data[10],
    "connection_retry_attempts":               data[11],
    "queue1":                                  data[12],
    "queue2":                                  data[13],
    "http_verb":                               data[14],
    "http_path":                               data[15],
    "http_protocol":                           data[16]
  }
  mongo_collection.insert_one(log_entry)

def process_file_line(line):
  search = haproxy_log_format.search(line)
  if search:
    add_haproxy_entry_to_db(search.groups())

log_path = "/logs/"

while True:
  file_list = [join(log_path, each_dir_entry) for each_dir_entry in listdir(log_path) if isfile(join(log_path, each_dir_entry))]
  for each_file in file_list:
    print("Processing file: " + each_file)
    lines_processed = 0
    file_handler = open(each_file, "r")
    for each_line in file_handler:
      process_file_line(each_line)
      lines_processed += 1
    file_handler.close()
    print("Processed " + str(lines_processed) + " lines from file: " + each_file)
    remove(each_file)
  time.sleep(5)
