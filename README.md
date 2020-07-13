# miniEcommerceApp
This is a mini e-commerce web application developed using Flask web framework and SQLAlchemy ORM framework with sqlite database in python programming language.

To run the web app:
1. Install requirements mentioned in requirements.txt: pip install -r requirements.txt
2. Run the application: python run.py
3. Access the admin user at: http://127.0.0.1:5000/admin  (Use 'admin' as username and 'admin' as password) : Create agent and customers
4. Access the agent user at: http://127.0.0.1:5000/agent (Login using added agents in step3)
5. Access the customer user at: http://127.0.0.1:5000/customer (Login using added customers in step3)

In the existing db, I have created a few orders, a product with two skus and:
1. Agent with username = 'agent', password='agent'
2. Customer with phone = 7665424890  , OTP = 1234

To run the application with a fresh db: disable comment [#db.drop_all()] in ecomm/__init__.py

