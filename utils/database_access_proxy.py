from bokeh.models import ColumnDataSource

import pandas as pd

from sqlalchemy import *
from sqlalchemy.schema import *
from sqlalchemy.sql import select

def execute_query(instances, engine):
	conn = engine.connect()
	result = conn.execute(instances)
	df = pd.DataFrame(result.fetchall(), columns=result.keys())
	df['valuedate'] = pd.to_datetime(df['valuedate'])
	source = ColumnDataSource(df)
	conn.close()
	return source


