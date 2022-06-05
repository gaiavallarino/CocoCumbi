# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 21:36:40 2022

@author: marti
"""

# -*- coding: utf-8 -*-

""" IMPORTING LIBRARIES"""
# import packages needed to Perform a REST API JSON data request with Python
from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g, abort
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
import requests
import json
import matplotlib.pyplot as plt
from psycopg2 import (connect)
from sqlalchemy import create_engine
import requests
import json
import pandas as pd
import geopandas as gpd
from bokeh.models import ColumnDataSource, LabelSet, Select, HoverTool
from bokeh.plotting import figure, output_file
from bokeh.tile_providers import CARTODBPOSITRON, get_provider # CARTODBPOSITRON_RETINA
from bokeh.io import curdoc, output_notebook, show
from bokeh.embed import components, server_document
from bokeh.layouts import row
#output_notebook()
from bokeh.resources import INLINE, CDN
output_notebook(INLINE)
import subprocess

"""FUNCTIONS"""



"""SETTING DATABASE CONNECTION"""
def insert_df():
    #open the configuration parameter from a txt file the table
    myFile = open('dbConfigTest.txt')
    connStr = myFile.readline()
    myFile.close()
    
    cleanup = ('DROP TABLE IF EXISTS pa_user CASCADE','DROP TABLE IF EXISTS trees','DROP TABLE IF EXISTS pa_data')
    
    #variable list containing the structures of the database
    commands = (
        """ CREATE TABLE pa_user(email VARCHAR(255) PRIMARY KEY, firstname VARCHAR(255) NOT NULL, lastname VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL )""")
    
    #create the connection with the database
    conn = connect(connStr)
    cur = conn.cursor()
    for command in cleanup :
        cur.execute(command)
    
    cur.execute(commands)
    cur.close()
    conn.commit()
    conn.close()
    
    #setup db connection 
    #NOTE: dbConfig.txt MUST be modified with the comfiguration of your DB
    # build the string for the customized engine
    #è come quello che fa il prof ma mettendo in un file di testo username, passsword ecc ecc, come risultato ho 
    #engine = create_engine('postgresql://postgres:admin@localhost:5432/databaseCoco')
    dbD = connStr.split()
    dbD = [x.split('=') for x in dbD]
    engStr = 'postgresql://'+ dbD[1][1]+':'+ dbD[2][1] + '@localhost:5432/' + dbD[0][1]
    engine = create_engine(engStr)  
    
    #IMPORT DATA FROM EPICOLLECT
    # send the request to the API of Epicollect5
    #response = requests.get('https://five.epicollect.net/api/export/entries/censo-forestal-del-canton-ruminahui?sort_orderASC&per_page=1000')
    response = requests.get('https://five.epicollect.net/api/export/entries/censo-forestal-del-canton-ruminahui?sort_order=ASC&per_page=1000')
    
    raw_data = response.text
    
    # parse the raw text response 
    data = json.loads(raw_data)
    
    # from JSON to Pandas DataFrame
    #dividiamo i sati in una tabella carina
    data_df = pd.json_normalize(data['data']['entries'])
    
    len(data_df) # for a good plot it's better to extract more then 50 lines
    # preprocessing data_df
    #le prime 4 colonne sono inutili quindi le tolgo
    data_df = data_df.iloc[: ,4:].copy()
    data_df.columns = ['treeID','date','censusArea','group','commonName','scientificName','status','writtenCoordinates','dbh','height','crownDiameter','crownRadius','sector','property','risk','latitude','longitude','accuracy','utmNorthing','utmEasting','utmZone']
    
    """GEOREFERENCING DATA"""
    data_df['latitude'] = data_df['latitude'].replace([''],'0')
    data_df['longitude'] = data_df['longitude'].replace([''],'0')
    data_df_proc= data_df.loc[data_df['latitude'] != '0']
    data_df_proc = data_df_proc.reset_index(drop=True)
    data_df_proc = data_df_proc.drop(['utmNorthing','utmEasting','crownRadius','utmZone','property','writtenCoordinates','date'], axis=1).copy()
    
    # from Pandas DataFrame to GeoPandas GeoDataFrame
    #we add a geometry column using the numeric coordinate colums
    data_geodf_proc = gpd.GeoDataFrame(data_df_proc, geometry=gpd.points_from_xy(data_df_proc.longitude, data_df_proc.latitude))
    data_geodf_proc = data_geodf_proc.drop_duplicates(subset ="geometry",keep = False)
    data_geodf_proc.to_crs = {'init': 'epsg:32617'}
    
    #convert from LAT/LNG to Mercator
    def wgs84_to_web_mercator(df, lon="LON", lat="LAT"):
          k = 6378137
          df["x"] = np.float64(df[lon] * (k * np.pi/180.0))
          df["y"] = np.log(np.tan((90 + np.float64(df[lat])) * np.pi/360.0)) * k
          return df
    data_geodf_proc = wgs84_to_web_mercator(data_geodf_proc,'longitude','latitude')# write the dataframe into postgreSQL
    data_geodf_proc.to_postgis('trees', engine, if_exists = 'replace', index=False)
    #data_geodf_proc = data_geodf_proc.drop('geometry', axis=1).copy()
    return engine
