from flask import Flask, render_template, session, redirect, url_for, request, flash

import logging

from bokeh_edar40.server import *

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

#Usamos este diccionario para mapear los usuarios diponibles a los principales de kerberos. Tenemos dos principales, uno para cada caso de uso
#si accedemos al caso de uso de EDAR Epele, accedemos mediante el principal bokeh-epele y si accedemos al caso de uso EDAR La Cartuja accedemos con el principal
#bokeh-cartuja. En el caso de uso de La Cartuja no sería necesario ingresar mediante Kerberos, ya que, el propio software RapidMiner ya está configurado con esta opción 
#y por lo tanto realiza la autenticación mediante Kerberos cuando es necesario.
# user_principal_mapping = {'ibermatica': 'bokeh-epele', 'rapidminer': 'bokeh-cartuja'}

# def do_kerberos_kinit(username):
# 	kinit = '/usr/bin/kinit'
# 	kinitopt = '-kt'
# 	#Para pruebas en local
# 	#keytab = '/Users/mikelamuchastegui/' +str(username)+'.keytab'
# 	keytab = '/etc/security/keytabs/'+str(username)+'.keytab'
# 	principal = str(username)
# 	realm = 'EDAR40.EUS'
# 	kinit_args = [ kinit, kinitopt, keytab, principal ]
# 	kinit = Popen(kinit_args)

# def do_kerberos_kdestroy():
# 	kdestroy = '/usr/bin/kdestroy'
# 	kdestroy_args = [ kdestroy ]
# 	kdestroy = Popen(kdestroy_args)

Thread(target=bk_worker).start()

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/cartuja/prediccion', methods=['GET'])
def cartuja_prediction():
	# script = server_document('http://localhost:9090/cartuja/prediccion')
	script = server_document('http://10.0.20.30:9090/cartuja/prediccion')
	return render_template('cartuja.html', script=script)

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/cartuja', methods=['GET'])
def cartuja():
	# script = server_document('http://localhost:9090/cartuja')
	script = server_document('http://10.0.20.30:9090/cartuja')	
	return render_template('cartuja.html', script=script)

@app.route('/', methods=['GET'])
def index():
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			return redirect(url_for('cartuja'))
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# p = pam.pam()
		username = request.form['username']
		password = request.form['password']

		# if p.authenticate(str(username), str(password)) and user_principal_mapping[str(username)] is not None:
		if str(username) == 'rapidminer' and str(password) == 'rapidminer':
			session['username'] = request.form['username']
			# do_kerberos_kinit(user_principal_mapping[str(username)])
			return redirect(url_for('index'))
		else:
			flash('Login incorrecto, inténtalo otra vez')

	return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('username', None)
	# do_kerberos_kdestroy()
	return redirect(url_for('index'))

#Configuración cuando ejecutamos unicamente Flask sin Gunicorn, en modo de prueba
if __name__ == '__main__':
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	app.run(port=9995, debug=False, host='0.0.0.0')
