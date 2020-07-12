from ecomm import db
import enum

'''
Requirements:
- an Invoice : has multiple skus
- order state is updatable by agent from confirmed to cancelled
- cash payment is recorded by agent any random time 
- states -- “Confirmed/Accepted/Placed?”, “Delivered”, “Cancelled”
- on order accept -- invoice created, financial ledger updated, SMS sent to customer
- on marking order cancelled before delivered -- reverse financial ledger entries are created
- List order history for each customer -- accessible by that customer and agent
'''

class OrderStates(enum.Enum):
	ACCEPTED = 'Accepted'
	DELIVERED = 'DELIVERED'
	CANCELLED = 'Cancelled'

class Invoice(db.Model):
	__tablename__ = 'order'
	id = db.Column(db.Integer,primary_key=True)
	status = db.Column(db.Enum(OrderStates))
	customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'))
	is_paid = db.Column(db.Boolean,default=False)
	time = db.Column(db.DateTime)
	order_skus = db.relationship('OrderSkus', backref=db.backref('invoice',lazy=True))
	total = db.Column(db.Integer)
	agent_id = db.Column(db.Integer,db.ForeignKey('agent.id'))

	def __init__(self,status,customer_id,is_paid,time, total):
		self.status = status
		self.customer_id = customer_id
		self.is_paid = is_paid
		self.time = time
		self.total = total

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

class CartSkus(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'),primary_key=True)
	sku_id = db.Column(db.Integer, db.ForeignKey('sku.id'),primary_key=True)
	quantity =  db.Column(db.Integer)
	price = db.Column(db.Integer,db.ForeignKey('sku.price'))
	properties = db.Column(db.String, db.ForeignKey('sku.properties'))

	def __init__(self,quantity):
		self.quantity= quantity


