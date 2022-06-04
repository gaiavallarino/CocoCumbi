# import packages needed to Perform a REST API JSON data request with Python
import requests
import json
import pandas as pd
import geopandas as gpd
# import packages needed for DB connection
from sqlalchemy import create_engine
from psycopg2 import (connect)

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
