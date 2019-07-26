from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from bokeh_edar40.applications.epele.epele import modify_epele_doc
from bokeh_edar40.applications.cartuja.first_descriptive import modify_first_descriptive
from bokeh_edar40.applications.cartuja.second_descriptive import modify_second_descriptive

def bk_worker():
	server = Server({'/epele':modify_epele_doc, '/cartuja': modify_first_descriptive, '/cartuja/prediccion': modify_second_descriptive}, io_loop=IOLoop(), allow_websocket_origin=['localhost:9995'], port=9090)
	server.start()
	server.io_loop.start()