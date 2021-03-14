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

from flask import Flask, jsonify, request
from evaluator import Evaluator

app = Flask(__name__)
evaluator = Evaluator()

#
# Evaluation API
#
@app.route("/evaluate", methods=['POST'])
def post_sample():
	data = request.get_json()
	if data:
		result, status = evaluator.evaluate(data)
		if 200 <= status and status < 300:
			return jsonify({"result": result}), status
		else:
			return jsonify({"error": result}), status
	else:
		return jsonify({"error": "Payload not found."}), 400

#
# Run webserver
#
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)
