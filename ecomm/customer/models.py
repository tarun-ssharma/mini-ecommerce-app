from ecomm import db
from ecomm.admin import User
from ecomm.invoice import Invoice,CartSkus

class Customer(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	ledgerEntries = db.relationship('FinancialLedgerEntry', backref= db.backref('customer'),lazy='dynamic')
	orders = db.relationship('Invoice', backref= db.backref('customer'))
	cart_skus = db.relationship('CartSkus',backref=db.backref('customer'))
	phone = db.Column(db.Integer)

	def __init__(self, username, password, first_name, last_name, phone=None, email=None):
		super().__init__(username, password, first_name, last_name,email)
		self.phone = -1 if phone is None else phone

	__mapper_args__ = {
    	'polymorphic_identity':'customer'
    }

class FinancialLedgerEntry(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'))
	transaction_date = db.Column(db.DateTime)
	amount = db.Column(db.Float)
	balance = db.Column(db.Float)

	def __init__(self,transaction_date,amount,balance):
		self.transaction_date = transaction_date
		self.amount = amount
		self.balance = balance

