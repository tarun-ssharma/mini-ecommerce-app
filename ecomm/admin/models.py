from ecomm import db
import enum

user_roles = db.Table('user_roles',
	db.Column('user_id',db.Integer, db.ForeignKey('user.id'),primary_key=True),
	db.Column('role_id',db.Integer, db.ForeignKey('role.id'),primary_key=True)
	)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String)
	password = db.Column(db.String)
	email = db.Column(db.String)
	first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
	last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
	roles = db.relationship('Role',secondary=user_roles,  backref=db.backref('users',lazy='dynamic'))
	type = db.Column(db.String(50))

	__mapper_args__ = {
		'polymorphic_identity':'user',
		'polymorphic_on':'type'
	}

	def __init__(self, username, password, first_name, last_name,email=None):
		self.username = username
		self.password = password
		self.email = "" if email is None else email
		self.first_name = first_name
		self.last_name = last_name

	def get_key_values(self,users=None):
		if users is None:
			users = {}
		users[user.id] = {
		'name': self.username,
		'mail': self.email
		}
		return users

class Admin(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	__mapper_args__ = {
			'polymorphic_identity':'admin'
		}

class RoleValues(enum.Enum):
	ADMIN = 'Admin'
	AGENT = 'Agent'
	CUSTOMER = 'Customer'

class Role(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	type = db.Column(db.Enum(RoleValues))

	def __init__(self, type):
		self.type = type

