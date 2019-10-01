from utils.rapidminer_proxy import call_webservice
import json
import pandas as pd
from pandas.io.json import json_normalize

response = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out_JSON?','rapidminer','rapidminer')
# print(response)
cont = json.loads(response)
print(cont[0][1])

# df = pd.read_json(cont)
df = pd.DataFrame.from_dict(cont[0])
print(df)
print(len(df))
# new_df = json_normalize(df[0])
# print(new_df.head())