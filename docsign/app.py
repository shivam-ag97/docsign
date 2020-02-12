from flask import Flask,jsonify,request,render_template,g, url_for, session, redirect
from flask_restful import Api, Resource
from pymongo import MongoClient
import os


app = Flask(__name__)
api = Api(app)
app.secret_key = 'qweasb@#12344'

client = MongoClient('mongodb+srv://shivam:shivam@cluster0-3mbds.mongodb.net/test?retryWrites=true&w=majority')
db = client.get_database('docsign')
users = db.users



@app.route('/', methods=['POST' , 'GET'])
def index():
	if request.method == 'POST':
		session.pop('user' , None)
		users=db.users
		login_user = users.find_one({'user_id' : request.form['user']})
		if login_user:
			p=request.form['password']
			if p == login_user['pw']: 
				session['user']=request.form['user']
				user = login_user['user_name']
				# user = {'username': user}
				return redirect(url_for('protected'))
			return "Invalid userID or password"
		return "Invalid Credentials"
	return render_template('index.html')




@app.route('/register',methods=['POST','GET'])
def register():
	if request.method == 'POST':
		users=db.users
		existing_user = users.find_one({'user_id' : request.form['userid']})

		if existing_user is None:
			users.insert({'user_id' : request.form['userid'],'pw' : request.form['pass'],'user_name' : request.form['username']})
			session['user_name'] = request.form['username']
			return redirect(url_for('index'))

		return " User already registered! "
	return render_template('register.html')





@app.route('/protected')
def protected():
	if g.user:
		return render_template('draw.html', user=session['user'])
	return redirect(url_for('index'))


@app.before_request
def before_request():
	g.user = None

	if 'user' in session:
		g.user = session['user']


@app.route('/dropsession')
def dropsession():
	session.pop('user', None)
	return render_template('index.html')





if __name__=="__main__":
	app.run(debug=True)
