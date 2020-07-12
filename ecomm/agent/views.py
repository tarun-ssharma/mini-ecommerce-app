from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm.agent import Agent
from ecomm import db


agent_bp = Blueprint('agent',__name__)

def is_logged_in():
	return 'username' in session

def is_agent():
	return ('role' in session) and (session['role'] == 'AGENT')

@agent_bp.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		if(request.form['pwd'] != 'agent'):
			flash('Incorrect credentials. Please try to login again.')
			return render_template('admin_login.html', url= url_for('agent.login'))
		else:
			session['username'] = request.form['user']
			session['role'] = 'AGENT'
			flash('Logged in successfully!')
			return redirect(url_for('agent.home'))
	else:
		return render_template('admin_login.html', url= url_for('agent.login'))

@agent_bp.route('/')
@agent_bp.route('/home')
def home():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('agent.login'))
	else:
		#Logged in agent
		return render_template('agent_home.html')

@agent_bp.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('role', None)
	flash('Logged out successfully!')
	return redirect(url_for('agent.login'))