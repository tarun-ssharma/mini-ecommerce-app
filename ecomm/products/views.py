from ecomm.products.models import Product, SKU
from flask import Blueprint, render_template, request,abort,session, flash, redirect, url_for
from ecomm import db

products_bp = Blueprint('product',__name__)

'''
Requirements:
- updatable -- prod descr., price, stock level, status
- can add a new product
- can update an existing product
- can add a SKU to cart
- last price(if ordered) shown for every sku in cart
- only in_stock skus allowed to be ordered
- an Invoice : has multiple skus

- addProd button -- HOME PAGE
- search prod by name -- prod details page -- edit product / CREATE skus / SELECT AND ADD SKUS TO CART (addSkuToCart) -- HOME + PROD DETAILS PAGES
'''

def get_all_products():
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
def show_product_detail(prod_key):
	product = Product.query.get_or_404(prod_key)
	return render_template('show_product_details.html',products=product.get_key_values())

#Search prod by name

@products_bp.route('/addProduct',methods=['GET','POST'])
def add_product():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			name = request.form['name']
			description = request.form['description']
			price = request.form['price']
			stock_qty = request.form['stock_qty']
			if(not name or not price or not stock_qty):
				flash('Incomplete info. Please try again.')
				return render_template('admin_add_product.html')
			else:
				product = Product.query.filter_by(name=name).first()
				if product is None:
					try:
						product = Product(name, price, stock_qty,description)
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
def add_sku():
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			if(not request.args['product_id']):
				#empty fields validation
				flash('Invalid details. Please try again.')
				return render_template('admin_add_sku.html')
			else:
				product_id = request.args['product_id']
				properties = request.args['properties']
				price = request.form['price']
				stock_qty = request.form['stock_qty']
				product = Product.query.get_or_404(prod_key)
				sku = SKU(properties,stock_qty,price)
				product.skus.append(sku)
				db.session.add(sku)
				db.session.commit()
				flash('SKU added successfully!')
				return redirect(url_for('product.show_product_detail',prod_key=prod_key))
		else:
			product = Product.query.get_or_404(prod_key, description="Product does not exist!")
			return render_template('admin_add_sku.html',prod_key=prod_key)

@products_bp.route('/<sku_id>/updateSKU/',methods=['GET','POST'])
def update_sku(prod_key):
	if (not is_logged_in()) or (not is_admin()):
		return redirect(url_for('admin.login'))
	else:
		if request.method == 'POST':
			#If id exists, flash(already exists)
			properties = request.form['properties']
			price = request.form['price']
			stock_qty = request.form['stock_qty']
			if(not properties and not price and not stock_qty):
				flash('Incomplete info. Please try again.')
				return render_template('admin_update_sku.html')
			else:
				sku = SKU.query.get_or_404(sku_id, description="SKU does not exist!")
				try:
					#Update sku
					sku.properties = properties
					sku.price	= price
					sku.stock_qty = stock_qty
					db.session.commit()
					flash('Sku updated successfully!')
				except Exception as e:
					flash(str(e))
					db.session.rollback()
				return redirect(url_for('product.show_product_detail',prod_key=sku.product_id))
		else:
			sku = SKU.query.get_or_404(sku_id)
			return render_template('admin_update_sku.html',sku=sku)

@products_bp.route('/<sku_id>/addSkuToCart',methods=['POST'])
def add_to_cart():
	if (not is_logged_in()) or (not is_customer()):
		return redirect(url_for('customer.login'))
	else:
		quantity = request.arg['quantity']
		customer_id = request.args['customer_id']
		sku = SKU.query.get_or_404(sku_id)
		cart_entry = CartSkus.query.filter_by(sku_id=sku_id).filter_by(customer_id=customer_id).first()
		#CHECK FOR STOCK_QTY FOR THAT SKU
		if quantity > sku.stock_qty:
			flash('Insufficient stock!')
			return redirect(url_for('product.show_product_detail',prod_key=sku.product_id))
		if cart_entry is None:
			#This sku is being added for first time to cart.
			cart_entry = CartSkus(quantity)
			sku.carts.append(cart_entry)
			db.session.add(cart_entry)
			db.session.commit()
		else:
			#This sku is already present in the cart.
			cart_entry.quantity += quantity
			db.session.commit()
		flash('Sku added successfully to cart!')
		return redirect(url_for('customer.show_cart'))