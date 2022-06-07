# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 14:51:57 2022

@author: marti
"""
""" IMPORTING LIBRARIES AND PACKAGES"""
# import packages needed to Perform a REST API JSON data request with Python
from psycopg2 import (connect)
from bokeh.io import output_notebook
#output_notebook()
from bokeh.resources import INLINE
output_notebook(INLINE)

"""SETTING DATABASE CONNECTION"""
#open the configuration parameter from a txt file the table
myFile = open('dbConfigTest.txt')
connStr = myFile.readline()
myFile.close()

cleanup = ('DROP TABLE IF EXISTS pa_user CASCADE','DROP TABLE IF EXISTS trees')

#variable list containing the structures of the database
commands = (
    """CREATE TABLE pa_user(email VARCHAR(255) PRIMARY KEY, firstname VARCHAR(255) NOT NULL, lastname VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL )""")

#create the connection with the database
conn = connect(connStr)
cur = conn.cursor()
for command in cleanup :
    cur.execute(command)

cur.execute(commands)
cur.close()
conn.commit()
conn.close()