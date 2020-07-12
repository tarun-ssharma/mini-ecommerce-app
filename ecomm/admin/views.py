from ecomm.admin import User, Admin, Role, RoleValues
from ecomm.agent import Agent
from ecomm.customer import Customer
from ecomm.products.models import Product
from ecomm.products.views import get_all_products
from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm import db

admin_bp = Blueprint('admin',__name__)

def is_logged_in():
	return 'username' in session

def is_admin():
	return ('role' in session) and (session['role'] == 'ADMIN')

@admin_bp.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		if(request.form['pwd'] != 'admin'):
			#TODO: query db 
			flash('Incorrect credentials. Please try to login again.')
			return render_template('admin_login.html', url= url_for('admin.login'))
		else:
			session['username'] = request.form['user']
			session['role'] = 'ADMIN'
			flash('Logged in successfully!')
			return redirect(url_for('admin.home'))
	else:
		return render_template('admin_login.html', url= url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/home')
def home():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		#Logged in admin
		return render_template('admin_home.html',products=get_all_products())

@admin_bp.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('role', None)
	flash('Logged out successfully!')
	return redirect(url_for('admin.login'))

@admin_bp.route('/addAgent',methods=['GET','POST'])
def add_agent():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			password = request.form['pwd']
			username = request.form['user']
			#make sure this is None when no field sent
			email = request.form['email']
			first_name = request.form['firstName']
			last_name = request.form['lastName']

			#First, validate the field values
			if(not username or not password):
				#basic empty field validation
				flash('Incomplete credentials. Please try again.')
				#use AJAX
				render_template('admin_add_customer.html')
			else:
				agent = Agent.query.filter_by(username=username).first()
				if agent is None:
					try:
						agent = Agent(username, password, first_name, last_name,email)
						role = Role(RoleValues.AGENT)
						agent.roles.append(role)
						db.session.add(agent)
						db.session.commit()
						flash('Agent created successfully!')
					except Exception as e:
						flash(str(e))
						db.session.rollback()

					return redirect(url_for('admin.home'))
				else:
					flash('An agent with the same username already exists.')
					#use AJAX
					render_template('admin_add_customer.html')
		else:
			return render_template('admin_add_agent.html')


@admin_bp.route('/addCustomer',methods=['GET','POST'])
def add_customer():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			password = request.form['pwd']
			username = request.form['user']
			#make sure this is None when no field sent
			email = request.form['email']
			first_name = request.form['firstName']
			last_name = request.form['lastName']
			phone  = request.form['phone']

			#First, validate the field values
			if(not username or not password or not phone):
				#basic empty field validation
				flash('Incomplete credentials. Please try again.')
				#use AJAX
				return render_template('admin_add_customer.html')
			else:
				customer = Customer.query.filter_by(username=username).first()
				if customer is None:
					try:
						customer = Customer(username, password, first_name, last_name, phone, email)
						role = Role(RoleValues.CUSTOMER)
						customer.roles.append(role)
						db.session.add(customer)
						db.session.commit()
						flash('Customer created successfully!')
					except Exception as e:
						flash(str(e))
						db.session.rollback()

					return redirect(url_for('admin.home'))
				else:
					flash('A customer with the same username/phone already exists.')
					#use AJAX
					return render_template('admin_add_customer.html')
		else:
			return render_template('admin_add_customer.html')