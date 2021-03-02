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
from model_manager import ModelManager
from errors import InvalidPayloadException

app = Flask(__name__)
model_manager = ModelManager()

#
# Model API
#


@app.route("/model/<string:model_name>", methods=['GET'])
def get_model(model_name):
    model = model_manager.get_model(model_name)
    if model:
        return jsonify(model.get_parameters()), 200
    else:
        return jsonify({"error": "Model not found."}), 404


@app.route("/model/<string:model_name>", methods=['POST'])
def post_model(model_name):
    model = model_manager.get_model(model_name)
    if model:
        return jsonify({"error": "Model already exists."}), 409
    else:
        model = model_manager.create_model(model_name, request.get_json())
        return jsonify(model.get_parameters()), 200


@app.route("/model/<string:model_name>", methods=['DELETE'])
def delete_model(model_name):
    model = model_manager.get_model(model_name)
    if model:
        model_manager.delete_model(model_name)
        return '', 204
    else:
        return jsonify({"error": "Model not found."}), 404


#
# Evaluation API
#


@app.route("/evaluate/<string:model_name>", methods=['POST'])
def post_sample(model_name):
    model = model_manager.get_model(model_name)
    if model:
        try:
            evaluation = model.evaluate(request.get_json())
        except InvalidPayloadException as error:
            return jsonify({"error": str(error)}), 400
        if evaluation:
            return jsonify(evaluation), 200
        else:
            return jsonify({}), 204
    else:
        return jsonify({"error": "Model not found."}), 404

@app.route("/evaluate", methods=['POST'])
def post_sample_simple():
    return jsonify("Hmm.. seems ok."), 200

#
# Run webserver
#


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
