from flask import Flask, render_template, session, redirect, url_for, request, flash

import logging

from bokeh_edar40.server import *

from bokeh.embed import server_document

from threading import Thread

import pam
from subprocess import Popen

app = Flask(__name__)

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


user_principal_mapping = {'ibermatica': 'bokeh-epele', 'mikelamuchastegui': 'bokeh-cartuja'}

def do_kerberos_kinit(username):
	kinit = '/usr/bin/kinit'
	kinitopt = '-kt'
	keytab = '/Users/mikelamuchastegui/' +str(username)+'.keytab'
	#keytab = '/etc/security/keytabs/'+str(username)+'.keytab'
	principal = str(username)
	realm = 'EDAR40.EUS'
	kinit_args = [ kinit, kinitopt, keytab, principal ]
	kinit = Popen(kinit_args)

def do_kerberos_kdestroy():
	kdestroy = '/usr/bin/kdestroy'
	kdestroy_args = [ kdestroy ]
	kdestroy = Popen(kdestroy_args)

Thread(target=bk_worker).start()

@app.route('/cartuja/prediccion', methods=['GET'])
def cartuja_prediction():
	script = server_document('http://localhost:9090/cartuja/prediccion')
	return render_template('cartuja.html', script=script)

@app.route('/epele', methods=['GET'])
def epele():
	script = server_document('http://localhost:9090/epele')
	return render_template('epele.html', script=script)

@app.route('/cartuja', methods=['GET'])
def cartuja():
	script = server_document('http://localhost:9090/cartuja')
	return render_template('cartuja.html', script=script)

@app.route('/', methods=['GET'])
def index():
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'mikelamuchastegui':
			return redirect(url_for('cartuja'))
		else:
			return redirect(url_for('epele'))
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		p = pam.pam()
		username = request.form['username']
		password = request.form['password']

		if p.authenticate(str(username), str(password)) and user_principal_mapping[str(username)] is not None:
			session['username'] = request.form['username']
			do_kerberos_kinit(user_principal_mapping[str(username)])
			return redirect(url_for('index'))
		else:
			flash('Login incorrecto, inténtalo otra vez')

	return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('username', None)
	do_kerberos_kdestroy()
	return redirect(url_for('index'))

if __name__ == '__main__':
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	app.run(port=9995, debug=True, host='localhost')




