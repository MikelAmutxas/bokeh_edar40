import pandas as pd

import requests

def call_webservice(url, username, password, parameters=None):
	r = requests.get(url, params=parameters, auth=(username, password))
	xml_document = r.text
	return xml_document