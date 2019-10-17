import re
import math

class Tree:
	"""Clase Tree para representar la estructura del árbol de decisión
	
	Esta clase es utilizada para representar el árbol de decisión con una lista de nodo ordenados según los hijos y el padre de cada nodo
	
	Attributes:
		node_list: Lista de nodos
	"""

	NODE_WIDTH = 0.2
	NODE_HEIGHT = 0.15

	def __init__(self):
		self.node_list = []


	def add_node(self, node):
		"""Añade nodo a la lista y en caso de estar vacía se incializa

		Attributes:
			node (Node): Nodo para añadir a la lista
		"""
		if self.node_list == 0:
			self.node_list = []

		self.node_list.append(node)

	def get_nodes_by_level(self):
		"""Obtiene el número de nodos en cada nivel de profundidad del árbol en forma de diccionario

		Returns:
			dict: Número de nodos en cada nivel de profundidad
		"""
		levels = [node.level for node in self.node_list]
		nodes_in_levels = {level: levels.count(level) for level in levels}
		for nodes_in_levels_key, nodes_in_levels_value in nodes_in_levels.items():
			if nodes_in_levels_key-1 in nodes_in_levels and nodes_in_levels_value < nodes_in_levels[nodes_in_levels_key-1]*2:
				nodes_in_levels[nodes_in_levels_key] = nodes_in_levels[nodes_in_levels_key-1]*2
		return nodes_in_levels

	def get_nodes_relations(self):
		"""Recoorre la lista de nodos y obtiene la relación de cada nodo

		Returns:
			list: Lista de nodos de inicio
			list: Lista de nodos finales
		"""
		start = []
		end = []
		for node in self.node_list:
			start, end = node.get_start_and_end(start, end)

		return start, end

	def get_node_text_positions(self):
		"""Recorre la lista de nodos y obtiene la posición para mostrar el texto del nombre de cada nodo

		Returns:
			list: Coordenadas X de posición
			list: Coordenadas Y de posición
			list: Texto para mostrar como nombre en cada nodo
		"""
		x = []
		y = []
		text = []
		for node in self.node_list:	
			x.append(node.x) 
			y.append(node.y-(self.NODE_HEIGHT/2)+0.04)
			text.append(node.name)
		return x, y, text
			

	def get_layout_node_positions(self, tree_plot):
		"""Recorre la lista de nodos para obtener la posición de cada nodo en el plano 
		El tamaño del plano depende del tamaño de la figura Bokeh creada para mostrar el árbol

		Attributes:
			tree_plot (Figure): Figura Bokeh donde se dibuja el árbol de decisión

		Returns:
			list: Coordenadas X de los nodos
			list: Coordenada Y de los nodos
		"""
		nodes_in_levels = self.get_nodes_by_level()
		num_levels = len(nodes_in_levels.keys())
		x_range = tree_plot.x_range.end - tree_plot.x_range.start - (0.1*2)
		x = []
		y = []
		for node in self.node_list:
			node.get_layout_position(nodes_in_levels, num_levels, x_range)
			x.append(node.x)
			y.append(node.y)
		return x, y

	def get_line_text_positions(self):
		""" Recorre la lista de nodos para obtener la posición del texto y el texto de condición a dibujar sobre las relaciones entre los nodos 

		Returns:
			list: Coordenadas X de posición
			list: Coordenadas Y de posición
			list: Textos de condición a dibujar
		"""
		middle_x = []
		middle_y =  []
		middle_text = []
		for node in self.node_list:
			if node.childrens is not None:
				for i in range(len(node.childrens)):
					x = (node.childrens[i].x + node.x)/2
					y = (node.childrens[i].y + node.y)/2 - 0.02
					middle_x.append(x)
					middle_y.append(y)
					middle_text.append(node.link_text[i])

		return middle_x, middle_y, middle_text

	def order_nodes(self, tree_node, node_link_text):
		"""Ordena la lista de nodos. Para ello, recorre los nodos, busca el primer nodo de un nivel superior al nuevo nodo a insertar y cabia los parámetros childrens y parent de ambos nodos.
		Como el árbol en el fichero XML se obtiene de forma ordenada esto es correcto.

		"""
		add = True
		for node in reversed(self.node_list):
			# Si la lista ya contiene un nodo de mismo nombre y nivel de profundidad, puede que el nodo esté repetido
			if node.level == tree_node.level and node.name == tree_node.name:
				# Si el nodo padre tiene asignadas más condiciones de relación que número de hijos, el nodo no está repetido. Existe un nodo de mismo nombre y nivel de profundidad que debemos añadir a la lista
				if node.parent is not None and (len(node.parent.link_text) > len(node.parent.childrens)):
						add = True
						tree_node.parent = node.parent
						node.parent.add_children(tree_node)
						break
				tree_node.id = node.id
				node.add_link_text(node_link_text)
				add = False
	
			if node.level < tree_node.level:
				if add:
					tree_node.parent = node
					node.add_children(tree_node)
					break
		if add:
			tree_node.add_link_text(node_link_text)
			self.node_list.append(tree_node)

class Node:

	"""Clase Node para representar un nodo en el árbol de decisión
	
	Attributes:
		id (int): Id del nodo
		name (string): Nombre del nodo
		level (int): Nivel de profundida del nodo en el árbol
		color (string): Color con cual pintar el nodo en la figura
		link_text (string): Relaciones de condición del nodo para los nodos hijos
		childrens (list): Lista de nodos hijos del nodo
		parent (Node): Nodo padre
		x (float): Valor de posición coordenada X en el plano
		y (float): Valor de posición coordenada Y en el plano
	"""

	def __init__(self, id, name, level, color, link_text=None, childrens=None, parent=None, x=None, y=None):
		self.id = id
		self.name = name
		self.level = level
		self.color = color
		self.link_text = link_text
		self.childrens = childrens
		self.parent = parent
		self.x = x
		self.y = y


	def add_children(self, children):
		"""Añade un nodo hijo

		Attributes:
			children (Node): Nodo hijo
		"""
		if self.childrens == None:
			self.childrens = []
		self.childrens.append(children)

	def get_start_and_end(self, start, end):
		"""Obtiene relaciones de cada nodo.

		Attributes:
			start (list): Lista de ID-s del nodo de inicio de cada relación
			end (list): Lista de ID-s del nodo final de cada relación

		Returns:
			list: List of start relations.
			list: List of end relations.
		"""
		if self.childrens is not None:
			for children in self.childrens:
				start.append(self.id)
				end.append(children.id)
		return start, end

	def get_text_position(self):
		"""Obtiene posición del texto de nombre del nodo en el plano

		Returns:
			float: Valor coordenada X en el plano
			float: Valor coordenada Y en el plano
		"""

		x = self.x - 0.02
		y = self.y  - 0.01
		return x, y

	def add_link_text(self, text_link):
		"""Añade una relación de condición al nodo
		"""
		if self.link_text == None:
			self.link_text = []
		self.link_text.append(text_link)

	def get_layout_position(self, nodes_in_levels, num_levels, x_range):
		"""Obtiene posición del nodo en el plano

		Attributes:
			nodes_in_levels (dict): Diccionario conteniendo los niveles de profundidad que tiene el árbol como clave, y el número de nodos en cada nivel como valor
			num_levels (int): El número de niveles de profundidad que tiene el árbol (TODO: Esto puede conseguirse del diccionario anterior, no hace falta pasarlo)
			x_range (float): El rango del plano en el eje X, esto es, la anchura de la figura
		"""
		y_pos = 1 - (self.level/num_levels) # Dividimos el rango en el eje Y del plano por el número de niveles de profundidad del árbol. Así encontramos el valor de coordenada Y de los nodos de cada nivel de profundidad del árbol
		if self.parent is None: # Si se trata del nodo raíz, el valor de la coordenada X es el 0, suponiendo que el valor 0 es el cetro del rango X.
			x_pos = 0
			self.x = x_pos
			self.y = y_pos

		# Para el valor de coordenada X, si el nodo es un nodo intermedio, debemos dividir el espacio disponible en el rango X por el número de nodos a dibujar en ese nivel de profundidad
		# Para el valor de coordenada Y, como en el caso anterior, dividimos el rango en el eje Y del plano por el número de niveles de profundidad del árbol y así encontramos la coordenada Y de los nodos en ese nivel
		if self.childrens is not None: 
			num_childs_in_level = nodes_in_levels[self.childrens[0].level]
			x_gap = (x_range/2) / num_childs_in_level
			y_pos = 1 - (self.childrens[0].level/num_levels)
			for i in range(len(self.childrens)):
				x_pos = self.childrens[i].parent.x + (x_gap*(i+1)) - (x_gap*(len(self.childrens)-i))
				self.childrens[i].x = x_pos
				self.childrens[i].y = y_pos
