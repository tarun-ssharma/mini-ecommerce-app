from ecomm import app
app.config['SESSION_TYPE'] = 'memcached'
app.secret_key = "random_string"

'''
Initialization of the main application.
'''
if __name__ == '__main__':
	app.run(debug=True)
