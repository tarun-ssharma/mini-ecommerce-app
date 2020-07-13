from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm.invoice import Invoice, CartSkus, OrderSkus
from datetime import datetime
from ecomm.customer.models import Customer
from ecomm.products.views import get_all_products
from ecomm.products import SKU
from ecomm import db
from multiprocessing import Process
import time

customer_bp = Blueprint('customer',__name__)


def send_sms(phone, message):
	'''
	Logic to send a given message SMS to a phone number.
	'''
	time.sleep(2000)
	return True

def generate_otp():
	'''
	Mocking the OTP generation process
	'''
	return 1234

def is_logged_in():
	'''
	Utility method to ascertain if the user is logged in.
	'''
	return 'user_id' in session

def is_customer():
	'''
	Utility method to ascertain if the user is logged in as a customer.
	'''
	return ('role' in session) and (session['role'] == 'CUSTOMER')

@customer_bp.route('/login',methods=['GET','POST'])
def login():
	'''
	Handles the login functionality for customers.
	'''
	if request.method == 'POST':
		#Validations for login page
		if(('login_username' in request.form and request.form['pwd'] != 'customer') or('login_phone' in request.form and not request.form['phone'].isdigit())):
			flash('Incorrect credentials. Please try to login again.')
			return render_template('customer_login.html', url= url_for('customer.login'))
		#Validations for OTP page
		elif('login_otp' in request.form and int(request.form['otp']) != session['generated_otp']):
			flash('Incorrect OTP. Retry.')
			return render_template('enter_otp.html')
		else:
			if('login_phone' in request.form):
				session['phone'] = request.form['phone']
				customer = Customer.query.filter_by(phone=session['phone']).first()
				if customer is None:
					flash('Incorrect credentials. Please try to login again.')
					return render_template('customer_login.html', url= url_for('customer.login'))
				#Mock the OTP generation process
				session['generated_otp'] = generate_otp()
				#Spawn a new process which will take care of sending the OTP to the customer.
				process_send_otp = Process(
				        target=send_sms,
				        args=(session['phone'],'Your OTP for loggin in is'+str(session['generated_otp'])),
				        daemon=True
				    )
				process_send_otp.start()
				return render_template('enter_otp.html',url= url_for('customer.login'))
			elif('login_otp' in request.form):
				customer = Customer.query.filter_by(phone=session['phone']).first()
				session['user_id'] = customer.id
				session.pop('generated_otp',None)
				session.pop('phone',None)
			elif('login_username' in request.form):
				customer = Customer.query.filter_by(username=request.form['user']).first()
				session['user_id'] = customer.id

			session['role'] = 'CUSTOMER'
			flash('Logged in successfully!')
			return redirect(url_for('customer.home'))
	else:
		return render_template('customer_login.html', url= url_for('customer.login'))


@customer_bp.route('/')
@customer_bp.route('/home')
def home():
	'''
	Handles login functionality for customers.
	'''
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		return render_template('customer_home.html',products=get_all_products())


@customer_bp.route('/logout')
def logout():
	'''
	Handles logout functionality for customers.
	'''
	session.pop('user_id', None)
	session.pop('role',None)
	flash('Logged out successfully!')
	return redirect(url_for('customer.login'))

@customer_bp.route('/viewCart')
def show_cart():
	'''
	Renders the incomplete cart for customers. There can only be one per customer.
	'''
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		cart_skus = CartSkus.query.filter_by(customer_id=session['user_id']).all()
		last_prices = {}
		stock_qtys = {}
		prices = {}
		properties = {}
		for cart_sku in cart_skus:
			sku = SKU.query.get_or_404(cart_sku.sku_id)
			properties[sku.id] = sku.properties
			prices[sku.id] = sku.price
			stock_qtys[cart_sku.sku_id] = sku.stock_qty
			#Query to obtain the last ordered prices of current cart items.
			last_invoice = Invoice.query.filter_by(customer_id=session['user_id']).filter(Invoice.order_skus.any(sku_id=cart_sku.sku_id)).order_by(Invoice.time.desc()).first()
			if last_invoice is None:
				last_prices[cart_sku.sku_id] = -1
			else:	
				last_prices[cart_sku.sku_id] = OrderSkus.query.filter_by(order_id=last_invoice.id).first().price

		return render_template('show_cart.html',cart_skus=cart_skus,last_prices=last_prices,stock_qtys=stock_qtys,prices=prices,properties=properties)

@customer_bp.route('/orderHistory')
def show_order_history():
	'''
	Display brief information about previous orders placed by a customer.
	'''
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		invoices = Invoice.query.filter_by(customer_id=session['user_id']).all()
		return render_template('order_history.html',invoices=invoices)

@customer_bp.route('/placeOrder',methods=['POST'])
def place_order():
	'''
	Handle operations involved during placing an order, involving:
	1. Ascertain sufficient stocks
	2. Move cart skus to order skus, remove cart skus, reduce stock levels to account for ordered products.
	3. Create a new Invoice with state='ACCEPTED'
	4. Send 'Order Placed' notification to customer.
	NOTE/ASSUMPTION: Ledger is updated not now, but only once payment is recieved by an agent.
	'''
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		with db.session.no_autoflush:
			try:
				customer_id = session['user_id']
				cart_skus = CartSkus.query.filter_by(customer_id=customer_id).all()
				customer = Customer.query.get_or_404(customer_id)
				#Empty cart scenario
				if cart_skus is None:
					abort(404, description="Cart has no items!")
				total = 0
				order_skus = []
				for cart_sku in cart_skus:
					sku = SKU.query.get_or_404(cart_sku.sku_id)
					sku_stock_qty = sku.stock_qty
					#Abort the place order process if any of the cart items is not in sufficient stock.
					if(cart_sku.quantity > sku_stock_qty):
						raise Exception('Sku'+cart_sku.sku_id+' has insufficient stock')
					subtotal = cart_sku.quantity*(sku.price)
					order_sku = OrderSkus(cart_sku.quantity,sku.price,subtotal)
					if(cart_sku.quantity == sku_stock_qty):
						sku.in_stock = False
					#Reduce stock levels
					sku.stock_qty -= cart_sku.quantity
					sku.order_skus.append(order_sku)
					order_skus.append(order_sku)
					#Calculate order total
					total += subtotal
					db.session.delete(cart_sku)

				invoice = Invoice("ACCEPTED", False, datetime.now(), total)
				invoice.order_skus.extend(order_skus)
				customer.orders.append(invoice)
				db.session.add(invoice)
				for order_sku in order_skus:
				  db.session.add(order_sku)
				
				db.session.commit()
				flash('Order Placed!')

				#Mock the Confirmation Messsage sending process 
				process_send_sms = Process(
				        target=send_sms,
				        args=(customer.phone,'Order '+str(invoice.id)+' has been accepted and will be prepared for departure.'),
				        daemon=True
				    )
				#Once this process has started, the application will proceed while this process continues separately
				# to try to send confirmation message.
				process_send_sms.start()
				return redirect(url_for('customer.show_order_history'))
			except Exception as e:
				db.session.rollback()
				flash('Could not place the order.' + str(e))
				return redirect(url_for('customer.show_cart'))