# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
import requests
import logging as log
import google.cloud.logging

PROJECT_ID = "qwiklabs-gcp-04-f9624967eddc"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://qwiklabs-gcp-04-f9624967eddc-lab-bucket"

import vertexai
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

client = google.cloud.logging.Client()
client.setup_logging()

#
# Vertex AI Search
#
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

DS_ENGINE_ID = "goog-merch-ds_1747080039185"
search_client_options = ClientOptions(api_endpoint=f"discoveryengine.googleapis.com")
search_client = discoveryengine.SearchServiceClient(
    client_options=search_client_options
)
search_serving_config = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DS_ENGINE_ID}/servingConfigs/default_search:search"

def search_gms(search_query, rows):
    # build a search request
    request = discoveryengine.SearchRequest(
        serving_config=search_serving_config,
        query=search_query,
        page_size=rows,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
    )

    # search
    resp_pager = search_client.search(request)

    # parse the results
    response = discoveryengine.SearchResponse(
        results=resp_pager.results,
        facets=resp_pager.facets,
        total_size=resp_pager.total_size,
        attribution_token=resp_pager.attribution_token,
        next_page_token=resp_pager.next_page_token,
        corrected_query=resp_pager.corrected_query,
        summary=resp_pager.summary,
    )
    response_json = json.loads(
        discoveryengine.SearchResponse.to_json(
            response,
            including_default_value_fields=True,
            use_integers_for_enums=False,
        )
    )

    # extract ids
    resp_list = [doc for doc in response_json["results"]]
    return resp_list

#
# Flask app
#
from flask import Flask, request
from flask_cors import CORS

# init Flask app
app = Flask(__name__)
CORS(app)

PROF_ENABLED = False
MAX_RETRIES = 3

# Endpoint for the app home page
@app.route("/", methods=["GET"])
def home():
    return "Welcome to the ag-web backend app."

# Endpoint for the app to call Vertex AI Search
@app.route("/ask_gms", methods=["GET"])
def ask_gms():
    query = request.args.get("query")
    item = search_gms(query, 1)[0]["document"]["structData"]
    return json.dumps(item)

# run Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
