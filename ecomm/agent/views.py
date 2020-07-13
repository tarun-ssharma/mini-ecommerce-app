from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm.agent import Agent
from ecomm import db
from ecomm.customer import Customer,FinancialLedgerEntry
from ecomm.invoice import Invoice
from datetime import datetime

#Initialize the agent blueprint.
agent_bp = Blueprint('agent',__name__)

def is_logged_in():
	return 'user_id' in session

def is_agent():
	return ('role' in session) and (session['role'] == 'AGENT')

@agent_bp.route('/login',methods=['GET','POST'])
def login():
	'''
	Handles the agent login functionality.
	'''
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
	'''
	Renders the agent home page.
	'''
	if (not is_logged_in()) or (not is_agent()):
		return redirect(url_for('agent.login'))
	else:
		#Logged in agent
		return render_template('agent_home.html')

@agent_bp.route('/logout')
def logout():
	'''
	Handles the agent logout functionality.
	'''
	session.pop('user_id', None)
	session.pop('role', None)
	flash('Logged out successfully!')
	return redirect(url_for('agent.login'))

@agent_bp.route('/customerDetails',methods=['POST'])
def display_customer_details():
	'''
	Processes and displays orders and financial transactions related to a customer.
	'''
	if not(is_logged_in() and is_agent()):
		flash('You have to log in as an agent to perform this function!')
		return redirect(url_for('agent.login'))
	else:
		customer_id = request.form['customer_id']
		#Need to convert the string time recieved from front-end to a datetime object
		#So that we can compare with time columns
		starting_date_time = datetime.strptime(request.form['starting_date'], "%Y-%m-%dT%H:%M")
		ending_date_time = datetime.strptime(request.form['ending_date'], "%Y-%m-%dT%H:%M")
		if(request.form['function'] == "Display Orders"):
			#If 'Display Orders' functionality was invoked
			orders = Invoice.query.filter_by(customer_id=customer_id).filter(Invoice.time >= starting_date_time).\
				filter(Invoice.time <= ending_date_time).all()
			return render_template('agent_display_orders.html',orders=orders)
		elif(request.form['function'] == "Display financial transactions"):
			#If 'Display financial transactions' functionality was invoked
			customer = Customer.query.filter_by(id=customer_id).first_or_404(description='Customer does not exist!')
			ledgerEntries = customer.ledgerEntries.filter(FinancialLedgerEntry.transaction_date >= starting_date_time).\
				filter(FinancialLedgerEntry.transaction_date <= ending_date_time).all()
			return render_template('agent_display_transactions.html',ledgerEntries=ledgerEntries)

@agent_bp.route('/updateOrder',methods=['POST'])
def update_order():
	'''
	Handles operations on orders like recording payment, marking an order delivered and cancelling an accepted order.
	'''
	if not(is_logged_in() and is_agent()):
		flash('You have to log in as an agent to perform this function!')
		return redirect(url_for('agent.login'))
	else:
		order_id = request.form['order_id']
		order = Invoice.query.get_or_404(order_id, description='Order does not exist!')
		if(request.form['function'] == "Record Payment"):
			if(order.is_paid == True):
				flash('Order is already paid for!')
				return redirect(url_for('agent.home'))
			customer = Customer.query.get_or_404(order.customer_id)
			#Query the latest financial transaction to fetch the current balance.
			latest_entry = customer.ledgerEntries.order_by(FinancialLedgerEntry.transaction_date.desc()).first()
			
			#Assuming balance of the customer decreases after paying for the order.
			if latest_entry is None:
				balance = 0 - order.total
			else:
				balance = latest_entry.balance - order.total
			try:
				#Update order and ledger entry to reflect the payment.
				order.is_paid = True
				order.agent_id = session['user_id']
				ledgerEntry = FinancialLedgerEntry(datetime.now(),-1*order.total,balance)
				customer.ledgerEntries.append(ledgerEntry)
				db.session.add(ledgerEntry)
				db.session.commit()
				flash('Successfully recorded payment!')
			except Exception as e:
				db.session.rollback()
				flash(str(e))
			return redirect(url_for('agent.home'))

		elif(request.form['function'] == "Mark Delivered"):
			try:
				order.status = "DELIVERED"
				order.agent_id = session['user_id']
				db.session.commit()
				flash('State successfully updated!')
			except Exception as e:
				flash(str(e))
				db.session.rollback()
			return redirect(url_for('agent.home'))

		elif(request.form['function'] == "Cancel Order"):
			if(order.status == "DELIVERED"):
				flash('Order has been delivered and can\'t be cancelled now.')
				return redirect(url_for('agent.home'))
			elif(order.status == "CANCELLED"):
				flash('Order has already been cancelled.')
				return redirect(url_for('agent.home'))
			elif(order.status == "ACCEPTED"):
				customer = Customer.query.get_or_404(order.customer_id, description="Customer does not exist!")
				#Query the latest financial transaction to fetch the current balance.
				latest_entry = customer.ledgerEntries.order_by(FinancialLedgerEntry.transaction_date.desc()).first()
				if latest_entry is None:
					balance = 0 + order.total
				else:
					balance = latest_entry.balance + order.total
				try:
					#Update order and ledger entry to reflect order cancellation.
					order.status = "CANCELLED"
					order.agent_id = session['user_id']
					ledgerEntry = FinancialLedgerEntry(datetime.now(), order.total, balance)
					customer.ledgerEntries.append(ledgerEntry)
					db.session.add(ledgerEntry)
					db.session.commit()
					flash('Order cancelled successfully!')
				except Exception as e:
					flash(str(e))
					db.session.rollback()
				return redirect(url_for('agent.home'))
