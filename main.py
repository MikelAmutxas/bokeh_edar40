from flask import Flask, render_template, session, redirect, url_for, request, flash

import logging

from bokeh_edar40.server import bk_worker

from bokeh.embed import server_document

from threading import Thread

# import pam
from subprocess import Popen

app = Flask(__name__)

#Configuración de secret key y logging cuando ejecutamos sobre Gunicorn

if __name__ != '__main__':
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	gunicorn_logger = logging.getLogger('gunicorn.error')
	gunicorn_logger.setLevel(logging.INFO)
	
	tornado_access_logger = logging.getLogger('tornado.access')
	tornado_access_logger.setLevel(logging.INFO)
	tornado_access_handler = logging.FileHandler('logs/error_log.log')
	tornado_access_logger.addHandler(tornado_access_handler)

	tornado_application_logger = logging.getLogger('tornado.application')
	tornado_application_logger.setLevel(logging.INFO)
	tornado_application_handler = logging.FileHandler('logs/error_log.log')
	tornado_application_logger.addHandler(tornado_application_handler)

	app.logger.addHandler(gunicorn_logger.handlers)
	app.logger.addHandler(tornado_access_logger.handlers)
	app.logger.addHandler(tornado_application_logger.handlers)
	app.logger.setLevel(logging.INFO)

Thread(target=bk_worker).start()

@app.route('/', methods=['GET'])
def index():
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			return redirect(url_for('perfil'))
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	active_page = 'login'
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		if str(username) == def_user and str(password) == def_pass:
			session['username'] = request.form['username']
			return redirect(url_for('index'))
		else:
			flash('Login incorrecto, inténtalo otra vez')
	return render_template('login.html', active_page=active_page)

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('username', None)
	# do_kerberos_kdestroy()
	return redirect(url_for('index'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/perfil', methods=['GET'])
@app.route('/perfil/periodo1', methods=['GET'])
def perfil():
	active_page = 'perfil'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja')
			# script = server_document('http://3.10.15.221:9090/cartuja')
			script = server_document('http://10.0.20.30:9090/perfil', arguments={'periodo':1})
			# script = server_document(url=r'/cartuja', relative_urls=True)
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/perfil', arguments={'periodo':1})
			title = 'Calidad del Agua - Periodo 1'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

@app.route('/perfil/periodo2', methods=['GET'])
def perfil_p2():
	active_page = 'perfil'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja')
			script = server_document('http://10.0.20.30:9090/perfil', arguments={'periodo':2})
			# script = server_document(url=r'/cartuja', relative_urls=True)
			# script = server_document('http://3.10.15.221:9090/cartuja')
			# script = server_document(url=r'/cartuja', relative_urls=True)	
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/perfil', arguments={'periodo':2})
			title = 'Calidad del Agua - Periodo 2'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

@app.route('/perfil/comparativo', methods=['GET'])
def perfil_comp():
	active_page = 'perfil'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja')
			script = server_document('http://10.0.20.30:9090/perfil')
			# script = server_document(url=r'/cartuja', relative_urls=True)
			# script = server_document('http://3.10.15.221:9090/cartuja')
			# script = server_document(url=r'/cartuja', relative_urls=True)
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/perfil')
			title = 'Calidad del Agua - Comparativo Periodos'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/prediccion', methods=['GET'])
@app.route('/prediccion/periodo1', methods=['GET'])
def cartuja_prediction():
	active_page = 'prediccion'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja/prediccion')
			script = server_document('http://10.0.20.30:9090/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://3.10.15.221:9090/cartuja/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/prediccion')
			title = 'Predicción de Calidad del Agua - Periodo 1'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/prediccion/periodo2', methods=['GET'])
def cartuja_prediction_p2():
	active_page = 'prediccion'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja/prediccion')
			script = server_document('http://10.0.20.30:9090/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://3.10.15.221:9090/cartuja/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/prediccion')				
			title = 'Predicción de Calidad del Agua - Periodo 2'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/prediccion/comparativo', methods=['GET'])
def cartuja_prediction_comp():
	active_page = 'prediccion'
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			# script = server_document('http://192.168.10.130:9090/cartuja/prediccion')
			script = server_document('http://10.0.20.30:9090/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://3.10.15.221:9090/cartuja/prediccion')
			# script = server_document(url=r'/cartuja/prediccion', relative_urls=True)
			# script = server_document('http://bokeh.edar.vicomtech.org/cartuja/prediccion')								
			title = 'Predicción de Calidad del Agua - Comparativo Periodos'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title)
	return redirect(url_for('login'))

#Configuración cuando ejecutamos unicamente Flask sin Gunicorn, en modo de prueba
if __name__ == '__main__':
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	def_user = 'rapidminer'
	def_pass = 'rapidminer'
	active_page = 'perfil'
	app.run(port=9995, debug=False, host='0.0.0.0')
