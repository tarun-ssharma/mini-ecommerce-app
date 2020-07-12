from ecomm import db
from ecomm.admin import User
from ecomm.invoice import Invoice

class Agent(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	orders = db.relationship('Invoice',backref=db.backref('agent'))

	__mapper_args__ = {
    	'polymorphic_identity':'agent'
    }

