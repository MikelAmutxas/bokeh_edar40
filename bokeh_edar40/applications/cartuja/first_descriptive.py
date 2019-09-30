from bokeh_edar40.visualizations.treemap import *
from utils.rapidminer_proxy import call_webservice 
from utils.xml_parser import get_dataframe_from_xml
import utils.bokeh_utils as bokeh_utils

from bokeh.layouts import column, row, widgetbox, layout
from bokeh.models import ColumnDataSource, Div, DateRangeSlider, DatePicker, Button, DataTable, TableColumn
from bokeh.models.markers import Circle
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc, show
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange

import pandas as pd
import xml.etree.ElementTree as et

def create_treemap(df):
	"""Crea la gráfica de rectángulos

	Parameters:
		df (Dataframe): Dataframe de datos
	"""


	def sum_indicador_values(indicador, df):
		"""Suma los valores de un indicador o variable concreta

		Parameters:
			df (Dataframe): Dataframe de datos
			indicador (String): Nombre del indicador del cual se deben sumar todos los valores

		Returns:
			float: Suma total de los valores del indicador
		"""
		df = df.loc[df['Indicador'].isin([indicador])]
		sum_valor = pd.to_numeric(pd.Series(df['valor'].values)).sum()
		return sum_valor

	def create_treemap_data(key_names, key_values, color_values):
		"""Crea el ColumnDataSource correcto con los datos para el gráfico de rectángulos

		Parameters:
			key_name (list): Lista de nombres de los indicadores o variables
			key_values (list): Lista de suma de valores totales de cada indicador
			color_values (list): Lista de colores en hexadecimal para aplicar a cada rectángulo

		Returns:
			ColumnDataSource: ColumnDataSource correcto con los datos para el gráfico de rectángulos
		"""
		source = ColumnDataSource(
			data = dict(
				Indicadores = key_names,
				Valor_Total = key_values,
				Colores = color_values
				)
			)

		return source
	
	def create_first_level_treemap_data(df):
		"""Crea el ColumnDataSource correcto para los rectángulos del primer nivel (mostrando las variables significativas)

		Parameters:
			df (Dataframe): Dataframe de datos

		Returns:
			ColumnDataSource: ColumnDataSource correcto para los rectángulos del primer nivel
		"""
		sum_total_values = []
		indicator_values = []
		indicators = df.drop_duplicates(subset='Indicador')
		color_values = ['#396ab1', '#da7c30', '#3e9651', '#cc2529']
		for indicator in indicators['Indicador']:
			sum_value = sum_indicador_values(indicator, df)
			if sum_value > 0:
				sum_total_values.append(sum_value)
				indicator_values.append(indicator)

		source = create_treemap_data(indicator_values, sum_total_values, color_values)
		return source

	def create_low_level_treemap_data(df, indicator, color_value):
		"""Crea el ColumnDataSource correcto para los rectángulos de niveles inferiores (mostrando tipos de calidad de agua construidos significativamente por esa variable)

		Parameters:
			df (Dataframe): Dataframe de datos
			indicator (String): Nombre del indicador o variable
			color_value (String): Color en hexadecimal para aplicar a cada rectángulo

		Returns:
			ColumnDataSource: ColumnDataSource correcto para los rectángulos de nivel inferior
		"""
		indicator_df = df.loc[df['Indicador'].isin([indicator])]
		sum_value = sum_indicador_values(indicator, df)
		if sum_value > 0:
			indicator_df['valor'] = pd.to_numeric(indicator_df['valor'])
			indicator_df = indicator_df[indicator_df['valor'] > 0]
			indicator_df = indicator_df.dropna(subset=['valor'])
			source = create_treemap_data(list(indicator_df['cluster']), list(indicator_df['valor']), [color_value]*len(indicator_df))
			return source

	def create_treemap_rects(total_source, x, y, width, height, rects, treemap_figure):
		"""Crea los rectángulos del gráfico de rectángulos

		Parameters:
			total_source (ColumnDataSource): ColumnDataSource con los datos a representar
			x (float): Posición x de comienzo para dibujar los rectángulos (para rectángulos de nivel inferior)
			y (float): Posición y de comienzo para dibujar los rectángulos (para rectángulos de nivel inferior)
			width (float): Anchura de espacio para dibujar los rectángulos
			height (float): Altura de espacio para dibujar los rectángulos
			rects (dict): Diccionario de rectángulos con toda la información necesaria para dibujarlos
			treemap_figure (Figure): Figura de Bokeh para visualizar el gráfico de rectángulos

		Returns:
			dict: Diccionario con la figura de Bokeh para visualizar el gráfico de rectángulos y un segundo diccionario con los rectángulos creados
		"""
		
		values = total_source.data['Valor_Total']
		values.sort(reverse=True)
		values = normalize_sizes(total_source.data['Valor_Total'], width, height)
		rects = squarify(values, x, y, width, height)

		X = [rect['x'] for rect in rects]
		Y = [rect['y'] for rect in rects]
		dX = [rect['dx'] for rect in rects]
		dY = [ rect['dy'] for rect in rects]

		XdX = []
		YdY = []

		for i in range(len(X)):
		    XdX.append(X[i]+dX[i])
		    YdY.append(Y[i]+dY[i])

		text_Y = [y - 0.06 for y in YdY]
		text_X = [x + 0.01 for x in X]

		treemap_figure.quad(top=YdY, bottom=Y, left=X, right=XdX, color=total_source.data['Colores'], line_color='black')
		
		return {'treemap': treemap_figure, 'rects': rects}

	def create_first_level_rect_text_data(rects, source):
		"""Crea el texto a mostrar (nombre de indicador o variable) en cada rectángulo del primer nivel

		Parameters:
			rects (dict): Diccionario de rectángulos con toda la información necesaria para dibujarlos
			source (ColumnDataSource): ColumnDataSource con los datos a representar

		Returns:
			dict: Diccionario con las coordenadas X e Y y el texto a mostrar en cada rectángulo del primer nivel
		"""
		x = []
		y = []
		text = []
		for rect in rects:
			x.append(rect['x']+0.01)
			y.append((rect['y'] + rect['dy'])-0.06)
		for indicador in source.data['Indicadores']:
			text.append(indicador)

		return {'x': x, 'y': y, 'text': text}

	def create_low_level_rect_text_data(rects, source, x, y, text):
		"""Crea el texto a mostrar (nombre de indicador o variable) en cada rectángulo de nivel inferior

		Parameters:
			rects (dict): Diccionario de rectángulos con toda la información necesaria para dibujarlos
			source (ColumnDataSource): ColumnDataSource con los datos a representar
			x (list): Lista de valores de coordenadas X para cada texto a mostrar
			y (list): Lista de valores de coordenadas Y para cada texto a mostrar
			text (list): Lista de valores de texto a mostrar


		Returns:
			dict: Diccionario con las coordenadas X e Y y el texto a mostrar en cada rectángulo del niveles inferiores
		"""
		
		# Vamos insertando los valores en las listas ya creadas en el primer nivel, debido a que el texto debe ser lo último al 
		# dibujar, si no, al dibujar rectángulos de nivel inferior el texto del primer nivel desaparece
		for rect in rects:
			x.append(((rect['x']+(rect['x']+rect['dx']))/2)-0.04)
			y.append(((rect['y']+(rect['y']+rect['dy']))/2)-0.02)
		for indicator in source.data['Indicadores']:
			text.append(indicator)

		return {'x': x, 'y': y, 'text': text}


	treemap_figure = figure(plot_height=400, sizing_mode='stretch_width', toolbar_location=None)
	treemap_figure.axis.visible = False
	treemap_figure.xgrid.grid_line_color = None
	treemap_figure.ygrid.grid_line_color = None

	first_level_source = create_first_level_treemap_data(df)
	# Comenzamos a crear los rectángulos teniendo todo el espacio libre
	treemap_info = create_treemap_rects(first_level_source, 0., 0., 1, 1, [], treemap_figure)
	rects = treemap_info['rects']
	treemap_figure = treemap_info['treemap']
	colores = bokeh_utils.BAR_COLORS_PALETTE[:len(df['Indicador'].values)]
	
	i = 0

	rect_text = create_first_level_rect_text_data(rects, first_level_source)
	new_rects_text = dict(
		x = [],
		y = [],
		text = []
		)

	indicadores = df.drop_duplicates(subset='Indicador')
	for indicador in indicadores['Indicador']:
		low_level_source = create_low_level_treemap_data(df, indicador, colores[i])
		if low_level_source != None:
			# Creamos los rectángulos de nivel inferior teniendo en cuenta el espacio disponible por el rectángulo del nivel superior
			treemap_info = create_treemap_rects(low_level_source, rects[i]['x'], rects[i]['y'], rects[i]['dx'],rects[i]['dy'], rects, treemap_info['treemap'])
			new_rects = treemap_info['rects']
			new_rects_text = create_low_level_rect_text_data(new_rects, low_level_source, new_rects_text['x'], new_rects_text['y'], new_rects_text['text'])
			treemap_figure = treemap_info['treemap']
			i = i + 1
	
	# Creamos el texto para cada rectángulo y luego lo mostramos, primero nivel superior y después inferiores
	treemap_figure.text(rect_text['x'], rect_text['y'], text=rect_text['text'], text_font_size={'value': '11pt'})
	treemap_figure.text(new_rects_text['x'], new_rects_text['y'], text=new_rects_text['text'], text_font_size={'value': '11pt'})

	treemap_figure.title.text = 'Indicadores normalizados en representación rectangular influentes en la calidad del agua'
	treemap_figure.title.align = 'left'
	treemap_figure.title.text_font_size = '16px'

	return treemap_figure

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


def create_normalize_plot(df):
	import numpy as np
	"""Crea gráfica de variables afectando en cada tipo de calidad de agua con valores normalizados
	
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de variables afectando en cada tipo de calidad de agua con valores normalizados
	"""
	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	TOOLTIPS = [
		('Indicador', '@Indicador'),
		('Valor', '@valor'),
	]

	normalize_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_range=FactorRange(factors=source_cluster_0.data['Indicador']), tooltips=TOOLTIPS)
	normalize_plot.line(x='Indicador', y='valor', source=source_cluster_0, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[0], legend='Cluster 0')
	normalize_plot.line(x='Indicador', y='valor', source=source_cluster_1, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[1], legend='Cluster 1')
	normalize_plot.line(x='Indicador', y='valor', source=source_cluster_2, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[2], legend='Cluster 2')
	normalize_plot.line(x='Indicador', y='valor', source=source_cluster_3, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[3], legend='Cluster 3')

	normalize_plot.xaxis.major_label_orientation = np.pi/2
	normalize_plot.xaxis.axis_label = 'Indicador (promedio)'

	normalize_plot.y_range.start = -2
	normalize_plot.y_range.end = 3
	normalize_plot.legend.location = 'top_left'
	normalize_plot.legend.orientation = 'horizontal'
	normalize_plot.legend.click_policy = 'hide'

	normalize_plot.title.text = 'Indicadores normalizados influentes en la calidad del agua'
	normalize_plot.title.align = 'left'
	normalize_plot.title.text_font_size = '16px'

	return normalize_plot

def create_not_normalize_plot(df):
	"""Crea tabla de variables afectando en cada tipo de calidad de agua con valores sin normalizar
	
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		DataTable: Tabla de variables afectando en cada tipo de calidad de agua con valores sin normalizar
	"""
	units = 4*["tuni1","tuni2","tuni3","tuni4","tuni5","tuni6","tuni7","tuni8","tuni9","tuni10"]
	source = ColumnDataSource(df.assign(Units=units))
	columns = [
		TableColumn(field='cluster', title='Cluster', width=100),
		TableColumn(field='Indicador', title='Indicador', width=200),
		TableColumn(field='valor', title='Valor', width=80),
		TableColumn(field='Units', title='Unidad', width=50)
	]

	data_table = DataTable(source=source, columns=columns, selectable=False, sizing_mode='fixed', width=470, height=376)

	return data_table

def create_weight_plot(df):
	"""Crea gráfico de importancia de variables sobre calidad del agua
	
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		DataTable: Gráfico de importancia de variables sobre calidad del agua
	"""

	source = ColumnDataSource(df)

	TOOLTIPS = [
		('Atributo', '@Attribute'),
		('Peso', '@Weight'),
	]

	weight_plot = figure(height=400, toolbar_location=None, sizing_mode='stretch_width',y_range=FactorRange(factors=source.data['Attribute']), x_range=(0,1), tooltips=TOOLTIPS)
	weight_plot.hbar(y='Attribute', left='Weight', right=0, source=source, height=0.6, fill_color=bokeh_utils.BAR_COLORS_PALETTE[0], line_color=bokeh_utils.BAR_COLORS_PALETTE[0])

	weight_plot.title.text = 'Peso de indicadores sobre calidad del agua'
	weight_plot.title.align = 'left'
	weight_plot.title.text_font_size = '16px'
	return weight_plot

def create_description():
	"""Crea panel de descripción del dashboard

	Returns:
		Div: Panel de descripción del dashboard
	"""

	desc = Div(text='''
	<!--<div class="row">
		<div class="card mb-4">
			<div class="card-header">
				<h6 class="m-0 font-weight-bold text-dark">Información General</h6>
			</div>
			<div class="card-body">
				Este dashboard muestra la monitorización de calidad del agua de la planta EDAR Cartuja. POR COMPLETAR
			</div>
		</div>
	</div>-->
	''')
	return desc

def create_table_title():
	"""Crea tiítulo en forma de Div para la tabla de variables afectando en cada tipo de calidad de agua con valores sin normalizar, ya que,
	las tablas de Bokeh no disponen de la opción de insertar un título por defecto

	Returns:
		Div: Título de la tabla
	"""

	title = Div(text='Indicadores sin normalizar influentes en la calidad del agua', style={'font-weight': 'bold', 'font-size': '16px', 'color': '#343a40', 'margin-top': '2px', 'font-family': 'inherit'}, width=470, height=10)
	return title

def modify_first_descriptive(doc):

	desc = create_description()

	#xml_document = call_webservice('http://smvhortonworks:8888/api/rest/process/EDAR_Cartuja_Perfil_Out?', 'rapidminer', 'rapidminer')	
	xml_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out?', 'rapidminer', 'rapidminer')
	xml_root = et.fromstring(xml_document)

	normalize_xml = xml_root[0]
	not_normalize_xml = xml_root[1]
	weight_xml = xml_root[2]
	
	normalize_df = get_dataframe_from_xml(normalize_xml, ['cluster', 'Indicador', 'valor'])
	
	normalize_df["Indicador"] = normalize_df["Indicador"].astype("str")
	normalize_df.Indicador.replace('(','podio',inplace=True)
	not_normalize_df = get_dataframe_from_xml(not_normalize_xml, ['cluster', 'Indicador', 'valor'])
	weight_df = get_dataframe_from_xml(weight_xml, ['Attribute', 'Weight'])
	
	normalize_plot = create_normalize_plot(normalize_df)
	treemap_plot = create_treemap(normalize_df)
	not_normalize_table = create_not_normalize_plot(not_normalize_df)
	not_normalize_table_title = create_table_title()
	not_normalize_widget_box = widgetbox([not_normalize_table_title, not_normalize_table], width=470, height=400, sizing_mode='fixed', spacing=3)
	weight_plot = create_weight_plot(weight_df)

	l = layout([
		[desc],
		[normalize_plot, treemap_plot],
		[not_normalize_widget_box, weight_plot]
	], sizing_mode='stretch_both')

	doc.add_root(l)
