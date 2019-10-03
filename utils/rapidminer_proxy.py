import pandas as pd

import requests

def call_webservice(url, username, password, parameters=None, out_json=False):
	r = requests.get(url, params=parameters, auth=(username, password))
	if out_json:
		document = r.json()
	else:
		document = r.text
	return document