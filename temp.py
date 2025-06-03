from collections import *

from flask import Flask, render_template, request, url_for, redirect,jsonify, session
from pymongo import MongoClient

#from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

import bcrypt

import math

#set app as a Flask instance 

app = Flask(__name__)
#encryption relies on secret keys so they could be run
app.secret_key = "testing"

# #connect to your Mongo DB database
def MongoDB():
    client = MongoClient("mongodb+srv://deepasriselladurai:deepasri_25@studentsresultcluster.9v1m0.mongodb.net/")
    db = client.get_database('StudentsRecordDatabase')
    records = db.register
    return records
    #return records
records = MongoDB()

'''
##Connect with Docker Image###
def dockerMongoDB():
    client = MongoClient(host='test_mongodb',
                            port=27017, 
                            username='root', 
                            password='pass',
                            authSource="admin")
    db = client.users
    pw = "test123"
    hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    records = db.register
    records.insert_one({
        "name": "Test Test",
        "email": "test@yahoo.com",
        "password": hashed
    })
    return records
'''
#record = dockerMongoDB()

#assign URLs to have a particular route 
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/home")
def home1():
    return render_template("home.html")

@app.route("/index", methods=['post', 'get'])
def index():
    message = 'HELLO'

    #if method post in index
    if "email" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        #if found in database showcase that it's found 
        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('index.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('index.html', message=message)
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('index.html', message=message)
        else:
            #hash the password and encode it
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            #assigning them in a dictionary in key value pairs
            user_input = {'name': user, 'email': email, 'password': hashed}
            #insert it in the record collection
            records.insert_one(user_input)
            
            #find the new created account and its email
            user_data = records.find_one({"email": email})

            new_email = user_data['email']
            #if registered redirect to logged in as the registered user
            return render_template('logged_in.html', email=new_email)
    return render_template('index.html')

@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #check if email exists in database
        email_found = records.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            #encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)

@app.route('/start',methods=["POST","GET"]) 
def start():
    if "email" in session:
        return render_template("start.html")
    return render_template('index.html')

@app.route("/submit_data", methods=["POST"])
def submit_data():
    if request.method == "POST":
        data = request.form.to_dict()
        details_collection = records.database['Details']
        details_collection.insert_one(data)
        name=records.find_one({"email": session["email"]})['name']
        email=records.find_one({"email": session["email"]})['email']
        return render_template('profile.html',name=name,email=email,details_dict=details_collection.find_one({"email": session["email"]}))    
        
@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        user_data = records.find_one({"email": email})
        name = user_data['name']
        return render_template('logged_in.html', email=email,name=name)
    else:
        return redirect(url_for("login"))

@app.route('/profile', methods=["POST","GET"])
def profile():
    if "email" in session:
        email = session["email"]
        user_data = records.find_one({"email": email})
        name = user_data['name']

        # Accessing data from 'Details' collection
        details_collection = records.database['Details']
        student_details = details_collection.find_one({"email": email})

        details_dict = student_details if student_details else {}

        return render_template('profile.html', email=email, name=name, details_dict=details_dict)
    else:
        return redirect(url_for("login"))

@app.route('/scorecard', methods=["POST","GET"])
def scorecard():
    if "email" in session:
        email = session["email"]
        user_data = records.find_one({"email": email})
        name = user_data['name']
        details_collection = records.database['Details']
        student_details = details_collection.find_one({"email": email})

        details_dict = student_details if student_details else {}

        return render_template('scorecard.html', email=email, name=name, details_dict=details_dict)
    else:
        return redirect(url_for("login"))



@app.route('/update')
def update():
    email=session["email"]
    data=records.find_one({"email":email})
    return render_template('update.html',data=data)

@app.route('/update_data', methods=['POST'])
def update_data():
    email=session["email"]
    data = request.form.to_dict()  # Retrieve form data as a dictionary
    
    if not data or not email:
        return jsonify({'status': 'failure', 'message': 'Invalid data'}), 400

    json_data = jsonify(data).json  # Convert the dictionary to JSON

    new_values = {"$set": json_data} 
    
    result = records.update_many({'email': email},new_values)
    
    #if result:
    #    return jsonify({'status': 'success', 'message': 'Data updated successfully'})
    #else:
    #    return jsonify({'status': 'failure', 'message': 'No data was updated'})
    if result:
        email = session["email"]
        user_data = records.find_one({"email": email})
        name = user_data['name']
        return render_template('logged_in.html', email=email,name=name)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('index.html')

def short_int(value):
    """Convert an integer to a short form."""
    if value >= 1_000_000:
        return f'{value / 1_000_000:.1f}M'
    elif value >= 1_000:
        return f'{value / 1_000:.1f}K'
    return str(math.ceil(value))

app.jinja_env.filters['short_int'] = short_int



if __name__ == "__main__":
  app.run(debug=True, port=5000)
