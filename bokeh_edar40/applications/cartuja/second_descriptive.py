from utils.rapidminer_proxy import call_webservice
from utils.xml_parser import get_dataframe_from_xml, create_performance_vector_data, create_correct_quantity_data, create_decision_tree_data
import utils.bokeh_utils as bokeh_utils

from bokeh_edar40.visualizations.decision_tree import *

from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Div, HoverTool, GraphRenderer, StaticLayoutProvider, Rect, MultiLine, LinearAxis, Grid, Legend, LegendItem
from bokeh.models.ranges import FactorRange
from bokeh.models.widgets import Select, Button, TableColumn, DataTable
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.transform import jitter, factor_cmap, dodge

import xml.etree.ElementTree as et
import pandas as pd


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

	corrects_plot.legend.location = 'top_left'
	corrects_plot.legend.orientation = 'vertical'
	corrects_plot.legend.click_policy = 'hide'

	corrects_plot.title.text = 'Gráfica de aciertos'
	corrects_plot.title.align = 'left'
	corrects_plot.title.text_font_size = '16px'

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

	weight_plot.y_range.start = 0

	weight_plot.title.text = 'Importancia de los predictores'
	weight_plot.title.align = 'left'
	weight_plot.title.text_font_size = '16px'

	return weight_plot


def create_performance_vector_table(data_dict):
	"""Crea tabla de matriz de confusión
	Parameters:
		data_dict (dict): Diccionario con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de importancia de predictores
	"""

	source = ColumnDataSource(data_dict)
	columns = [TableColumn(field=key, title=key) for key in data_dict]

	table = DataTable(source=source, columns=columns, height=200, sizing_mode='stretch_width')

	return table

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

	selected_value = option_values[0]

	select = Select(value=selected_value, options=option_values, width=330, height=35)

	button = Button(label='Modelizar', button_type='primary', width=330, height=45)

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

	outlier_plot.legend.location = 'top_left'
	outlier_plot.legend.orientation = 'horizontal'
	outlier_plot.legend.click_policy = 'hide'
	outlier_plot.xaxis[0].formatter = DatetimeTickFormatter(years=['%Y'])

	outlier_plot.title.text = 'Probabilidad de Outliers'
	outlier_plot.title.align = 'left'
	outlier_plot.title.text_font_size = '16px'
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

	prediction_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime')

	df['añomes'] = pd.to_datetime(df['añomes'], format='%m/%d/%y %I:%M %p')
	df['Prediction'] = pd.to_numeric(pd.Series(df['Prediction'].values))
	
	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	x_axis_tick_vals = source_cluster_0.data['añomes'].astype(int) / 10**6

	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_0, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[0], legend='Cluster 0')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_1, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[1], legend='Cluster 1')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_2, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[2], legend='Cluster 2')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_3, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[3], legend='Cluster 3')

	prediction_plot.legend.location = 'top_left'
	prediction_plot.legend.orientation = 'horizontal'
	prediction_plot.legend.click_policy = 'hide'
	prediction_plot.xaxis[0].formatter = DatetimeTickFormatter(months=['%b %Y'])
	prediction_plot.xaxis[0].ticker = FixedTicker(ticks=list(x_axis_tick_vals))

	prediction_plot.title.text = 'Predicción de los clusters a futuro'
	prediction_plot.title.align = 'left'
	prediction_plot.title.text_font_size = '16px'
	prediction_plot.add_tools(hover_tool)


	return prediction_plot

def create_description():
	"""Crea panel de descripción del dashboard

	Returns:
		Div: Panel de descripción del dashboard
	"""
	desc = Div(text="""
	<h1 class="display-4">Monitorización planta EDAR Cartuja</h1>
	<p class="lead">Este dashboard muestra la monitorización de calidad del agua de la planta EDAR Cartuja.</p>
	""")
	return desc

def modify_second_descriptive(doc):

	desc = create_description()

	# xml_perfil_document = call_webservice('http://smvhortonworks:8888/api/rest/process/EDAR_Cartuja_Perfil_Out', 'rapidminer', 'rapidminer')
	xml_perfil_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out', 'rapidminer', 'rapidminer')	
	# xml_prediction_document = call_webservice('http://smvhortonworks:8888/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': 'Calidad_Agua', 'Discretizacion': 'Calidad_Agua'})
	xml_prediction_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': 'Calidad_Agua', 'Discretizacion': 'Calidad_Agua'})

	xml_perfil_root = et.fromstring(xml_perfil_document)
	xml_prediction_root = et.fromstring(xml_prediction_document)

	decision_tree_xml = xml_prediction_root[0]
	performance_vector_xml = xml_prediction_root[1]
	weight_xml = xml_prediction_root[2]
	correct_xml = xml_prediction_root[3]
	prediction_xml = xml_perfil_root[3]
	outlier_xml = xml_perfil_root[4]
	
	prediction_df = get_dataframe_from_xml(prediction_xml, ['Prediction', 'cluster', 'añomes'])
	outlier_df = get_dataframe_from_xml(outlier_xml, ['outlier', 'timestamp', 'pc_1', 'pc_2', 'cluster'])
	decision_tree_data = create_decision_tree_data(decision_tree_xml.text)
	performance_vector_data_dict = create_performance_vector_data(performance_vector_xml.text)	
	weight_df = get_dataframe_from_xml(weight_xml, ['Weight', 'Attribute'])
	possible_values = list(performance_vector_data_dict.keys())
	possible_values.remove('True')
	possible_values.remove('class_precision')
	correct_values, correct_data_dict = create_correct_quantity_data(correct_xml, 'Calidad_Agua', possible_values)

	
	prediction_plot = create_prediction_plot(prediction_df)
	outlier_plot = create_outlier_plot(outlier_df)
	decision_tree_plot = create_decision_tree_plot()
	decision_tree_graph = create_decision_tree_graph_renderer(decision_tree_plot, decision_tree_data)
	decision_tree_plot = append_labels_to_decision_tree(decision_tree_plot, decision_tree_graph, decision_tree_data)
	decision_tree_menu_title = Div(text='Árbol de decisión', style={'font-weight': 'bold', 'font-size': '16px', 'color': '#343a40', 'margin-top': '2px', 'font-family': 'inherit'}, height=20, sizing_mode='stretch_width')
	decision_tree_selection_button, decision_tree_selection_select_menu = create_decision_tree_menu()
	decision_tree_selection_wb = widgetbox([decision_tree_selection_select_menu , decision_tree_selection_button], width=350, height=100, sizing_mode='fixed')
	performance_vector_table = create_performance_vector_table(performance_vector_data_dict)
	weight_plot = create_attribute_weight_plot(weight_df)
	corrects_plot = create_corrects_plot(correct_values, correct_data_dict)

	l = layout([
		[desc],
		[prediction_plot],
		[outlier_plot],
		[decision_tree_menu_title],
		[decision_tree_selection_wb, performance_vector_table],
		[decision_tree_plot],
		[weight_plot, corrects_plot]

	], sizing_mode='stretch_both')

	def prediction_callback():

		# Llamar al sericio web EDAR_Cartuja_Prediccion con los nuevos parámetros
		model_objective = decision_tree_selection_select_menu.value
		if model_objective == 'Calidad_Agua':
			model_discretise = '10'
		else:
			model_discretise = model_objective

		# xml_prediction_document = call_webservice('http://smvhortonworks:8888/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': str(model_objective), 'Discretizacion': str(model_discretise)})
		xml_prediction_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion', 'rapidminer', 'rapidminer', {'Objetivo': str(model_objective), 'Discretizacion': str(model_discretise)})		
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

		# Acturalizar matriz de confusión
		performance_vector_data_dict = create_performance_vector_data(performance_vector_xml.text)
		source = ColumnDataSource(performance_vector_data_dict)
		columns = [TableColumn(field=key, title=key) for key in performance_vector_data_dict]
		performance_vector_table.source.data = source.data
		performance_vector_table.columns = columns

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


	decision_tree_selection_button.on_click(prediction_callback)

	doc.add_root(l)
