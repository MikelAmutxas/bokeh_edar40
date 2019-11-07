import pandas as pd
import requests
import json

def call_webservice(url, username, password, parameters=None, out_json=False):
	r = requests.get(url, params=parameters, auth=(username, password))
	if out_json:
		document = json.loads(r.text)
	else:
		document = r.text
	return document