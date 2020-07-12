from ecomm import db

'''
Requirements:
- updatable -- prod descr., price, stock level, status
- can add a new product
- can update an existing product
- can add a SKU to cart
- last price(if ordered) shown for every sku in cart
- only in_stock skus allowed to be ordered
- an Invoice : has multiple skus
'''

class Product(db.Model):
	id =  db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255),nullable=False)
	description = db.Column(db.String(255), default="")
	skus = db.relationship('SKU',backref='product')

	def __init__(self, name, price,stock_qty, description=None):
		self.name = str(name)
		if(description is not None):
			self.description = description

	def get_key_values(self,products=None):
		if products is None:
			products = {}
		products[self.id] = {
		'name': self.name,
		'description': self.description,
		}
		skus = {}
		for sku in self.skus:
			sku.get_key_values(skus)
		products[self.id]['skus'] = skus
		return products

class SKU(db.Model):
	__tablename__ = 'sku'
	id = db.Column(db.Integer, primary_key=True)
	properties = db.Column(db.String(255))
	product_id = db.Column(db.Integer, db.ForeignKey('product.id'),nullable=False)
	in_stock =  db.Column(db.Boolean,default=False)
	stock_qty = db.Column(db.Integer,nullable=False)
	price =  db.Column(db.Float,nullable=False)
	carts = db.relationship('CartSkus',backref=db.backref('skus',lazy='dynamic'))
	
	def __init__(self,properties,stock_qty,price):
		self.properties = properties
		self.price = float(price)
		self.stock_qty = int(stock_qty)
		if(self.stock_qty > 0):
			self.in_stock = True

	def get_key_values(self,skus=None):
		if skus is None:
			skus = {}
		properties_list = [pair.split('=') for pair in self.properties.split(',')]
		sku = {}
		for pair in properties_list:
			sku[pair[0]] = pair[1]
		sku['price'] = self.price
		sku['stock_qty'] = self.stock_qty
		sku['in_stock'] = self.in_stock
		skus[self.id] = sku
		return skus