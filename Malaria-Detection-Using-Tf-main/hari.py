# -*- coding: utf-8 -*-
"""
Created on Tue May  4 12:22:13 2021

@author: hp
"""

from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np

# Keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Flask utils
from flask import Flask, redirect, url_for, request, render_template,session
import bcrypt
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'Malaria'
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/Malaria'
mongo = PyMongo(app)
app = Flask(__name__)
MODEL_PATH ='model_vgg19.h5'
model = load_model(MODEL_PATH)
def model_predict(file_path,model):
    img = image.load_img(file_path,target_size=(224, 224))
    x = image.img_to_array(img)
    x = x/255
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x)
    preds=np.argmax(preds, axis=1)
    if preds==0:
        preds = "INFECTED"
    else:
        preds = "uninfected"
    return preds
@app.route('/',methods = ['POST','GET'])
def index():
    if 'email' in session:
        return render_template('sw_features.html')    
    return render_template('index_sw.html')
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    msg = ""
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(f.filename)
        file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        msg = model_predict(file_path,model)
        session['status'] = msg
        return render_template("sw_features.html",msg = "Result: "+msg)
    return None
@app.route('/login', methods=['POST','GET'])
def login():
    msg = ""
    users = mongo.db.collection
    login_user = users.find_one({'email' : request.form['email']})

    if login_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['email'] = request.form['email']
            session['Name'] = login_user['Name']
            session['status'] = 'unknown'
            #return redirect(url_for('sw_features.html'))
            return render_template('sw_features.html')
    msg = 'Invalid username/password combination'
    return render_template('index_sw.html',msg = msg)
@app.route('/register', methods=['POST', 'GET'])
def register():
    msg = ""
    if request.method == 'POST':
        users = mongo.db.collection
        existing_user = users.find_one({'email' : request.form['email']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'Name' : request.form['Name'],'email':request.form['email'], 'password' : hashpass,'Address':request.form['Address'],'status':'unknown'})
            session['email'] = request.form['email']
            session['status'] = 'unknown'
            msg = "You have successfully registered !!"
            #return redirect(url_for('index'))  #sending to index function
            return render_template('index_sw.html',msg = msg)
        msg = "That email already exists!"
        return render_template('index_sw.html',msg = msg)

    return render_template('register_sw.html',msg = msg)
@app.route('/logout') 
def logout(): 
    msg=""
    session.pop('email', None) 
    session.pop('Name', None) 
    return render_template('index_sw.html',msg = "Successfully logged out")
if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run()
