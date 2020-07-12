
from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from ecomm.invoice import Invoice,OrderStates
from datetime import datetime
from ecomm.customer.models import Customer

customer_bp = Blueprint('customer',__name__)

def generate_otp():
	return 1234

def is_logged_in():
	return 'user_id' in session

def is_customer():
	return ('role' in session) and (session['role'] == 'CUSTOMER')

@customer_bp.route('/login',methods=['GET','POST'])
def login():
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
				session['generated_otp'] = generate_otp()
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
	if(not is_logged_in() or not is_customer()):
		#Not logged in
		return redirect(url_for('customer.login'))
	else:
		#Logged in customer
		return render_template('customer_home.html',products=get_all_products())

@customer_bp.route('/logout')
def logout():
	session.pop('user_id', None)
	session.pop('role',None)
	flash('Logged out successfully!')
	return redirect(url_for('customer.login'))

@customer_bp.route('/viewCart')
def show_cart():
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		cart_skus = CartSkus.query.filter_by(customer_id=session['user_id']).all()
		last_prices = {}
		stock_qtys = {}
		for cart_sku in cart_skus:
			stock_qtys[cart_sku.sku_id] = SKU.query.get_or_404(cart_sku.sku_id).stock_qty
			last_invoice = Invoice.query.filter_by(customer_id=session['user_id']).filter_by(Invoice.order_skus.any(sku_id=cart_sku.sku_id)).order_by(time).last()
			if last_invoice is None:
				last_prices[cart_sku.sku_id] = -1
			else:	
				last_prices[cart_sku.sku_id] = OrderSkus.query.filter_by(order_id=last_invoice.id).first().price

		return render_template('show_cart.html',cart_skus=cart_skus,last_prices=last_prices,stock_qtys=stock_qtys)

@customer_bp.route('/orderHistory')
def show_order_history():
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		invoices = Invoice.query.filter_by(customer_id=session['user_id']).all()
		return render_template('order_history.html',invoices=invoices)

@customer_bp.route('/placeOrder',methods=['POST'])
def place_order():
	if(not is_logged_in() or not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		try:
			customer_id = session['user_id']
			cart_skus = CartSkus.query.filter_by(customer_id=customer_id).all()
			total = 0
			order_skus = []
			for cart_sku in cart_skus:
				sku_stock_qty = SKU.query.get_or_404(cart_sku.sku_id).stock_qty
				if(cart_sku.quantity > sku_stock_qty):
					flash('Sku'+cart_sku.sku_id+' has insufficient stock')
					return redirect(url_for('customer.show_cart'))
				subtotal = sku_stock_qty*(cart_sku.price)
				order_skus.append(OrderSkus(sku_stock_qty,cart_sku.price,subtotal))
				total += subtotal

			invoice = Invoice(OrderStates.ACCEPTED, customer_id, False, datetime.now(), total)
			invoice.order_skus.extend(order_skus)
			db.session.add(invoice)
			db.session.commit()
			flash('Order Placed!')
			return redirect(url_for('customer.show_order_history'))
		except Exception as e:
			flash('Could not place the order.' + str(e))
			return redirect(url_for('customer.show_cart'))