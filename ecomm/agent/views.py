from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm.agent import Agent
from ecomm import db
from ecomm.customer import Customer,FinancialLedgerEntry
from ecomm.invoice import Invoice
from datetime import datetime


agent_bp = Blueprint('agent',__name__)

def is_logged_in():
	return 'user_id' in session

def is_agent():
	return ('role' in session) and (session['role'] == 'AGENT')

@agent_bp.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		if(not request.form['pwd'] or not request.form['user'] or \
		 (Agent.query.filter_by(username=request.form['user']).first() is None) or \
		  request.form['pwd'] != Agent.query.filter_by(username=request.form['user']).first().password):
			flash('Incorrect credentials. Please try to login again.')
			return render_template('admin_login.html', url= url_for('agent.login'))
		else:
			session['user_id'] = Agent.query.filter_by(username=request.form['user']).first().id
			session['role'] = 'AGENT'
			flash('Logged in successfully!')
			return redirect(url_for('agent.home'))
	else:
		return render_template('admin_login.html', url= url_for('agent.login'))

@agent_bp.route('/')
@agent_bp.route('/home')
def home():
	if (not is_logged_in()) or (not is_agent()):
		return redirect(url_for('agent.login'))
	else:
		#Logged in agent
		return render_template('agent_home.html')

@agent_bp.route('/logout')
def logout():
	session.pop('user_id', None)
	session.pop('role', None)
	flash('Logged out successfully!')
	return redirect(url_for('agent.login'))

@agent_bp.route('/customerDetails',methods=['POST'])
def display_customer_details():
	if not(is_logged_in() and is_agent()):
		flash('You have to log in as an agent to perform this function!')
		return redirect(url_for('agent.login'))
	else:
		customer_id = request.form['customer_id']
		if(request.form['function'] == "Display Orders"):
			orders = Invoice.query.filter_by(customer_id=customer_id).all()
			return render_template('agent_display_orders.html',orders=orders)
		elif(request.form['function'] == "Display financial transactions"):
			customer = Customer.query.filter_by(id=customer_id).first_or_404(description='Customer does not exist!')
			ledgerEntries = customer.ledgerEntries.all()
			return render_template('agent_display_transactions.html',ledgerEntries=ledgerEntries)

@agent_bp.route('/recordOrderPayment',methods=['POST'])
def record_order_payment():
	if not(is_logged_in() and is_agent()):
		flash('You have to log in as an agent to perform this function!')
		return redirect(url_for('agent.login'))
	else:
		order_id = request.form['order_id']
		order = Invoice.query.get_or_404(order_id, description='Order does not exist!')
		customer = Customer.query.get_or_404(order.customer_id)
		latest_entry = customer.ledgerEntries.order_by(FinancialLedgerEntry.transaction_date.desc()).first()
		
		#Assuming balance of the customer decreases after paying for the order.
		if latest_entry is None:
			balance = 0 - order.total
		else:
			balance = latest_entry.balance - order.total
		try:
			order.is_paid = True
			order.agent_id = session['user_id']
			ledgerEntry = FinancialLedgerEntry(datetime.now(),order.total,balance)
			customer.ledgerEntries.append(ledgerEntry)
			db.session.add(ledgerEntry)
			db.session.commit()
			flash('Successfully recorded payment!')
		except Exception as e:
			db.session.rollback()
			flash(str(e))
		return redirect(url_for('agent.home'))