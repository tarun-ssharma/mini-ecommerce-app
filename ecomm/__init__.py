from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///db/database.db'
db = SQLAlchemy(app)

from ecomm.admin.views import admin_bp
from ecomm.products.views import products_bp
from ecomm.agent.views import agent_bp
from ecomm.customer.views import customer_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(products_bp, url_prefix='/products')
app.register_blueprint(agent_bp, url_prefix='/agent')
app.register_blueprint(customer_bp, url_prefix='/customer')


#db.drop_all()
db.create_all()
