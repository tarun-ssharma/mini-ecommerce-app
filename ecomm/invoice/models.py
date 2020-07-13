from ecomm import db
import enum

'''
ACCEPTED/CANCELLED/DELIVERED orders.
'''
class Invoice(db.Model):
	__tablename__ = 'order'
	id = db.Column(db.Integer,primary_key=True)
	status = db.Column(db.String(50))
	customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'))
	is_paid = db.Column(db.Boolean,default=False)
	time = db.Column(db.DateTime)
	order_skus = db.relationship('OrderSkus', backref=db.backref('invoice',lazy=True))
	total = db.Column(db.Integer)
	agent_id = db.Column(db.Integer,db.ForeignKey('agent.id'))

	def __init__(self,status,is_paid,time, total):
		self.status = status
		self.is_paid = is_paid
		self.time = time
		self.total = total

'''
SKU Details of orders.
'''
class OrderSkus(db.Model):
	__tablename__ = 'order_skus'
	order_id = db.Column(db.Integer, db.ForeignKey('order.id'),primary_key=True)
	sku_id = db.Column(db.Integer, db.ForeignKey('sku.id'),primary_key=True)
	quantity =  db.Column(db.Integer)
	price = db.Column(db.Integer)
	subtotal = db.Column(db.Integer)

	def __init__(self,quantity,price, subtotal):
		self.quantity= quantity
		self.price = price
		self.subtotal = subtotal

'''
SKU details of cart items.
'''
class CartSkus(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'),primary_key=True)
	sku_id = db.Column(db.Integer, db.ForeignKey('sku.id'),primary_key=True)
	quantity =  db.Column(db.Integer)

	def __init__(self,quantity):
		self.quantity= quantity


