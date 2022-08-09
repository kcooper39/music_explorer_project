# MusicExplorer

---

Code Base for Team Music Explorer

The project can be broken down into multiple files, each of which have a specific purpose:

- **app.py** This contains the code for creating the Dash web app which powers the application. It is used as the main script which runs everything behind the scenes (i.e. loads data from Neo4J, creates the website/design, etc.)

- **data.py** This contains helper functions which are used when retrieving data from Neo4J

- **spotify_data.py** This contains helper functions which connect to a users Spotify account, get data, etc.

- **similarity.py** This module contains the functions to provide recommendations inside the web app. Both cosine similarity and agglomerative hierarchial clustering are used

- **neo4j_connection.py** This contains a helper class to connect to a Neo4J database instance

- **assets** This folder contains required content for the Dash web app such as static CSS files, images, etc.

## Setup Instructions (Python 3.8.x)

In order to use this Dash Webapp, you will need to take a few steps in order to have access to our data. Please follow the below instructions:

**If you have a Windows machine, please refer to the instructions located in Windows installation instructions**

#### Mac OS Installation Instructions

1. Download the repository [here](https://github.gatech.edu/Zburns6/MusicExplorer/tree/master). To do so, click on **Clone or Download** and download the zip file into a directory of your choice. Unzip it once downloading is complete
   Download and Install [Neo4J desktop](https://neo4j.com/download/)
2. Open Neo4J desktop and load the dump file located [here](https://drive.google.com/file/d/1tDAoyUuTXP-v8r1kP8raTl1Hg5o1qttU/view?usp=sharing)
3. Create a new project within Neo4J called **Explorify**
4. Once the file is loaded into Neo4J, hover over the file on the RHS of the page and select **Create DBMS from Dump**
   - Name the DB: **discogs** and set the password to: **music**
5. Start the DB
6. Hover over the active database on the RHS of the page and open the Neo4J browser
7. Under the Database Information tab, go into the command line at the top and enter: :use system
8. Then enter the following command: create database discogs
9. Use the macos_requirements.txt file to create a new conda environment with all dependencies installed:
   - Inside of your terminal (Terminal for Mac or Iterm2), run: conda create --name <env> --file macos_requirements.txt
10. Inside of your terminal, navigate to the directory where you placed the github repository and then run: python3 app.py
11. Go to the http link that will be provided (probably [this](http://127.0.0.1:8050/)). If not, check the specific location inside the terminal
12. The Dash Webapp should now be functional. Please refer to the Tab sections for further instructions

### Explore Tab:

To use the explore tab, follow the below instructions:

1. Beside the search bar, select what type of entity you would like to search for (Artist, Track or Release - I.e Album)
2. Enter a search selection and press enter on your keyboard
3. Using the returned search results on the right hand side of the page, select cells from the table and use the **Add Node** button in order to add the entity to the interactive graph
4. For artists and album nodes, you can click on the node in the chart and then switch to the **Selected Data** tab (where the search results popped up) to find other associated entities

### Playlist Tab:

In order to link Spotify with the webapp, you will need to register for Spotify API credentials [here](https://developer.spotify.com/dashboard/login)

1. Sign into your spotify account. Note, this does not require a premium Spotify account.
2. Once logged in, click on **Create an App** and fill out the required information. Doing so will give you a Client ID and Client secret.
3. Once you have your Client ID and Client Secret, you will need to use this inside of the webapp. Under the Playlist tab, there will be a username box (Spotify username), client ID box and client secret box where you will use the keys generated from the link above. 4. One you are done this, review the songs you would like to add to your new Spotify playlist - Explorify. Once ready, use the buttons to add them and display visuals related to the songs you have chosen

### Content Similarity Recommendations: Cosine Similarity and Agglomerative Clustering

Explorify's recommendations are generated via Cosine Similarity and Agglomerative Clustering and thus will produce different recommendations. Use the search boxes within the tab to search for music

Additional Notes:

- There are the original A-Z.txt files which were the source for the training.

- Also, there is a sample out20000.csv which contains top 10 recs for the first 20000 songs
  as well as two IndexKey.zip files which has the total IndexKey (~60MB) including
  [Index],[title],[artist],[release]
