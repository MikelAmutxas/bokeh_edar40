from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from bokeh_edar40.applications.cartuja.first_descriptive import modify_first_descriptive
from bokeh_edar40.applications.cartuja.second_descriptive import modify_second_descriptive

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
def bk_worker():
	server = Server({'/cartuja': modify_first_descriptive, '/cartuja/prediccion': modify_second_descriptive}, io_loop=IOLoop(), allow_websocket_origin=['localhost:9995','10.0.20.30:9995', '192.168.10.130:9995'], port=9090)
	server.start()
	server.io_loop.start()