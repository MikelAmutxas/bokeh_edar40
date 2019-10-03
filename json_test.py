from utils.rapidminer_proxy import call_webservice
import json
import pandas as pd
import time
from pandas.io.json import json_normalize

start_time = time.time()    # Measure time
response = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out_JSON?','rapidminer','rapidminer') # Call webservice takes 1.21 secs
elapsed_time = time.time() - start_time # Measure time

# print(response)
cont = json.loads(response)
print(cont[0][1])

# df = pd.read_json(cont)
# df = pd.DataFrame.from_dict(cont[0])
print(f'Elapsed Time Perfil Out: {elapsed_time}')
# print(df)
# print(len(df))
# new_df = json_normalize(df[0])
# print(new_df.head())

start_time = time.time()    # Measure time
prediction_doc = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion_JSON?', 'rapidminer', 'rapidminer', {'Objetivo': 'Calidad_Agua', 'Discretizacion': 'Calidad_Agua'}, out_json=True)
elapsed_time = time.time() - start_time # Measure time
print(f'Elapsed Time Prediccion: {elapsed_time}')

# j_pred = prediction_doc.json()
# cont_pred = json.loads(prediction_doc)
print(prediction_doc)
# df_pred = pd.DataFrame.from_dict(prediction_doc)
# print(df_pred)
