from utils.database_access_proxy import execute_query

from bokeh.layouts import column, row, widgetbox, layout
from bokeh.models import ColumnDataSource, Div, DateRangeSlider, DatePicker, Button, DataTable, TableColumn, HoverTool
from bokeh.models.markers import Circle
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc, show
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange

from datetime import date
from datetime import datetime

import pandas as pd

from sqlalchemy import *
from sqlalchemy.engine import create_engine

engine = create_engine('presto://smvhortonworks:7778/hive/epele', connect_args={'protocol':'https', 'KerberosPrincipal': 'bokeh-epele@EDAR40.EUS', 'KerberosKeytabPath': '/Users/mikelamuchastegui/bokeh-epele.keytab', 'KerberosRemoteServiceName': 'presto', 'requests_kwargs':{'verify':'/Users/mikelamuchastegui/Documents/EDAR Certificates/ca-cert.pem'}}, echo=False)

def get_power_kpi_data(date_interval, group_by, idvar, table):
	if group_by is True:
		power_kpi_instances = select([column('valuedate'), func.sum(column('value')).label('value')], from_obj=table).where(or_(column('idvar') == idvar[0], column('idvar') == idvar[1])).where(column('valuedate').between(date_interval[0], date_interval[1])).group_by(column('valuedate')).order_by(asc(column('valuedate')))
	else:
		power_kpi_instances = select([column('valuedate'), column('value')], from_obj=table).where(and_(column('valuedate').between(date_interval[0], date_interval[1]), column('idvar') == idvar[0]))

	power_kpi_source = execute_query(power_kpi_instances, engine)
	return power_kpi_source

def get_models_data(date_interval, idvar, table):
	models_instances = select([column('valuedate'), column('value')], from_obj=table).where(and_(column('valuedate').between(date_interval[0], date_interval[1]), column('idvar') == idvar))
	models_source = execute_query(models_instances, engine)
	return models_source

def create_power_kpi_plot(data_sources, title, legends):
	hover_tool = HoverTool(
		tooltips = [
			('Fecha', '@valuedate{%m/%d %H:%M}'),
			('Valor', '@value')
		],
		formatters = {
			'valuedate': 'datetime',
		},
		mode = 'mouse'
		)
	power_kpi_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')
	power_kpi_plot.line(x='valuedate', y='value', source=data_sources[0], line_width=2, line_color='#396ab1', legend=legends[0])
	power_kpi_plot.line(x='valuedate', y='value', source=data_sources[1], line_width=2, line_color='#da7c30', legend=legends[1])
	power_kpi_plot.line(x='valuedate', y='value', source=data_sources[2], line_width=2, line_color='#3e9651', legend=legends[2])
	power_kpi_plot.xaxis[0].formatter = DatetimeTickFormatter(hours=['%H:%M'], minutes=['%Y/%m/%d %H:%M'])
	power_kpi_plot.add_tools(hover_tool)
	power_kpi_plot.legend.location = 'top_left'
	power_kpi_plot.legend.orientation = 'vertical'
	power_kpi_plot.legend.click_policy = 'hide'
	power_kpi_plot.title.text = title
	power_kpi_plot.title.align = 'left'
	power_kpi_plot.title.text_font_size = '16px'
	return power_kpi_plot

def create_power_plots(table):
	a_power = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], False, [51102], table)
	b_power = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], False, [51103], table)
	total_power = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], True, [51102,51103], table)
	power_plot = create_power_kpi_plot([total_power, a_power, b_power], 'Monitorización consumo de potencia de la planta', ['Potencia total de planta', 'Potencia zona A', 'Potencia zona B'])
	return {power_plot:[total_power,a_power,b_power]}

def create_kpi_plots(table):
	a_kpi = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], False, [51141], table)
	b_kpi = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], False, [51142], table)
	total_kpi = get_power_kpi_data([datetime(2016,3,1,0,0,0), datetime(2016,3,2,0,0,0)], True, [51141,51142], table)
	kpi_plot = create_power_kpi_plot([total_kpi, a_kpi, b_kpi], 'Monitorización ratio kw/m3h de la planta', ['KPI total planta', 'KPI zona A', 'KPI zona B'])
	return {kpi_plot:[total_kpi,a_kpi,b_kpi]}

def create_model_plot(data_source, title, color, line_type):
	hover_tool = HoverTool(
		tooltips = [
			('Fecha', '@valuedate{%m/%d %H:%M}'),
			('Valor', '@value')
		],
		formatters = {
			'valuedate': 'datetime',
		},
		mode = 'mouse'
		)
	model_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')
	model_plot.line(x='valuedate', y='value', source=data_source, line_width=2, line_color=color, line_dash=line_type)
	model_plot.xaxis[0].formatter = DatetimeTickFormatter(days=['%m/%d'], minutes=['%Y/%m/%d %H:%M'])
	model_plot.add_tools(hover_tool)
	model_plot.title.text = title
	model_plot.title.align = 'left'
	model_plot.title.text_font_size = '12px'
	return model_plot

def create_models_plots(table):
	a_power_day_dev = get_models_data([datetime(2016,3,1,0,0,0), datetime(2016,3,7,23,0,0)], 51137, table)
	a_perc_day_dev = get_models_data([datetime(2016,3,1,0,0,0), datetime(2016,3,7,23,0,0)], 51138, table)
	b_power_day_dev = get_models_data([datetime(2016,3,1,0,0,0), datetime(2016,3,7,23,0,0)], 51125, table)
	b_perc_day_dev = get_models_data([datetime(2016,3,1,0,0,0), datetime(2016,3,7,23,0,0)], 51126, table)
	a_power_dev_plot = create_model_plot(a_power_day_dev, 'Desviación de potencia estimada Zona A en KW', '#396ab1', 'solid')
	a_perc_day_dev_plot = create_model_plot(a_perc_day_dev, 'Desviación de potencia estimada Zona A en %', '#da7c30', 'dashed')
	b_power_dev_plot = create_model_plot(b_power_day_dev, 'Desviación de potencia estimada Zona B en KW', '#396ab1', 'solid')
	b_perc_dev_plot = create_model_plot(b_perc_day_dev, 'Desviación de potencia estimada Zona B en %', '#da7c30', 'dashed')
	return {a_power_dev_plot:a_power_day_dev, a_perc_day_dev_plot:a_perc_day_dev, b_power_dev_plot:b_power_day_dev, b_perc_dev_plot: b_perc_day_dev}

def create_decription():
	desc = Div(text="""
	<h1 class="display-4">Monitorización consumo planta EDAR Epele</h1>
	<p class="lead">Este dashboard muestra la monitorización de consumo de la planta EDAR Epele.</p>
	""")
	return desc

def create_datetime_slider(start_date, end_date, selected_date):
	slider = DateRangeSlider(title='Selecciona un intervalo', start=start_date, end=end_date, value=(selected_date[0], selected_date[1]), step=1, sizing_mode='stretch_width')
	return slider

def modify_epele_doc(doc):
	table = Table('all_data_orc', MetaData(bind=engine), autoload=True)

	power_plot_data = create_power_plots(table)
	kpi_plot_data = create_kpi_plots(table)
	models_plot_data = create_models_plots(table)

	desc = create_decription()

	power_plot = list(power_plot_data)[0]
	kpi_plot = list(kpi_plot_data)[0]
	a_power_dev_plot = list(models_plot_data)[0]
	a_perc_day_dev_plot = list(models_plot_data)[1]
	b_power_dev_plot = list(models_plot_data)[2]
	b_perc_dev_plot = list(models_plot_data)[3]

	power_plot_slider = create_datetime_slider(date(2016,3,1), date(2017,3,1), [date(2016,3,1), date(2016,3,2)])
	power_change_data_button = Button(label='Actualizar datos', button_type='primary', width=112, height=45, sizing_mode='fixed')

	dev_plot_slider = create_datetime_slider(date(2016,3,1), date(2017,3,1), [date(2016,3,1), date(2016,3,7)])
	dev_change_data_button = Button(label='Actualizar datos', button_type='primary', width=112, height=45, sizing_mode='fixed')

	l = layout([
		[desc],
		[power_plot_slider, power_change_data_button],
		[power_plot],
		[kpi_plot],
		[dev_plot_slider, dev_change_data_button],
		[a_power_dev_plot, a_perc_day_dev_plot, b_power_dev_plot,b_perc_dev_plot],
	], sizing_mode='stretch_both')

	def power_kpi_plot_callback():
		date_from = datetime.utcfromtimestamp(power_plot_slider.value[0]/1000).replace(second=0, microsecond=0)
		date_to = datetime.utcfromtimestamp(power_plot_slider.value[1]/1000).replace(second=0, microsecond=0)

		a_power = get_power_kpi_data([date_from, date_to], False, [51102], table)
		b_power = get_power_kpi_data([date_from, date_to], False, [51103], table)
		total_power = get_power_kpi_data([date_from, date_to], True, [51102,51103], table)
		power_data = power_plot_data[power_plot]
		#power_data[0].data = total_power.data
		power_data[1].stream(a_power.data)
		power_data[2].data = a_power.data

		kpi_a = get_power_kpi_data([date_from, date_to], False, [51141], table)
		kpi_b = get_power_kpi_data([date_from, date_to], False, [51142], table)
		kpi_total = get_power_kpi_data([date_from, date_to], True, [51141, 51142], table)
		kpi_data = kpi_plot_data[kpi_plot]
		kpi_data[0].data = kpi_total.data
		kpi_data[1].data = kpi_a.data
		kpi_data[2].data = kpi_b.data

	def dev_plot_callback():
		date_from = datetime.utcfromtimestamp(dev_plot_slider.value[0]/1000).replace(second=0, microsecond=0)
		date_to = datetime.utcfromtimestamp(dev_plot_slider.value[1]/1000).replace(second=0, microsecond=0)

		a_power_day_dev = get_models_data([date_from, date_to], 51137, table)
		a_perc_day_dev = get_models_data([date_from, date_to], 51138, table)
		b_power_day_dev = get_models_data([date_from, date_to], 51125, table)
		b_perc_day_dev = get_models_data([date_from, date_to], 51126, table)

		models_plot_data[a_power_dev_plot].data = a_power_day_dev.data
		models_plot_data[a_perc_day_dev_plot].data = a_perc_day_dev.data
		models_plot_data[b_power_dev_plot].data = b_power_day_dev.data
		models_plot_data[b_perc_dev_plot].data = b_perc_day_dev.data

	power_change_data_button.on_click(power_kpi_plot_callback)
	dev_change_data_button.on_click(dev_plot_callback)

	doc.add_root(l)