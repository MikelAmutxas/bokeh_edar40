import pandas as pd
import re
from bokeh_edar40.visualizations.decision_tree import Node, Tree
import utils.bokeh_utils as bokeh_utils
import collections


def get_dataframe_from_xml(result_set, df_cols):
	"""Crea un dataframe desde el contenido de un fichero XML
	
	Parameters:
		result_set (Element): Resultados del fichero XML <example-set>
		df_cols (list): Lista de nombres de columnas a parsear
	
	Returns:
		Dataframe: Dataframe creado del contenido del fichero XML
	"""
	out_df = pd.DataFrame(columns = df_cols)
	for result in result_set:
		res = []
		for el in df_cols:
			if result is not None and result.find(el) is not None:
				res.append(result.find(el).text)
			else:
				res.append(None)
		out_df = out_df.append(pd.Series(res, index=df_cols), ignore_index = True)

	return out_df

def create_performance_vector_data(xml_text):
	"""Obtiene los datos para la matriz de confusión desde el contenido del fichero XML
	
	Parameters:
		xml_text (string): El contenido XML para parsear
	
	Returns:
		dict: Diccionario con los datos parseados para la matriz de confusión
	"""

	# Eliminamos del contenido en formato XML las líneas que no nos interesan
	xml_lines = xml_text.splitlines()
	xml_lines.pop(0)
	xml_lines.pop(0)
	title = xml_lines.pop(0)
	xml_lines.pop(0)

	column_titles = []
	data_dict = collections.OrderedDict()
	class_recall_sum = []
	num_classifications = len(re.findall(r'(\t)', xml_lines[0])) # Buscamos el número de clases que contiene la matriz de confusión, separadas todas ellas por un tabulador (\t)
	search_regex = '(.*):'
	search_regex = search_regex + ('\t(.*)' * ( num_classifications)) # Con el numero de clases obtenido construimos una expresión regular de búsqueda, que encuentra cualquier valor separado por un tabulador (\t)
	for i in range(len(xml_lines)):
		column_values = re.findall(r''+search_regex+'', xml_lines[i])
		# La primera línea contiene el nombre de las clases, y por tanto, las claves del dict. Creamos estas claves e inicializamos cada valor como una lista vacía
		if len(column_values) > 0 and len(column_titles) == 0: 
			column_titles.extend(list(column_values[0]))
			for column_title in column_titles:
				data_dict[column_title] = []
				class_recall_sum.append(0)
			data_dict['class_precision'] = []
		# Tras la primera línea, añadimos cada valor en la lista valor de cada clave correspondiente del dict
		elif len(column_values) > 0:
			column_values = list(column_values[0])
			sum_pred = 0
			for j in range(len(column_values)):
				if j > 0:
					data_dict[column_titles[j]].append(column_values[j])
					sum_pred += float(column_values[j])
					class_recall_sum[j] = class_recall_sum[j] + float(column_values[j])
				else:
					data_dict[column_titles[j]].append('pred.'+column_values[j])
			try: 
				# Despues de añadir todos los valores a la lista computamos el valor de precisión con la suma que hemos ido haciendo
				data_dict['class_precision'].append(str(round(((float(data_dict[column_titles[i]][i-1])/sum_pred) * 100),2))+'%')
			except ZeroDivisionError:
				data_dict['class_precision'].append(str(0)+'%')

	# Finalmente, computamos el valor de exahustividad (recall), sumando todos los valores de la columna y dividiendo ese valor por el que coindice con el nombre de la columna
	class_recall_sum[0] = 'class recall'
	for i in range(len(class_recall_sum)):
		if i > 0:
			try:
				data_dict[column_titles[i]].append(str(round(((float(data_dict[column_titles[i]][i-1])/class_recall_sum[i])*100),2))+'%')
			except ZeroDivisionError:
				data_dict[column_titles[i]].append(str(0)+'%')
		else:
			data_dict[column_titles[i]].append(class_recall_sum[i])

	data_dict['class_precision'].append('')
	return data_dict

def create_correct_quantity_data(result_set, model_value, possible_values):
	"""Obtiene los datos para la gráfica de aciertos desde el contenido del fichero XML
	
	Parameters:
		result_set (Element): Resultados del fichero XML <example-set>
		model_value (string): Nombre de la variable modelizada
		possible_values (list): Lista de posible valores a predecir
	Returns:
		list: Lista de las posibles variables que ha predicho el modelo
		dict: Diccionario con el nombre de la variable predicha como clave y una lista del número de predicciones correctas como valor
	"""
	prediction_values = []
	corrects_dict = dict()
	prediction = ''
	real_value = ''

	data_dict = dict()

	# Recorremos los resultados y obtenemos los valores correctos y predicciones. Si la predicción del modelo es correcta sumar se suma uno al valor del diccionario correspondiente a la predicción
	for result in result_set:
		if result.find(model_value) is not None:
			real_value = result.find(model_value).text
		if result.find('prediction-'+model_value+'-') is not None:
			if result.find('prediction-'+model_value+'-').text not in corrects_dict:
				corrects_dict[result.find('prediction-'+model_value+'-').text] = dict()
			prediction = result.find('prediction-'+model_value+'-').text

		if prediction not in prediction_values:
			prediction_values.append(prediction)

		if real_value not in corrects_dict[prediction]:
			corrects_dict[prediction][real_value] = 1
		else:
			corrects_dict[prediction][real_value] += 1

	# En ocasiones puede ocurrir que sobre una predicción no se dan todos los valores posibles, en esa ocasión se debe insertar el valor 0 en la lista
	for prediction_dict_key, prediction_dict_values in corrects_dict.items():
		for possible in possible_values:
			if possible not in prediction_dict_values:
				corrects_dict[prediction_dict_key][possible] = 0

	# Cambiamos la estructura inicial del diccionario por la estructura necesaria para la visualización
	for prediction in corrects_dict.values():
		for real in prediction:
			if real not in data_dict:
				data_dict[real] = []
			data_dict[real].append(prediction[real])


	return prediction_values, data_dict

def create_decision_tree_data(xml_text):
	"""Obtiene los datos para la gráfica del árbol de decisión desde el contenido del fichero XML
	
	Parameters:
		xml_text (string): El contenido XML para parsear
	Returns:
		Tree: Un objeto Tree con la lista de nodos que contiene, ordenada correctamente con respecto al padre e hijos de cada nodo
	"""
	xml_tree_leafs = xml_text.splitlines()
	tree_node_list = []
	color_palette = {'cluster_0': bokeh_utils.BAR_COLORS_PALETTE[0], 'cluster_1': bokeh_utils.BAR_COLORS_PALETTE[1], 'cluster_2': bokeh_utils.BAR_COLORS_PALETTE[2], 'cluster_3': bokeh_utils.BAR_COLORS_PALETTE[3], 
	'range1': bokeh_utils.BAR_COLORS_PALETTE[0], 'range2': bokeh_utils.BAR_COLORS_PALETTE[1], 'range3': bokeh_utils.BAR_COLORS_PALETTE[2], 'range4': bokeh_utils.BAR_COLORS_PALETTE[3], 'range5': bokeh_utils.BAR_COLORS_PALETTE[4]}
	# Eliminamos la primera línea del contenido del fichero XML porque está vacía
	if len(xml_tree_leafs) > 1:
		xml_tree_leafs.pop(0)
	tree = Tree()
	new_leaf = True
	# Recorremos todas las líneas del XML, representando cada línea una rama del árbol
	for i in range(len(xml_tree_leafs)):
		# Obtenemos el nivel de profundidad del nodo, representado por el número de carácteres | en la línea
		levels = re.findall(r'(\|)', xml_tree_leafs[i])
		levels_count = len(levels)
		final_node = re.findall(r'(\:)', xml_tree_leafs[i]) # Comprobamos si en la línea existe un nodo final, buscando para ello, el carácter :
		cluster_range_name = None
		cluster_range_dist = None
		# Obtenemos el texto de la condición que sigue al siguiente nodo. Únicamente si el árbol se compone de más de una rama
		if len(xml_tree_leafs) > 1:
			node_link_text = re.findall(r'([><≤]\s\d*[.\d]*)', xml_tree_leafs[i])[0]
		color = '#c2e8e0'
		# Si tenemos un nodo final en la línea, obtenemos sus datos (nombre y en caso de ser un rango, los valores del rango). Es indispensable tener en cuenta que en la 
		# línea vamos a tener también el nodo anterior al nodo final.
		if len(final_node) > 0:
			if levels_count > 0:
				node_name = re.findall(r'\|\s*([a-zA-Z]*_[a-zA-Z0-9\_]*)\s', xml_tree_leafs[i])[0] # Nombre nodo anterior al final
			else:
				node_name = re.findall(r'([a-zA-Z]*_[a-zA-Z0-9\_]*)\s', xml_tree_leafs[i])[0] # Nombre nodo anterior al final, pero en caso de ser un árbol sin profundidad
			cluster_range_name = re.findall(r':\s([a-z]*_?[0-9])', xml_tree_leafs[i])[0] # Nombre del cluster final
			range_name_range = re.findall(r':\s([a-z]*_?[0-9])(\s\[.*])\s{', xml_tree_leafs[i]) # Nombre del rango y valores del rango
			cluster_range_dist = re.findall(r'({.*})', xml_tree_leafs[i])[0] # Distribución de los valores sobre los clusteres o los rangos
		# Obtenemos nodos intermedios del árbol
		elif final_node is None:
			node_name = re.findall(r'\|\s*([a-zA-Z]*_[a-zA-Z0-9\_]*)\s', xml_tree_leafs[i])[0]
		# Obtenemos nodo raíz
		else:
			node_name = re.findall(r'([a-zA-Z]*_[a-zA-Z0-9\_]*)\s', xml_tree_leafs[i])[0]

		tree_node = Node(i+1, node_name, levels_count, color) # Creamos el objeto nodo con los datos obtenidos
		# print(f"tree_node = Node({i+1}, '{node_name}', {levels_count}, '{color}')")
		# print(f"tree.order_nodes(tree_node, '{node_link_text}')")
		tree.order_nodes(tree_node, node_link_text) # Ordenamos la lista de nodos del árbol e insertamos el nuevo nodo
		
		# En caso de tener un nodo final debemos asignar nuevos parámetros como el color del nodo. Y en caso de tratarse de un nodo final con rango, debemos de concatenar el nombre con el valor de rango
		if cluster_range_name is not None and cluster_range_dist is not None:
			color = color_palette[cluster_range_name]
			if len(range_name_range) > 0:
				cluster_range_name = cluster_range_name + '\n' + list(range_name_range[0])[1]
			cluster_range_node = Node(i+len(xml_tree_leafs), cluster_range_name, levels_count+1, color) # En caso de nodo final, asignamos un ID aleatorio superior a los anteriores para evitar repeticiones
			# print(f"tree_node = Node({i+len(xml_tree_leafs)}, '{cluster_range_name}', {levels_count+1}, '{color}')")
			tree.order_nodes(cluster_range_node, node_link_text) # Ordenamos la lista de nodos del árbol e insertamos el nuevo nodo
			# print(f"tree.order_nodes(tree_node, '{node_link_text}')")

	return tree