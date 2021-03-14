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
from flask import Flask, jsonify, request
from pymongo import MongoClient

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

if 'MONGO_URL' in os.environ:
	mongo_url = os.environ['MONGO_URL']
	client = MongoClient(mongo_url)
	logger.info('Using mongo URL: %s', mongo_url)
else:
	logger.fatal('Missing MONGO_URL environment variable.')
	sys.exit()

if 'MONGO_DATABASE' in os.environ:
	mongo_database = os.environ['MONGO_DATABASE']
	database = client[mongo_database]
	collection = database.haproxy_records
	logger.info('Using mongo database: %s', mongo_database)
else:
	logger.fatal('Missing MONGO_DATABASE environment variable.')
	sys.exit()

app = Flask(__name__)

@app.route("/ping", methods=['GET'])
def ping():
	return 'OK', 200

@app.route("/evaluate", methods=['POST'])
def evaluate():
	payload = request.get_json()
	if payload:
		logger.info('Received payload: %s', str(payload))
		try:
			collection.insert_one(payload)
			return 'OK', 200
		except:
			logger.error('Error sending data to MongoDB.')
			return 'Error sending data to MongoDB.', 500
	else:
		logger.warning('Request with no payload received.')
		return 'Missing payload.', 400

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=False)
