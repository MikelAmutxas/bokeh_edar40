from utils.rapidminer_proxy import call_webservice
from utils.xml_parser import get_dataframe_from_xml, create_performance_vector_data, create_correct_quantity_data, create_decision_tree_data
import utils.bokeh_utils as bokeh_utils

from bokeh_edar40.visualizations.decision_tree import *

from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Div, HoverTool, GraphRenderer, StaticLayoutProvider, Rect, MultiLine, LinearAxis, Grid, Legend, LegendItem, Span, Label, BasicTicker, ColorBar, LinearColorMapper, PrintfTickFormatter, MonthsTicker
from bokeh.models.ranges import FactorRange
from bokeh.models.widgets import Select, Button, TableColumn, DataTable, CheckboxButtonGroup
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox, column, row, gridplot
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.transform import jitter, factor_cmap, dodge, transform

import xml.etree.ElementTree as et
import pandas as pd
import numpy as np
from pandas.io.json import json_normalize
from datetime import datetime as dt
import time


def create_data_source_from_dataframe(df, group_value_name, group_value):
	"""Crea ColumnDataSource desde DataFrame agrupando los valores de una columna concreta según un valor
	Parameters:
		df (Dataframe): Dataframe de datos
		group_value_name (string): Nombre de columna donde buscar los valores a agrupar
		goup_value (string): Valor para agrupar los datos
	
	Returns:
		ColumnDataSource: ColumnDataSource con los datos correctamente agrupados
	"""
	df = df.loc[df[group_value_name].isin([group_value])]
	source = ColumnDataSource(df)

	return source

def create_corrects_plot_positions_data(number_of_values, bar_width):
	"""Inserta las barras en la gráfica de aciertos
	Parameters:
		number_of_values (int): Número de valores a mostrar en la visualización
		bar_width (float): Ancho de cada barra del gráfico

	Returns:
		list: Valores de coordenadas X donde dibujar las barras del gráfico de aciertos
	"""
	x_pos = []
	start_x = 0

	if number_of_values % 2 != 0:
		start_x = 0
	else:
		start_x = bar_width

	# Computamos la posición de cada barra en el gráfico dependiendo del número de gráficos a mostrar por grupo de predicción
	for i in range(number_of_values):
		if start_x == 0:
			x = start_x + i * (bar_width + bar_width/2) - ((bar_width*number_of_values/2) + bar_width/2)
		else:
			x = start_x + i * (bar_width + bar_width/2) - ((2*bar_width*number_of_values/2) - bar_width/2)
			if i >= number_of_values/2:
				x = x + (bar_width/2)

		x_pos.append(x)

	return x_pos

def create_bars_in_corrects_plot(plot, data_dict, number_of_values, x_pos):
	"""Inserta las barras en la gráfica de aciertos
	Parameters:
		plot (Figura): Figura de Bokeh donde se representa la gráfica de aciertos
		data_dict (dict): Diccionario con los datos a mostrar en la visualización
		number_of_values (int): Número de valores a mostrar en la visualización
		x_pos (string): Valores de coordenadas X donde dibujar las barras del gráfico de aciertos
	"""

	values_keys = list(data_dict.keys())
	values_keys.remove('predictions')
	source = ColumnDataSource(data=data_dict)

	legend_items = []

	for i in range(number_of_values):
		vbar = plot.vbar(x=dodge('predictions', x_pos[i], range=plot.x_range), top=values_keys[i], width=0.1, source=source, color=bokeh_utils.BAR_COLORS_PALETTE[i])
		legend_items.append(LegendItem(label=values_keys[i], renderers=[vbar]))

	if len(plot.legend) == 0:
		legend = Legend(items=legend_items)
		plot.add_layout(legend)
	else:
		legend = plot.legend[0]
		legend.items = legend_items


def create_corrects_plot(prediction_values, data_dict):
	"""Crea gráfica de aciertos
	Parameters:
		prediction_values (list): Lista de valores predichos por el modelo
		data_dict (dict): Diccionario con los datos a mostrar en la visualización

	Returns:
		DataTable: Tabla de matriz de confusión
	"""
	
	data_dict['predictions'] = prediction_values

	corrects_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_range=prediction_values)
	
	number_of_values = len(data_dict.keys()) - 1
	bar_width = 0.1

	x_pos = create_corrects_plot_positions_data(number_of_values, bar_width)
	create_bars_in_corrects_plot(corrects_plot, data_dict, number_of_values, x_pos)

	corrects_plot.x_range.range_padding = 0.1
	corrects_plot.y_range.start = 0

	corrects_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	corrects_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	corrects_plot.legend.location = 'top_left'
	corrects_plot.legend.orientation = 'horizontal'
	corrects_plot.legend.click_policy = 'hide'
	corrects_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	corrects_plot.title.text = 'Gráfica de aciertos'
	corrects_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	corrects_plot.title.align = 'left'
	corrects_plot.title.text_font_size = '16px'
	corrects_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	corrects_plot.min_border_right = 15

	return corrects_plot

def create_attribute_weight_plot(df):
	"""Crea gráfica de importancia de predictores
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de importancia de predictores
	"""

	df['colors'] = bokeh_utils.BAR_COLORS_PALETTE[:len(df['Attribute'].values)]

	source = ColumnDataSource(df)
	
	weight_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_range=df['Attribute'].values)

	weight_plot.vbar(x='Attribute', top='Weight', source=source, width=0.9, line_color='white', fill_color='colors')

	weight_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	weight_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	weight_plot.y_range.start = 0

	weight_plot.title.text = 'Importancia de los predictores'
	weight_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	weight_plot.title.align = 'left'
	weight_plot.title.text_font_size = '16px'
	weight_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR

	return weight_plot

def create_confusion_matrix(data_dict):
	"""Crea tabla de matriz de confusión
	Parameters:
		data_dict (dict): Diccionario con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de importancia de predictores
	"""

	'''Old version - DataTable
	# source = ColumnDataSource(data_dict)
	# columns = [TableColumn(field=key, title=key) for key in data_dict]

	# table = DataTable(source=source, columns=columns, max_width=700, height=200, sizing_mode='stretch_width')
	# table.min_border_right = 15
	'''
	# Paleta de colores
	colors = ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c','#08306b']

	# Had a specific mapper to map color with value
	mapper = LinearColorMapper(palette=colors, low=data_dict.value.min(), high=data_dict.value.max())

	# Define a figure
	p = figure(
		plot_height=270,
		# title="Matriz de confusión",
		x_range=list(data_dict.Actual.drop_duplicates()),
		y_range=list(reversed(data_dict.Prediction.drop_duplicates())),
		toolbar_location=None,
		tools="",
		x_axis_location="above",
		x_axis_label="Actual Label",
		y_axis_label="Predicted Label",
		sizing_mode='stretch_width')
	p.xaxis.axis_line_color = None
	p.yaxis.axis_line_color = None
	p.xaxis.major_label_orientation = np.pi/4
	
	# Create rectangle for heatmap
	p.rect(
		x="Actual",
		y="Prediction",
		width=1,
		height=1,
		source=ColumnDataSource(data_dict),
		line_color=None,
		fill_color=transform('value', mapper))
	p.text(x="Actual",
		y="Prediction", text='value', text_align="center", text_baseline="middle", source=ColumnDataSource(data_dict))
	
	p.border_fill_color = bokeh_utils.BACKGROUND_COLOR	
	p.background_fill_color = bokeh_utils.BACKGROUND_COLOR
	# p.title.text = 'Matriz de confusión'
	# p.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	# p.title.align = 'left'
	# p.title.text_font_size = '16px'
	# p.title.offset = -75
	# Add legend
	color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    ticker=BasicTicker(desired_num_ticks=len(colors)))
	color_bar.background_fill_color = bokeh_utils.BACKGROUND_COLOR

	p.add_layout(color_bar, 'right')

	return p, color_bar
	#return table

def create_decision_tree_menu():
	"""Crea menú de selección de variables para modelización del árbol de decisión

	Returns:
		Button: Botón del menú de selección
		Select: Panel de selección de variable del menú de selección
	"""

	option_values = []
	variables_file = open('resources/model_variables.txt', 'r')
	variables_file_lines = variables_file.readlines()

	for line in variables_file_lines:
		option_values.append(line.rstrip('\n'))
	
	option_values.sort(key=lambda option_value:(option_value[:2]!='O_', option_value))

	# selected_value = option_values[0]
	selected_value = 'Calidad_Agua'

	select = Select(value=selected_value, options=option_values, height=35)

	button = Button(label='Modelizar', button_type='primary', height=45)

	return button, select


def create_decision_tree_graph_renderer(plot, tree):
	"""Crea el renderizador del gráfico del árbol de decisión. Para ello se deben especificar configuraciones como: indices o identificadores
	de los nodos, colores de los nodos, tipos de figura de los nodos, tipos de figura de relación entre nodo y las relaciones entre los nodos (inicio y final)
	Parameters:
		plot (Figure): Figura Bokeh donde se muestra el árbol de decisión
		tree (Tree): Estructura del árbol de decisión a mostrar

	Returns:
		GraphRenderer: Renderizador del gráfico del árbol de decisión
	"""
	
	node_indices = [node.id for node in tree.node_list]
	node_colors = [node.color for node in tree.node_list]

	start, end = tree.get_nodes_relations()
	x, y = tree.get_layout_node_positions(plot)
	graph_layout = dict(zip(node_indices, zip(x,y)))

	graph = GraphRenderer()

	graph.node_renderer.data_source.add(node_indices, 'index')
	graph.node_renderer.data_source.add(node_colors, 'color')
	graph.node_renderer.glyph = Rect(height=0.15, width=0.2, fill_color='color')
	graph.edge_renderer.glyph = MultiLine(line_color='#b5b8bc', line_alpha=0.8, line_width=5)

	graph.edge_renderer.data_source.data = dict(
    	start=start,
    	end=end)

	graph.layout_provider = StaticLayoutProvider(graph_layout=graph_layout)

	return graph

def append_labels_to_decision_tree(plot, graph, tree):
	"""Añade los textos necesarios (nombre del nodo y condición de relación) al gráfico del árbol de visualización
	Parameters:
		plot (Figure): Figura Bokeh donde se muestra el árbol de decisión
		graph (GraphRenderer): Renderizador del gráfico del árbol de decisión
		tree (Tree): Estructura del árbol de decisión a mostrar

	Returns:
		Figure: Gráfica del árbol de decisión
	"""
	plot.renderers = []
	plot.renderers.append(graph)
	
	node_text_x, node_text_y, node_text = tree.get_node_text_positions()
	plot.text(node_text_x, node_text_y, text=node_text, text_font_size={'value': '10pt'}, text_align='center')

	middle_x, middle_y, middle_text = tree.get_line_text_positions()
	plot.text(middle_x, middle_y, text=middle_text, text_font_size={'value': '11pt'}, text_align='center')
	return plot


def create_decision_tree_plot():
	"""Crea la figura para visualizar el árbol de decisión

	Returns:
		Figure: Gráfica del árbol de decisión
	"""
	plot = figure(x_range=(-1.1,1.1), y_range=(0,1.1), toolbar_location=None, plot_height=500, sizing_mode='stretch_width')

	plot.axis.visible = False
	plot.xgrid.grid_line_color = None
	plot.ygrid.grid_line_color = None
	plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR	
	plot.background_fill_color = bokeh_utils.BACKGROUND_COLOR
	plot.outline_line_color = None

	return plot

def create_outlier_plot(df):
	"""Crea gráfica de outliers
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de outliers
	"""

	hover_tool = HoverTool(
		tooltips = [
			('Fecha', '@timestamp{%b %Y}'),
			('Outlier', '@outlier')
		],
		formatters = {
			'timestamp': 'datetime',
		},
		mode = 'mouse'
		)

	outlier_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')

	df['timestamp'] = pd.to_datetime(df['timestamp'])
	df['outlier'] = pd.to_numeric(pd.Series(df['outlier'].values))

	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_0, color=bokeh_utils.LINE_COLORS_PALETTE[0], size=6, legend='Cluster 0')
	outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_1, color=bokeh_utils.LINE_COLORS_PALETTE[1], size=6, legend='Cluster 1')
	outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_2, color=bokeh_utils.LINE_COLORS_PALETTE[2], size=6, legend='Cluster 2')
	outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_3, color=bokeh_utils.LINE_COLORS_PALETTE[3], size=6, legend='Cluster 3')

	outlier_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	outlier_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	outlier_plot.legend.location = 'top_left'
	outlier_plot.legend.orientation = 'horizontal'
	outlier_plot.legend.click_policy = 'hide'
	outlier_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	outlier_plot.xaxis[0].formatter = DatetimeTickFormatter(years=['%Y'])

	outlier_plot.title.text = 'Probabilidad de Outliers'
	outlier_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	outlier_plot.title.align = 'left'
	outlier_plot.title.text_font_size = '16px'
	outlier_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	outlier_plot.min_border_right = 15
	outlier_plot.add_tools(hover_tool)

	return outlier_plot

def create_prediction_plot(df):
	"""Crea gráfica de predicción a futuro
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de de predicción a futuro
	"""

	hover_tool = HoverTool(
		tooltips = [
			('Fecha', '$x{%b %Y}'),
			('Predicción', '@Prediction')
		],
		formatters = {
			'$x': 'datetime',
		},
		mode = 'mouse'
		)

	# Estructuración de los tipos de datos del dataframe
	df['añomes'] = pd.to_datetime(df['añomes'], format='%m/%d/%y %I:%M %p')
	df['Prediction'] = pd.to_numeric(pd.Series(df['Prediction'].values))

	prediction_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')
	
	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	x_axis_tick_vals = source_cluster_0.data['añomes'].astype(int) / 10**6

	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_0, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[0], legend='Cluster 0')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_1, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[1], legend='Cluster 1')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_2, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[2], legend='Cluster 2')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_3, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[3], legend='Cluster 3')

	prediction_plot.xaxis.major_label_orientation = np.pi/4
	prediction_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	prediction_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	prediction_plot.legend.location = 'top_left'
	prediction_plot.legend.orientation = 'horizontal'
	prediction_plot.legend.click_policy = 'hide'
	prediction_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR
	prediction_plot.xaxis[0].formatter = DatetimeTickFormatter(months=['%b %Y'])
	prediction_plot.xaxis[0].ticker = FixedTicker(ticks=list(x_axis_tick_vals))
	# print(x_axis_tick_vals)
	# Linea vertical para definir el horizonte de predicción
	prediction_date = time.mktime(dt(2019, 2, 1, 0, 0, 0).timetuple())*1000
	vline = Span(location=prediction_date, dimension='height', line_color='gray', line_alpha=0.6, line_dash='dotted', line_width=2)
	prediction_plot.add_layout(vline)
	# Etiqueta linea horizontal
	vlabel = Label(x=prediction_date, y=40, text='→Predicción', text_color='gray', text_alpha=0.6, text_font_size='14px')
	prediction_plot.add_layout(vlabel)

	prediction_plot.title.text = 'Predicción de los clusters a futuro'
	prediction_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	prediction_plot.title.align = 'left'
	prediction_plot.title.text_font_size = '16px'
	prediction_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	prediction_plot.add_tools(hover_tool)
	prediction_plot.min_border_right = 15


	return prediction_plot

def create_df_confusion(data_dict):
	"""Crea el dataframe para la matriz de confusion
	Parameters:
		data_dict (Diccionario): Diccionario ordenado con los datos de la matriz de confusión
	
	Returns:
		df: Dataframe con los datos convertidos para la matriz de confusion
	"""
	# Cargar datos
	df_original = pd.DataFrame(data_dict, columns=data_dict.keys())
	
	# Slicing dataframe for confussion matrix and removing redundant text
	df = df_original.drop("class_precision", axis=1)
	df['True'].replace(regex="pred.", value="", inplace=True)
	df = df.set_index("True")
	df = df.drop("class recall", axis=0)
	df.columns.name = 'Actual'
	df.index.name = 'Prediction'
	df = df.transpose()

	# Converting dataframe to right format
	df = df.apply(pd.to_numeric)
	df = df.stack().rename("value").reset_index()
	return df

def create_daily_pred_plot(df, target='Calidad_Agua'):
	"""Crea gráfica de predicciones contra valores reales
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de predicciones contra valores reales
	"""
	df.rename(columns={target: 'real', 'prediction-'+target+'-': 'prediction'}, inplace=True)
	df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y').sort_values()
	df = df.set_index('timestamp')
	df = df.groupby(df.index).first()
	df = df['2018-02-01':]
	# df.to_csv("df.csv")
	bins = list(df['real'].unique())
	print(bins)
	print(df.head(100))

	if target=='Calidad_Agua':
		df.replace(regex=['cluster_'], value='', inplace=True)
	else:
		df.replace(regex=[r'\[.*\]', 'range'], value='', inplace=True)
	
	df[['real','prediction']] = df[['real','prediction']].astype(int)
	df['error'] = abs(df['real']-df['prediction'])
	print(df.head())
	print(df.dtypes)
	# df.to_excel("df.xlsx", sheet_name="df2")

	TOOLTIPS = [
		('Fecha', "@timestamp{%F}"),
		('Real', '@real'),
		("Predicho", "@prediction")
	]
	hover = HoverTool(tooltips = TOOLTIPS, formatters={'timestamp': 'datetime'})

	source = ColumnDataSource(df)

	daily_pred_plot = figure(plot_height=200, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')

	daily_pred_plot.line(x='timestamp', y='real', source=source, line_width=2, line_color='#392FCC', legend='Real')
	daily_pred_plot.line(x='timestamp', y='prediction', source=source, line_width=2, line_color='#CA574D', line_dash='dashed', legend='Predicción')
	daily_pred_plot.line(x='timestamp', y='error', source=source, line_width=2, line_color='green', line_alpha=0.4, legend='Error')

	daily_pred_plot.xaxis.major_label_orientation = np.pi/4
	# x_axis_tick_vals = source.data['timestamp'].astype(int) / 10**6
	daily_pred_plot.xaxis[0].formatter = DatetimeTickFormatter(months=['%b %Y'])
	# daily_pred_plot.xaxis[0].ticker = FixedTicker(ticks=list(x_axis_tick_vals))
	daily_pred_plot.xaxis.ticker = MonthsTicker(months=list(range(12)))
	daily_pred_plot.yaxis[0].ticker.desired_num_ticks = len(bins)
	daily_pred_plot.yaxis.ticker =  list(range(len(bins)))
	if target == 'Calidad_Agua':
		daily_pred_plot.yaxis.formatter = PrintfTickFormatter(format="Cluster %u")
	else:
		daily_pred_plot.yaxis.formatter = PrintfTickFormatter(format="Range %u")
	daily_pred_plot.ygrid.minor_grid_line_color = None
	
	daily_pred_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	daily_pred_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	daily_pred_plot.legend.location = 'top_left'
	daily_pred_plot.legend.orientation = 'horizontal'
	daily_pred_plot.legend.click_policy = 'hide'
	daily_pred_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	daily_pred_plot.title.text = 'Predicciones diarias'
	daily_pred_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	daily_pred_plot.title.align = 'left'
	daily_pred_plot.title.text_font_size = '16px'
	daily_pred_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	daily_pred_plot.min_border_right = 15
	daily_pred_plot.add_tools(hover)

	return daily_pred_plot

def create_div_title(title = ''):
	div_title = Div(
				text=title,
				style={
					'font-weight': 'bold',
					'font-size': '16px',
					'color': bokeh_utils.TITLE_FONT_COLOR,
					'margin-top': '2px',
					'font-family': 'inherit'},
				height=20,
				sizing_mode='stretch_width')
	
	return div_title

def modify_second_descriptive(doc):
	models = set(['Calidad_Agua'])
	# Llamada al webservice de RapidMiner
	xml_prediction_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': 'Calidad_Agua', 'Discretizacion': 5})
	json_perfil_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out_JSON?', 'rapidminer', 'rapidminer', out_json=True)
	# TODO json_prediction_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion_JSON?', 'rapidminer', 'rapidminer', {'Objetivo': 'Calidad_Agua', 'Discretizacion': 'Calidad_Agua'})

	# Extracción de los datos web
	df_perfil = [json_normalize(data) for data in json_perfil_document]
	xml_prediction_root = et.fromstring(xml_prediction_document)
	# TODO df_prediction = [json_normalize(data) for data in json_prediction_document]

	decision_tree_xml = xml_prediction_root[0]
	performance_vector_xml = xml_prediction_root[1]
	weight_xml = xml_prediction_root[2]
	correct_xml = xml_prediction_root[3]
	prediction_df = df_perfil[3]
	outlier_df = df_perfil[4]
	daily_pred_df = get_dataframe_from_xml(correct_xml, ['timestamp', 'Calidad_Agua', 'prediction-Calidad_Agua-'])
	# print(daily_pred_df.head(100))

	decision_tree_data = create_decision_tree_data(decision_tree_xml.text)
	performance_vector_data_dict = create_performance_vector_data(performance_vector_xml.text)
	performance_vector_df = create_df_confusion(performance_vector_data_dict)
	weight_df = get_dataframe_from_xml(weight_xml, ['Weight', 'Attribute'])
	possible_values = list(performance_vector_data_dict.keys())
	possible_values.remove('True')
	possible_values.remove('class_precision')
	correct_values, correct_data_dict = create_correct_quantity_data(correct_xml, 'Calidad_Agua', possible_values)

	prediction_plot = create_prediction_plot(prediction_df)
	daily_pred_plot = create_daily_pred_plot(daily_pred_df, 'Calidad_Agua')
	outlier_plot = create_outlier_plot(outlier_df)
	decision_tree_plot = create_decision_tree_plot()
	decision_tree_graph = create_decision_tree_graph_renderer(decision_tree_plot, decision_tree_data)
	decision_tree_plot = append_labels_to_decision_tree(decision_tree_plot, decision_tree_graph, decision_tree_data)
	simulation_title = create_div_title('Simulación')
	add_model_button, model_select_menu = create_decision_tree_menu()
	model_select_wb = widgetbox([model_select_menu , add_model_button], max_width=200, sizing_mode='stretch_width')
	confusion_matrix, color_bar = create_confusion_matrix(performance_vector_df)
	weight_plot = create_attribute_weight_plot(weight_df)
	corrects_plot = create_corrects_plot(correct_values, correct_data_dict)
	confusion_title = create_div_title('Matriz de confusión')
	decision_tree_title = create_div_title('Arbol de decisión')
	created_models_checkbox = CheckboxButtonGroup(labels=list(models))
	created_models_checkbox.active = [0]
	model_plots = layout([
		[daily_pred_plot],
		[column([confusion_title, confusion_matrix], sizing_mode='stretch_width'), weight_plot, corrects_plot],
		[decision_tree_title],
		[decision_tree_plot]
	], name='Calidad_Agua')
	l = layout([
		[prediction_plot],
		[outlier_plot],
		[simulation_title],
		[model_select_wb, column(create_div_title('Modelos creados'), created_models_checkbox, sizing_mode='stretch_width')],
		[model_plots]
	], sizing_mode='stretch_both')

	def prediction_callback():
		# Llamar al sericio web EDAR_Cartuja_Prediccion con los nuevos parámetros
		model_objective = model_select_menu.value
		model_discretise = 5

		models.add(model_objective)
		created_models_checkbox.labels = list(models)
		# created_models_checkbox.active = list(models)

		# xml_prediction_document = call_webservice('http://smvhortonworks:8888/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': str(model_objective), 'Discretizacion': str(model_discretise)})
		xml_prediction_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': str(model_objective), 'Discretizacion': model_discretise})		
		xml_prediction_root = et.fromstring(xml_prediction_document)
		
		# Obtener datos
		decision_tree_xml = xml_prediction_root[0]
		performance_vector_xml = xml_prediction_root[1]
		weight_xml = xml_prediction_root[2]
		correct_xml = xml_prediction_root[3]

		# Actualizar árbol de decisión
		decision_tree_data = create_decision_tree_data(decision_tree_xml.text)
		decision_tree_graph = create_decision_tree_graph_renderer(decision_tree_plot, decision_tree_data)
		append_labels_to_decision_tree(decision_tree_plot, decision_tree_graph, decision_tree_data)

		# Actualizar matriz de confusión
		performance_vector_data_dict = create_performance_vector_data(performance_vector_xml.text)
		performance_vector_df = create_df_confusion(performance_vector_data_dict)
		source = ColumnDataSource(performance_vector_df)
		colors = ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c','#08306b']
		color_bar.color_mapper = LinearColorMapper(palette=colors, low=performance_vector_df.value.min(), high=performance_vector_df.value.max())
		confusion_matrix.x_range.factors = list(performance_vector_df.Actual.drop_duplicates())
		confusion_matrix.y_range.factors = list(reversed(performance_vector_df.Prediction.drop_duplicates()))
		confusion_matrix.renderers[0].data_source.data = source.data
		confusion_matrix.renderers[1].data_source.data = source.data
		
		# Actualizar gráfica de importancia de predictores
		weight_df = get_dataframe_from_xml(weight_xml, ['Weight', 'Attribute'])
		weight_df['colors'] = bokeh_utils.BAR_COLORS_PALETTE[:len(weight_df['Attribute'].values)]
		source = ColumnDataSource(weight_df)
		weight_plot.x_range.factors = list(weight_df['Attribute'].values)
		weight_plot.renderers[0].data_source.data = source.data

		# Actualizar gráfica de aciertos
		possible_values = list(performance_vector_data_dict.keys())
		possible_values.remove('True')
		possible_values.remove('class_precision')
		correct_values, correct_data_dict = create_correct_quantity_data(correct_xml, model_objective, possible_values)
		correct_data_dict['predictions'] = correct_values
		number_of_values = len(correct_data_dict.keys()) - 1
		bar_width = 0.1
		x_pos = create_corrects_plot_positions_data(number_of_values, bar_width)
		corrects_plot.legend[0].items = []	
		corrects_plot.renderers = []
		corrects_plot.x_range.factors = correct_values		
		create_bars_in_corrects_plot(corrects_plot, correct_data_dict, number_of_values, x_pos)

		# TODO
		# new_plots = layout([
		# 	[column([confusion_title, confusion_matrix], sizing_mode='stretch_width'), weight_plot, corrects_plot],
		# 	[decision_tree_title],
		# 	[decision_tree_plot]
		# ], name=list(models)[-1])
		new_plots = layout([
			[daily_pred_plot],
			[column([confusion_title, confusion_matrix], sizing_mode='stretch_width'), weight_plot, corrects_plot],
			[decision_tree_title],
			[decision_tree_plot]
		], name=list(models)[-1])

		model_plots.children.append(new_plots)
		
	add_model_button.on_click(prediction_callback)

	doc.add_root(l)
