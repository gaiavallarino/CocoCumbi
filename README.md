# 1.INTRODUCTION

The <u><b>Coco Cumbi</b></u> software is born as the main deliverable of the <b>Software Engineering for Geoinformatics</b> course of the <i>POLIMI M.Sc. in Geoinformatics Engineering</i>.

Coco Cumbi is a software built in aid of Public Administrations' environmental departments, in order to help in the decision-making process, by deploying queries, statistics and visualization of a tree census dataset. 

The accompaning documentation can be found in this repository and documents better the scope, plan, purpose, testing and implementation of the software, better that a readme file could ever do.

The team of developers is composed by the following people who mainly operated in the following roles:
- <b>Stefano Brazzoli</b>, <i>back-end developer</i>
- <b>Martina Giovanna Esposito</b>, <i>back-end developer</i>
- <b>Mattia Koren</b>, <i>full-stack developer</i>
- <b>Gaia Vallarino</b>, <i>front-end developer</i>

# 2.INSTRUCTIONS

## 2.1.DESCRIPTION OF THE FILES
This repository contains all the files needed in order to run the application:
- `static`: this folder contains the css and all the assets for the html files
- `templates`: this folder contains all html files
- `CocoCumbi.py`: this is the main python code with functions and flask application
- `connection.py`: this is the necessary python code to create databases, to import data from epicollect and to fix the data georeferencing them and removing wrong                          elements
- `map_correct.py`: this is the python code for the interactive map
- `widget.py`: this is the python code for the barplot
- `dbConfigTest.txt`:in this txt you need to change user and password with your personal credentials
## 2.2 HOW TO RUN THE APP
-To run the Cococumbi Web Application you need to :
   - have postgreSQL-postGIS installed on your computer
   - have an Anaconda environment with the following libraries installed:
        - flask
        - geopandas
        - spyder 
        - sqlalchemy
        - psycoppg2
        - bokeh
        - json
        - pandas
   - modify dbConfigTest.txt file inserting the name of you're postgreSQL database, username and password
   - launch the Cococumbi.py script
   - open the browser at http:\127.0.0.1:5000
   - login/register to the Cococumbi WebApp, for the registration you need to use an account from Politecnico di Milano. (with the domain @mail.polimi.it)
