# -*- coding: utf-8 -*-
"""
@author: Mattia
"""
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g
)
from math import log2
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import abort
from psycopg2 import (
        connect
)
from sqlalchemy import create_engine 
import numpy as np
import pyproj
import pandas as pd
import geopandas as gpd

#db connection
def get_dbConn():
    if 'dbConn' not in g:
        myFile = open('dbConfigTest.txt')
        connStr = myFile.readline()
        g.dbConn = connect(connStr)
    return g.dbConn

def close_dbConn():
    if 'dbConn' in g:
        g.dbComm.close()
        g.pop('dbConn')
#splitting written coordinates
def splitcoordinates(df):
    wc=df['writtenCoordinates']
    lat=[]
    lon=[]
    for i in range (len(wc)):
        temp=wc[i].replace("-,",";")
        pos=temp.find(';')
        #splitting coordinates in latitude and longitude
        templat=temp[0:pos]
        templon=temp[pos+1:len(wc)]
        #removing X and Y from coordinates
        templat=templat.replace('X',"")
        templat=templat.replace('Y',"")
        templon=templon.replace('X',"")
        templon=templon.replace('Y',"")
        templon=templon.replace(' ',"")
        #conversion to float
        templat=float(templat)
        templon=float(templon)
        #add lat and lon to list
        lat.append(templat)
        lon.append(templon)
    #add lat and lon lists to dataframe
    df['writtenLatitude']=lat
    df['writtenLongitude']=lon
    return df

#shannon
def shannon(df):
    nh=df[['commonName', 'height']]
    N = len(df.index)
    nh = nh['commonName'].str.strip()
    nh = nh.value_counts()
    maxsh= log2(len(nh.index))
    sh=0
    
    for i in range(len(nh.index)):
        Pi = nh[i]/N
        sh=sh+Pi*log2(Pi)
    esh=(-sh/maxsh)
    return -sh,esh

x=shannon(data_df)
#ricerca per altezza
def heightrange(max,min,df):
    if max is None & min is None:
        s=df
    elif max is None:
        s=df.query('height >= @min')
    elif min is None:
        s=df.query('height <= @max')
    else:
        s=df.query('(height <= @max) & (height >= @min)')
    return s

#ricerca per crown diameter
def crownrange(max,min,df):
    if max is None & min is None:
        s=df
    elif max is None:
        s=df.query('crownDiameter >= @min')
    elif min is None:
        s=df.query('crownDiameter <= @max')
    else:
        s=df.query('(crownDiameter <= @max) & (crownDiameter >= @min)')
    return s

#ricerca per nome
def searchname(worser,df): 
    if worser is None:
        s=df
    else:
        s=df.query("commonName == @worser")
    return s

#ricerca per area
def searcharea(worser,df): 
    if worser is None:
        s=df
    else:
        s=df.query("censusArea == @worser")
    return s

#ricerca per gruppo
def searchgroup(worser,df): 
    if worser is None:
        s=df
    else:
        s=df.query("group == @worser")
    return s

#ricerca per settore
def searchsector(worser,df): 
    if worser is None:
        s=df
    else:
        s=df.query("sector == @worser")
    return s

# Create the application instance
app = Flask(__name__, template_folder="templates")
# Set the secret key 
app.secret_key = '_5#(tgy&_loé/c]/'

#registration page
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['lastname']
        email = request.form['email']
        atpos = email.find('@')
        validdomain='mail.polimi.it'
        domain=email[atpos+1:len(email)-1]
        password = request.form['password']
        passwordcon = request.form['checkpassword']
        error = None
        #check for mandatory credentials
        if not name:
            error= 'Name is required'
        elif not surname:
            error= 'Surname is required'
        elif not email:
            error= 'Email is required'
        elif not password:
            error= 'Password is required'
        elif not passwordcon:
            error= 'Password Confirmation is required'
        #check for authorized domain
        #elif domain != validdomain:
            #error='Domain not authorized'
        #check for password 
        elif (len(password)<8):
            error='Password needs to be at least 8 characters long'
        elif password!=passwordcon:
            error='Different password confirmation'
        #check if there is an existing account associated with the email
        else:
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute(
            'SELECT email FROM pa_user WHERE email = %s', (email,))
            if cur.fetchone() is not None:
                error = 'This email is already associated with an existing account'
                cur.close()
        #registration in database
        if error is None:
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO pa_user (firstname, lastname, email, password) VALUES (%s, %s,%s, %s)',
                (name, surname, email, generate_password_hash(password))
            )
            cur.close()
            conn.commit()
            return redirect(url_for('login'))
        flash(error)
    return render_template('aasignup.html')

#login page
@app.route('/login', methods=('GET', 'POST'))
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_dbConn()
        cur = conn.cursor()
        error = None
        
        cur.execute(
            'SELECT * FROM pa_user WHERE email = %s', (email,)
        )
        user = cur.fetchone()
        cur.close()
        conn.commit()
        #check user credentials
        if user is None:
            error = 'Invalid email'
        elif not check_password_hash(user[3], password):
            error = 'Wrong password.'
        
        if error is None:
            session.clear()
            session['email'] = user[0]
            return redirect(url_for('home'))

        flash(error)

    return render_template('aalogin.html')

#cookies
def load_logged_in_user():
    email = session.get('email')

    if email is None:
        g.user = None
    else:
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM pa_user WHERE email = %s', (email,)
        )
        g.user = cur.fetchone()
        cur.close()
        conn.commit()
    if g.user is None:
        return False
    else: 
        return True
    
#logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

#home page
@app.route('/')
@app.route('/home')
def home():
    error = None
    if load_logged_in_user():
        return render_template('aamaintest.html')
    else:
        error='You are not logged in'
        flash(error)
        return redirect(url_for('login'))
        
# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True)