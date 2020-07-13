from ecomm.products.models import Product, SKU
from flask import Blueprint, render_template, request,abort,session, flash, redirect, url_for
from ecomm import db
from ecomm.invoice import CartSkus
from ecomm.customer import Customer

#Initialize the products blueprint.
products_bp = Blueprint('product',__name__)

def is_logged_in():
	return 'username' in session

def is_customer_logged_in():
	return 'user_id' in session

def is_admin():
	return ('role' in session) and (session['role'] == 'ADMIN')

def is_customer():
	return ('role' in session) and (session['role'] == 'CUSTOMER')

def get_all_products():
	'''
	Get all the products and associated skus.
	'''
	products = {}
	for product in Product.query.all():
		#Is python pass by object
		product.get_key_values(products)
	return products

@products_bp.route('/')
@products_bp.route('/home')
def show_all():
	return render_template('show_all.html',products=get_all_products())

@products_bp.route('/detail/<prod_key>')
@products_bp.route('/detail')
def show_product_detail(prod_key=None):
	'''
	Show details about a product and its related skus.
	'''
	if(prod_key is None):
		prod_key = request.args.get('prod_key')
	product = Product.query.get_or_404(int(prod_key))
	return render_template('show_product_details.html',products=product.get_key_values())


@products_bp.route('/addProduct',methods=['GET','POST'])
def add_product():
	'''
	Add a new product to the catalog.
	'''
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			name = request.form['name']
			description = request.form['description']
			if(not name):
				flash('Incomplete info. Please try again.')
				return render_template('admin_add_product.html')
			else:
				product = Product.query.filter_by(name=name).first()
				if product is None:
					try:
						product = Product(name,description)
						db.session.add(product)
						db.session.commit()
						flash('Product added successfully!')
						return redirect(url_for('product.show_product_detail',prod_key=product.id))
					except Exception as e:
						flash(str(e))
						db.session.rollback()
						return redirect(url_for('product.add_product'),code=307)
				else:
					flash('Product already exists!')
					return redirect(url_for('product.add_product'),code=307)
		else:
			return render_template('admin_add_product.html')

@products_bp.route('/<prod_key>/addSKU',methods=['GET','POST'])
def add_sku(prod_key):
	'''
	Add a new sku to an existing product.
	'''
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			if(not request.form['properties'] or not request.form['price'] or not request.form['stock_qty']):
				#empty fields validation
				flash('Invalid details. Please try again.')
				return render_template('admin_add_sku.html')
			else:
				properties = request.form['properties']
				price = request.form['price']
				stock_qty = request.form['stock_qty']
				product = Product.query.get_or_404(int(prod_key))
				sku = SKU(properties,stock_qty,price)
				product.skus.append(sku)
				db.session.add(sku)
				db.session.commit()
				flash('SKU added successfully!')
				return redirect(url_for('product.show_product_detail',prod_key=prod_key))
		else:
			product = Product.query.get_or_404(int(prod_key), description="Product does not exist!")
			return render_template('admin_add_sku.html',prod_key=prod_key)

@products_bp.route('/<sku_id>/updateSKU/',methods=['GET','POST'])
def update_sku(sku_id):
	'''
	Update a sku with fields like price, stock level etc.
	'''
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			properties = request.form['properties']
			price = request.form['price']
			stock_qty = request.form['stock_qty']
			if(not properties or not price or not stock_qty or (int(stock_qty) < 0)):
				flash('Incomplete info. Please try again.')
				return render_template('admin_update_sku.html')
			else:
				sku = SKU.query.get_or_404(int(sku_id), description="SKU does not exist!")
				try:
					#Update sku
					sku.properties = properties
					sku.price	= float(price)
					sku.stock_qty = int(stock_qty)
					if(sku.stock_qty>0):
						sku.in_stock = True
					else:
						sku.in_stock = False
					db.session.commit()
					flash('Sku updated successfully!')
				except Exception as e:
					flash(str(e))
					db.session.rollback()
				return redirect(url_for('product.show_product_detail',prod_key=sku.product_id))
		else:
			sku = SKU.query.get_or_404(int(sku_id))
			return render_template('admin_update_sku.html',sku=sku)

@products_bp.route('/<sku_id>/addSkuToCart',methods=['POST'])
def add_to_cart(sku_id):
	'''
	Add a sku to cart. A product with no skus can't be added to cart.
	'''
	if (not is_customer_logged_in()) or (not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		quantity = int(request.form['quantity'])
		customer_id = session['user_id']
		
		sku = SKU.query.get_or_404(int(sku_id))
		customer = Customer.query.get_or_404(customer_id)
		cart_entry = CartSkus.query.filter_by(sku_id=int(sku_id)).filter_by(customer_id=int(customer_id)).first()
		#Check if we have sufficient stocks for the selected SKUs.
		if quantity > sku.stock_qty:
			flash('Insufficient stock!')
			return redirect(url_for('product.show_product_detail',prod_key=sku.product_id))
		if cart_entry is None:
			with db.session.no_autoflush:
				#Case 1: This sku is being added for first time to cart.
				try:
					cart_entry = CartSkus(quantity)
					cart_entry.id = 1234
					sku.carts.append(cart_entry)
					customer.cart_skus.append(cart_entry)
					db.session.add(cart_entry)
					db.session.commit()
					flash('Sku added successfully to cart!')
				except Exception as e:
					db.session.rollback()
					flash(str(e))
		else:
			#Case 2: This sku is already present in the cart.
			try:
				cart_entry.quantity += quantity
				db.session.commit()
				flash('Sku added successfully to cart!')
			except Exception as e:
				db.session.rollback()
				flash(str(e))
		return redirect(url_for('customer.show_cart'))