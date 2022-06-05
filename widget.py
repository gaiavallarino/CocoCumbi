# -*- coding: utf-8 -*-
"""
Created on Sun May 29 23:31:51 2022

@author: marti
"""
#Importing the required packages
import numpy as np
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
from bokeh.embed import components
from bokeh.layouts import row
#output_notebook()
from bokeh.resources import INLINE, CDN
output_notebook(INLINE)

#database connection..
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




data_df['latitude'] = data_df['latitude'].replace([''],'0')
data_df['longitude'] = data_df['longitude'].replace([''],'0')
data_df_proc= data_df.loc[data_df['latitude'] != '0']
data_df_proc = data_df_proc.reset_index(drop=True)
#trees_splitted = splitcoordinates(data_df)



# from Pandas DataFrame to GeoPandas GeoDataFrame
#we add a geometry column using the numeric coordinate colums
data_geodf_proc = gpd.GeoDataFrame(data_df_proc, geometry=gpd.points_from_xy(data_df_proc.longitude, data_df_proc.latitude))
data_geodf_proc = data_geodf_proc.drop_duplicates(subset ="geometry",keep = False)
#unique = data_geodf_proc['longitude'].unique()
#unique = data_geodf_proc.drop_duplicates(subset ="geometry",keep = False, inplace = True)
#data_geodf_proc = gpd.GeoDataFrame(data_df_proc, geometry=gpd.points_from_xy(data_df_proc.writtenLongitude, data_df_proc.writtenLatitude))
data_geodf_proc.to_crs = {'init': 'epsg:32617'}
# write the dataframe into postgreSQL
data_geodf_proc.to_postgis('trees', engine, if_exists = 'replace', index=False)


# import geo data
gdf_trees = gpd.GeoDataFrame.from_postgis('trees', engine, geom_col='geometry')
# save a copy of the GeoDataFrame in a new DataFrame by dropping the 'geometry' column
trees = gdf_trees.drop('geometry', axis=1).copy()
#convert from LAT/LNG to Mercator
def wgs84_to_web_mercator(df, lon="LON", lat="LAT"):
      k = 6378137
      df["x"] = df[lon] * (k * np.pi/180.0)
      df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

      return df
trees_mercator = wgs84_to_web_mercator(trees,'longitude','latitude')

#Define variables
#names = trees['commonName'].unique().tolist()
trees_names = trees_mercator.groupby('commonName', axis=0, as_index=False).median()
#trees_names = trees_names_complete.drop(['commonName','treeID','latitude','longitude','utmNorthing','utmEasting','x','y'], axis=1).copy()
names = list(trees_names.index)
quantity = ColumnDataSource({'x' : names, 'y': list(trees_names['dbh'].round(decimals=2))})
# Create Select Widget menu options
trees_attributes = list(trees_names)
options=[]
for i in trees_attributes:
    string = '%s' %i
    options.append(string) 
#Create the Bar plot 
p2 = figure()
p2.vbar(x='x', top='y', source = quantity, width=0.9)
#p2.add_tools(HoverTool(tooltips=[("name", "@index"), ("height", "@height")]))
#Create the Select Widget
select_widget = Select(options = options, value = options[0], 
                title = 'Select an attribute')
#Create a function that will be called when certain attributes on a widget are changed
def callback(attr, old, new):
    column2plot = select_widget.value
    quantity.data = {'x' : names, 'y': list(trees_names[column2plot])}
    p2.vbar(x='x', top='y', source = quantity, width=0.9) 
#Update Select Widget to each interaction
select_widget.on_change('value', callback)
# Create the plot layout by merging the bar plot and the widget
layout = row(select_widget, p2)
# Display the plot
#show(layout)
#output_file(r"C:\Users\marti\OneDrive\Polimi\1 ANNO MAGISTRALE\SOFTWARE ENGINEERING FOR GEOINFORMATICS\barplot.html")
# Add the layout to the current Document displayed in the Browser
curdoc().add_root(layout)


