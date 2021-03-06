from bokeh_edar40.visualizations.treemap import normalize_sizes, squarify
from utils.rapidminer_proxy import call_webservice 
import utils.bokeh_utils as bokeh_utils

from bokeh.layouts import column, row, widgetbox, grid,layout
from bokeh.models import ColumnDataSource, Div, DateRangeSlider, DatePicker, Button, DataTable, TableColumn, LabelSet, Span, Label
from bokeh.models.markers import Circle
from bokeh.plotting import figure, curdoc, show
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models.tools import HoverTool
from bokeh.models.widgets import Tabs, Panel

import pandas as pd
from pandas.io.json import json_normalize
import numpy as np
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
			# indicator_df['valor'] = pd.to_numeric(indicator_df['valor'])
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

		# text_Y = [y - 0.06 for y in YdY]
		# text_X = [x + 0.01 for x in X]

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
	treemap_figure.x_range.range_padding = 0
	treemap_figure.y_range.range_padding = 0

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

	treemap_figure.title.text = 'Mapa de arbol de indicadores influentes'
	treemap_figure.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	treemap_figure.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	treemap_figure.background_fill_color = bokeh_utils.BACKGROUND_COLOR
	treemap_figure.title.align = 'left'
	treemap_figure.title.text_font_size = '16px'
	treemap_figure.outline_line_color = None
	treemap_figure.min_border_left = 0
	treemap_figure.min_border_right = 15
	treemap_figure.min_border_bottom = 0
	treemap_figure.min_border_top = 0

	return treemap_figure

def create_data_source_from_dataframe(df, group_value_name, group_value):
	"""Crea ColumnDataSource desde DataFrame agrupando los valores de una columna concreta según un valor
	
	Parameters:
		df (Dataframe): Dataframe de datos
		group_value_name (string): Nombre de columna donde buscar los valores a agrupar
		group_value (string): Valor para agrupar los datos
	
	Returns:
		ColumnDataSource: ColumnDataSource con los datos correctamente agrupados
	"""

	df = df.loc[df[group_value_name].isin([group_value])]
	source = ColumnDataSource(df)
	return source


def create_normalize_plot(df):
	"""Crea gráfica de variables afectando en cada tipo de calidad de agua con valores normalizados
	
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de variables afectando en cada tipo de calidad de agua con valores normalizados
	"""

	NUM_CLUSTERS = df.cluster.nunique()	# Extraer numero clusters
	
	# source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	# source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	# source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	# source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')
	source_cluster = []
	for i in range(NUM_CLUSTERS):
		source_cluster.append(create_data_source_from_dataframe(df, 'cluster', f'cluster_{i}'))
		# print(source_cluster[i].data)

	TOOLTIPS = [
		('Indicador', '@Indicador'),
		('Valor', '@valor')
	]

	normalize_plot = figure(plot_height=350, toolbar_location=None, sizing_mode='stretch_width',
							x_range=FactorRange(factors=source_cluster[0].data['Indicador']), tooltips=TOOLTIPS)
	# Linea horizontal de anotación sobre nivel máximo de 0 a 1
	hline = Span(location=1, dimension='width', line_color='red', line_alpha=0.6, line_dash='dotted', line_width=2)
	
	normalize_plot.add_layout(hline)

	# Etiqueta linea horizontal
	hlabel = Label(x=8.7, y=1, text='Max', text_color='red', text_alpha=0.6, text_font_size='14px')
	normalize_plot.add_layout(hlabel)

	for i in range(NUM_CLUSTERS):
		normalize_plot.line(x='Indicador', y='valor', source=source_cluster[i], line_dash='dashed', line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[i], legend_label=f'Cluster {i}')
		normalize_plot.circle(x='Indicador', y='valor', source=source_cluster[i], size=8, line_color=bokeh_utils.LINE_COLORS_PALETTE[i],fill_color='white', legend_label=f'Cluster {i}')

	normalize_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	normalize_plot.xaxis.major_label_orientation = np.pi/4
	normalize_plot.xaxis.axis_label = 'Indicador (promedio)'
	normalize_plot.xaxis.axis_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	normalize_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	normalize_plot.yaxis.axis_label = 'Valor (normalizado)'
	normalize_plot.yaxis.axis_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	normalize_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	normalize_plot.y_range.start = -2
	normalize_plot.y_range.end = 3
	normalize_plot.legend.location = 'top_left'
	normalize_plot.legend.orientation = 'horizontal'
	normalize_plot.legend.click_policy = 'hide'
	normalize_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR
	normalize_plot.legend.background_fill_alpha = 0
	normalize_plot.legend.border_line_alpha = 0


	normalize_plot.title.text = 'Perfil de la calidad del agua'
	# normalize_plot.title.text_font = 'helvetica'
	normalize_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	normalize_plot.title.align = 'left'
	normalize_plot.title.text_font_size = '1rem'
	normalize_plot.title.visible = False
	normalize_plot.min_border_right = 20

	return normalize_plot


def create_radar_plot(df):
	"""Crea gráfica de radar afectando en cada tipo de calidad de agua con valores normalizados
	
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de radar afectando en cada tipo de calidad de agua con valores normalizados
	"""

	def unit_poly_verts(theta, r=0.5, center=0.5):
		"""Return vertices of polygon for subplot axes.
		This polygon is circumscribed by a unit circle centered at center(def:(0.5, 0.5))
		"""
		x0, y0 = [center] * 2
		verts = [(r*np.cos(t) + x0, r*np.sin(t) + y0) for t in theta]
		return verts

	def radar_patch(r, theta, center):
		yt = (r + 0.01) * np.sin(theta) + center
		xt = (r + 0.01) * np.cos(theta) + center
		return xt, yt

	NUM_VARS = df.Indicador.nunique() # Extraer numero de indicadores
	CENTER = 0.5 # Centro del gráfico de araña
	GRID_STEPS = 5 # Grid Subdivisions

	theta = np.linspace(0, 2*np.pi, NUM_VARS, endpoint=False)
	# rotate theta such that the first axis is at the top
	theta += np.pi/2

	x = [] # x-vertices
	y = [] # y-vertices
	# x_var_label = [] # x-vertices for variable labels
	x_ticks = [0.5]*(GRID_STEPS-1) # x-vertices for circular grid ticks
	y_ticks = [] # y-vertices for circular grid tick
	text = list(df.Indicador.unique()) # List with variable names

	#Tooltip creation
	TOOLTIPS = [('Indicador', '@Indicador'),
				('Valor', '@valor'),
				('Valor(esc)', '@valor_map')]
	hover = HoverTool(names=['radar_plt'], tooltips=TOOLTIPS)

	# Create radar figure
	nor_rad_pl = figure(plot_height=340, toolbar_location=None, x_range=(-0.2,1.4),
						y_range=(-0.1,1.1), tools=[hover,], sizing_mode='stretch_width')

	for i in range(GRID_STEPS):
		verts=unit_poly_verts(theta, (GRID_STEPS-i)*0.5/GRID_STEPS, CENTER)
		x.append([v[0] for v in verts])
		y.append([v[1] for v in verts])
		if i==0:
			source = ColumnDataSource({'x':x[i]+ [CENTER],'y':y[i]+ [(GRID_STEPS-i)*0.5/GRID_STEPS+CENTER],'text':text+ ['']})
			# source_test = ColumnDataSource({'x':x_var_label + [CENTER],'y':y[i]+ [(GRID_STEPS-i)*0.5/GRID_STEPS+CENTER],'text':text+ ['']})
			var_labels = LabelSet(x="x",y="y",text="text",source=source, text_color=bokeh_utils.LABEL_FONT_COLOR, text_font_size='15px') # Position variable labels
			nor_rad_pl.add_layout(var_labels) # Add variable labels
			color='black'
		else:
			source = ColumnDataSource({'x':x[i]+ [CENTER],'y':y[i]+ [(GRID_STEPS-i)*0.5/GRID_STEPS+CENTER]}) #radius*i/GRID_STEPS+CENTER
			color='gainsboro'
		nor_rad_pl.line(x="x", y="y", source=source, line_color=color) # Create poligons
		y_ticks.append(y[i][0]) # Store y-vertices grid ticks positions

	for i in range(NUM_VARS):
		nor_rad_pl.line(x=[CENTER,x[0][i]], y=[CENTER,y[0][i]], line_color='gainsboro') # Create grid lines from center to vertix

	y_ticks.reverse()
	text_labels_ticks = np.around(list(np.linspace(0, 1, GRID_STEPS, endpoint=False)), decimals=2) # Create text for grid ticks
	source_labels_ticks = ColumnDataSource({'x':x_ticks,'y':y_ticks[:-1],'text':text_labels_ticks[1:]})
	tick_labels = LabelSet(x="x",y="y",text="text",source=source_labels_ticks, text_color=bokeh_utils.LABEL_FONT_COLOR, text_font_size='14px') # Position grid tick labels
	nor_rad_pl.add_layout(tick_labels) # Add grid tick labels

	clist = []	# Cluster data list for spider pl patches
	colors = bokeh_utils.LINE_COLORS_PALETTE
	DATA_MIN = -2
	DATA_MAX = 3

	for i, cluster in enumerate(df.cluster.unique()):
		clist.append(df[df['cluster'] == cluster])
		xt, yt = radar_patch((clist[i].valor-DATA_MIN)/(DATA_MAX-DATA_MIN) * 0.5, theta, CENTER)
		clist[i]=clist[i].assign(**{'xt':xt, 'yt':yt, 'valor_map':(clist[i].valor-DATA_MIN)/(DATA_MAX-DATA_MIN)})
		nor_rad_pl.patch(x='xt', y='yt', fill_alpha=0.15, fill_color=colors[i], line_color=colors[i], legend_label=f'Cluster {i}', source=ColumnDataSource(clist[i]))
		nor_rad_pl.circle(x='xt', y='yt', size=15, fill_color=None, line_color=None ,source=ColumnDataSource(clist[i]), name='radar_plt')

	nor_rad_pl.legend.location = 'bottom_left'
	nor_rad_pl.legend.orientation = 'vertical'
	nor_rad_pl.legend.click_policy = 'hide'
	nor_rad_pl.legend.background_fill_alpha = 0
	nor_rad_pl.legend.border_line_alpha = 0
	nor_rad_pl.xgrid.visible = False
	nor_rad_pl.ygrid.visible = False
	nor_rad_pl.xaxis.visible = False
	nor_rad_pl.yaxis.visible = False
	nor_rad_pl.min_border = 0
	nor_rad_pl.outline_line_color = None
	nor_rad_pl.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	nor_rad_pl.background_fill_color = bokeh_utils.BACKGROUND_COLOR
	return nor_rad_pl


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
		TableColumn(field='cluster', title='Cluster', width=20),
		TableColumn(field='Indicador', title='Indicador (promedio)', width=72),
		TableColumn(field='valor', title='Valor', width=30),
		TableColumn(field='Units', title='Unidad', width=30)
	]

	data_table = DataTable(source=source, columns=columns, selectable=False, sizing_mode='stretch_width', max_width=650, height=200)

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

	weight_plot = figure(max_width=650, height=400, toolbar_location=None, sizing_mode='stretch_width',y_range=FactorRange(factors=source.data['Attribute']), x_range=(0,1), tooltips=TOOLTIPS)
	weight_plot.hbar(y='Attribute', left='Weight', right=0, source=source, height=0.6, fill_color=bokeh_utils.BAR_COLORS_PALETTE[0], line_color=bokeh_utils.BAR_COLORS_PALETTE[0])

	weight_plot.title.text = 'Peso de indicadores influentes'
	weight_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	weight_plot.title.align = 'left'
	weight_plot.title.text_font_size = '16px'
	weight_plot.title.offset = -100
	weight_plot.min_border_right = 15
	weight_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	weight_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	weight_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR

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

def create_title(text):
	"""Crea tiítulo en forma de Div para la tabla de variables afectando en cada tipo de calidad de agua con valores sin normalizar, ya que,
	las tablas de Bokeh no disponen de la opción de insertar un título por defecto

	Returns:
		Div: Título de la tabla
	"""

	title = Div(text=text, style={'font-weight': 'bold', 'font-size': '16px', 'color': bokeh_utils.TITLE_FONT_COLOR, 'margin-bottom': '2px', 'font-family': 'inherit'}, width=470, height=16)
	return title

def modify_first_descriptive(doc):
	args = doc.session_context.request.arguments
	try:
		periodo = int(args.get('periodo')[0])
	except:
		periodo = 0
	print(f'periodo: {periodo}')
	# desc = create_description()
	# Llamada al webservice de RapidMiner
	json_document = call_webservice('http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out_JSON?', 'rapidminer', 'rapidminer', out_json=True)
	df_perfil = [json_normalize(data) for data in json_document]
	
	# Extracción de los dataframe en valores absolutos
	normalize_df = df_perfil[0]
	not_normalize_df = df_perfil[1]
	weight_df = df_perfil[2]

	# Extracción de los dataframe en valores de rendimientos
	normalize_rend_df = df_perfil[0]
	not_normalize_rend_df = df_perfil[1]
	weight_rend_df = df_perfil[2]

	# Eliminamos texto repetido average() de los indicadores
	normalize_df['Indicador']=normalize_df['Indicador'].replace(regex=[r'\(', r'\)', 'average'],value='')	
	not_normalize_df['Indicador']=not_normalize_df['Indicador'].replace(regex=[r'\(', r'\)', 'average'],value='')
	normalize_rend_df['Indicador']=normalize_rend_df['Indicador'].replace(regex=[r'\(', r'\)', 'average'],value='')	
	not_normalize_rend_df['Indicador']=not_normalize_rend_df['Indicador'].replace(regex=[r'\(', r'\)', 'average'],value='')	

	# Convertimos las columnas numericas a flotante
	normalize_df['valor'] = normalize_df['valor'].astype('float')
	not_normalize_df['valor'] = not_normalize_df['valor'].astype('float')
	normalize_rend_df['valor'] = normalize_rend_df['valor'].astype('float')
	not_normalize_rend_df['valor'] = not_normalize_rend_df['valor'].astype('float')

	# Creación de los gráficos
	## Gráfico de perfil y araña normalizado-absolutos
	normalize_plot = create_normalize_plot(normalize_df)
	nor_rad_pl = create_radar_plot(normalize_df)
	l_panel = Panel(child=nor_rad_pl, title='Diagrama de araña')
	r_panel = Panel(child=normalize_plot, title='Diagrama de linea')
	profile_tabs = Tabs(tabs=[l_panel, r_panel], height = 400, sizing_mode="stretch_both", max_width=650, margin=[0,10,0,0])
	profile_title = create_title('Perfil de calidad del agua (normalizado-absolutos)')
	profile_widget_box = widgetbox([profile_title, profile_tabs], max_width=650, height=400, sizing_mode='stretch_width', spacing=3)
	
	## Gráfico de perfil y araña normalizado-rendimientos
	nor_rad_pl_rend = create_radar_plot(normalize_rend_df)
	normalize_plot_rend = create_normalize_plot(normalize_rend_df)
	l_panel_rend = Panel(child=nor_rad_pl_rend, title='Diagrama de araña')
	r_panel_rend = Panel(child=normalize_plot_rend, title='Diagrama de linea')
	profile_tabs_rend = Tabs(tabs=[l_panel_rend, r_panel_rend], height = 400, sizing_mode="stretch_both", max_width=650, margin=[0,10,0,0])
	profile_title_rend = create_title('Perfil de calidad del agua (normalizado-rendimientos)')
	profile_widget_box_rend = widgetbox([profile_title_rend, profile_tabs_rend], max_width=650, height=400, sizing_mode='stretch_width', spacing=3)

	## Tabla sin normalizar valores absolutos
	not_normalize_table_title = create_title('Indicadores influentes sin normalizar (absolutos)')
	not_normalize_table = create_not_normalize_plot(not_normalize_df)
	not_normalize_widget_box = widgetbox([not_normalize_table_title, not_normalize_table], max_width=650, height=250, sizing_mode='stretch_width', spacing=3)

	## Tabla sin normalizar valores rendimientos
	not_normalize_table_title_rend = create_title('Indicadores influentes sin normalizar (rendimientos)')
	not_normalize_table_rend = create_not_normalize_plot(not_normalize_rend_df)
	not_normalize_widget_box_rend = widgetbox([not_normalize_table_title_rend, not_normalize_table_rend], max_width=650, height=250, sizing_mode='stretch_width', spacing=3)
	
	## Gráfico de peso de indicadores absolutos y rendimientos
	weight_plot = create_weight_plot(weight_df)
	weight_plot_rend = create_weight_plot(weight_rend_df)

	# Distribución de los gráficos con una grid de bokeh
	l = grid([
		[profile_widget_box, profile_widget_box_rend],
		[not_normalize_widget_box, not_normalize_widget_box_rend],
		[weight_plot, weight_plot_rend]],
		sizing_mode='stretch_both')

	doc.add_root(l)
