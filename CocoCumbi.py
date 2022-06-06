# -*- coding: utf-8 -*-
"""
@author: Mattia
"""


""" IMPORTING LIBRARIES AND PACKAGES"""
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g
)
from math import log2
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2 import (connect)
import pandas as pd
import geopandas as gpd
import requests
import json
from bokeh.io import output_notebook
from bokeh.embed import components, server_document
#output_notebook()
from bokeh.resources import INLINE
output_notebook(INLINE)
import subprocess
#from connection import insert_df
from connection import engine
from map_correct import p1
#from prova import trees


"""FUNCTIONS"""
#this allows the bokeh app running on port 5006 to be accessed by Flask at port 5000
def bash_command(cmd):
    subprocess.Popen(cmd, shell=True)
    
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

#simpson
def simpson(df):
    nh=df[['commonName', 'height']]
    N = len(df.index)
    nh = nh['commonName'].str.strip()
    nh = nh.value_counts()
    maxsimp = 1/(len(nh.index))
    simp=0
    for i in range (len(nh.index)):
        Pi = nh[i]/N
        simp=simp+(Pi)**2     
    esimp=(1-simp)/(1-maxsimp)
    return (1-simp), esimp

#statistics
def statistics(df):
    meanh=df['height'].mean()
    meanc=df['crownDiameter'].mean()
    meandbh=df['dbh'].mean()
    maxh=df['height'].max()
    minh=df['height'].min()
    maxc=df['crownDiameter'].max()
    minc=df['crownDiameter'].min()
    maxdbh=df['dbh'].max()
    mindbh=df['dbh'].min()
    return meanh,meanc,meandbh,maxh,minh,maxc,minc,maxdbh,mindbh

#ricerca per altezza
def heightrange(max,min,df):
    if (not max) & (not min):
        s=df
    elif not max:
        min=float(min)
        s=df.query('height >= @min')
    elif not min:
        max=float(max)
        s=df.query('height <= @max')
    else:
        min=float(min)
        max=float(max)
        s=df.query('(height <= @max) & (height >= @min)')
    return s

#ricerca per altezza
def dbhrange(max,min,df):
    if (not max) & (not min):
        s=df
    elif not max:
        min=float(min)
        s=df.query('dbh >= @min')
    elif not min:
        max=float(max)
        s=df.query('dbh <= @max')
    else:
        min=float(min)
        max=float(max)
        s=df.query('(dbh <= @max) & (dbh >= @min)')
    return s

#ricerca per crown diameter
def crownrange(max,min,df):
    if (not max) & (not min):
        s=df
    elif not max :
        min=float(min)
        s=df.query('crownDiameter >= @min')
    elif not min :
        max=float(max)
        s=df.query('crownDiameter <= @max')
    else:
        min=float(min)
        max=float(max)
        s=df.query('(crownDiameter <= @max) & (crownDiameter >= @min)')
    return s

#ricerca per nome
def searchname(worser,df): 
    if not worser:
        s=df
    else:
        s=df.query("commonName == @worser")
    return s

#ricerca per area
def searcharea(worser,df): 
    if not worser:
        s=df
    else:
        s=df.query("censusArea == @worser")
    return s

#ricerca per gruppo
def searchgroup(worser,df): 
    if not worser:
        s=df
    else:
        s=df.query("group == @worser")
    return s

#ricerca per settore
def searchsector(worser,df): 
    if not worser:
        s=df
    else:
        s=df.query("sector == @worser")
    return s









"""FLASK APPLICATION"""
# import geo data
#engine = insert_df()
trees = gpd.GeoDataFrame.from_postgis('trees', engine, geom_col='geometry')
trees = trees.drop('geometry', axis=1).copy()
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
        domain=email[atpos+1:len(email)]
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
        elif domain != validdomain:
            error='Domain not authorized'
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
        return render_template('aaerror.html',error=error)
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
        return render_template('aaerror.html',error=error)
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
        return render_template('aamaintest.html',error=error)
    else:
        error='You are not logged in'
        flash(error)
        return redirect(url_for('login'))
    
#query page
@app.route('/query',methods=('GET','POST'))
def query():
    if request.method == 'POST':
        #import data for query from html
        hmin=(request.form['hmin'])
        hmax=(request.form['hmax'])
        cmin=(request.form['cmin'])
        cmax=(request.form['cmax'])
        dbhmin=(request.form['dbhmin'])
        dbhmax=(request.form['dbhmax'])
        nameser=request.form['nameser']
        groupser=request.form['groupser']
        sectorser=request.form['sectorser']
        areaser=request.form['areaser']
        #query
        queryres=trees
        queryres=heightrange(hmax, hmin, queryres)
        queryres=crownrange(cmax, cmin, queryres)
        queryres=dbhrange(dbhmax, dbhmin, queryres)
        queryres=searchname(nameser, queryres)
        queryres=searchgroup(groupser, queryres)
        queryres=searchsector(sectorser, queryres)
        queryres=searcharea(areaser, queryres)
        if queryres.empty == False:
            shan=shannon(queryres)
            simp=simpson(queryres)
            stat=statistics(queryres)
            queryres.columns=['TreeID','Census area','Group','Name','Scientific name','Status','DBH(m)','Height(m)','Crown diameter(m)','Sector','Risk','latitude','longitude','accuracy','X','Y']
            return render_template('newqueryresults.html',tables=[queryres.to_html(classes='data',header="true")],shan=shan,simp=simp,stat=stat)        
        error='Empty Dataframe'
        return render_template('aaerror.html',error=error)
    return render_template('newquery.html')

@app.route('/team', methods=[('GET')])
def team():
    return render_template("aateam.html")


@app.route('/barplot', methods=[('GET')])
def barplot():
    script =server_document("http://localhost:5006/widget")
    print(script)
    return render_template("aagraphs.html", script=script)

@app.route('/map', methods=[('GET')])
def intmap():
    p1_script, p1_div = components(p1)
    return render_template('aamap.html', p1_script= p1_script, p1_div= p1_div)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    bash_command('bokeh serve ./widget.py --allow-websocket-origin=127.0.0.1:5000')
    bash_command('bokeh serve ./map_correct.py --allow-websocket-origin=127.0.0.1:5000 --port=5007')
    app.run(debug=True)
     


