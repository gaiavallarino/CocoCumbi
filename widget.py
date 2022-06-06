# -*- coding: utf-8 -*-
"""
Created on Sun May 29 23:31:51 2022

@author: marti
"""


""" IMPORTING LIBRARIES AND PACKAGES"""
import geopandas as gpd
from bokeh.models import ColumnDataSource, Select
from bokeh.plotting import figure
from bokeh.io import curdoc, output_notebook
from bokeh.layouts import row
#output_notebook()
from bokeh.resources import INLINE
output_notebook(INLINE)
#from connection import insert_df
from connection import engine
#from prova import trees


"""IMPORTING DATA"""
# import geo data
#engine = insert_df()
trees = gpd.GeoDataFrame.from_postgis('trees', engine, geom_col='geometry')
trees = trees.drop('geometry', axis=1).copy()# save a copy of the GeoDataFrame in a new DataFrame by dropping the 'geometry' column


"""BARPLOT"""
#Define variables
#names = trees['commonName'].unique().tolist()
trees_names = trees.groupby('commonName', axis=0, as_index=False).median()
trees_names = trees_names.drop(['commonName','treeID','latitude','longitude','x','y'], axis=1).copy()
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


