""" Module for retreiving data from from Neo4J DB
"""
from neo4j_connection import Neo4jConnection
import pandas as pd
import json

def artist_nodes_to_df(results):
    df = [{"Artist" : result['a'][' name'],
    "id" : result["a"]["artistID"],
    "label": "Artist"} for result in results]
    df = pd.DataFrame(df)
    return(df)

def artist_credit_nodes_to_df(results):
    df = [{"label": "Artist",
    "Artist" : result['a'][' name'],
    "id" : result["a"]["artistID"],
    "Credit" : result["c"]["role"],
    "Track" : result["t"][" title"]} for result in results]
    df = pd.DataFrame(df)
    return(df)

def release_nodes_to_df(results):
    df = [{"Artist" : result['a'][' name'],
    "Release" : result['r'][' title'],
    "id" : result['r']['releaseId'],
    "label": "Release"} for result in results]
    df = pd.DataFrame(df)
    return(df)

def track_nodes_to_df(results):
    df = [{"Track": result['t'][' title'], 
    "Artist" : result['a'][' name'],
    "Release" : result['r'][' title'],
    "id" : result['t']['trackId'],
    "label": "Track"}
    for result in results]
    df = pd.DataFrame(df)
    return(df)

#def release_nodes_to_df(nodes):
    
    

def get_search_results(connection, sterm, stype):
    #Should implement index/contains with all node types
    if stype == "Artist":
        cypher_query = f"""
        MATCH (a:Artist)
        WHERE a.` name` CONTAINS '{sterm}'
        RETURN DISTINCT a
        """    
        results = connection.query(cypher_query, db="discogs")
        return artist_nodes_to_df(results)
    elif stype == "Track":
        cypher_query = f"""
        MATCH (r:Release)<-[:in_tracklist]-(t:Track)-[:Main]-(a:Artist)
        WHERE t.` title` CONTAINS '{sterm}'
        RETURN DISTINCT t, a, r
        """ 
        
        results = connection.query(cypher_query, db="discogs")
        return track_nodes_to_df(results)
    elif stype == "Release":
        cypher_query = f"""
        MATCH (r:Release)<-[:in_tracklist]-(t:Track)-[:Main]-(a:Artist)
        WHERE r.` title` CONTAINS '{sterm}'
        RETURN DISTINCT a, r
        """    
        results = connection.query(cypher_query, db="discogs")
        return release_nodes_to_df(results)


def get_artist_releases(connection, artistID):
    """ Return Tracks/Albums connected to a given artistID
    """
    # Find all relationships (Main, Extra or In-Tracklist) with a given artist
    cypher_query = f"""
    MATCH (a:Artist)-[m:Main]->(Track)-[:in_tracklist]->(r:Release) 
    WHERE a.`artistID` = "{artistID}"
    return DISTINCT a, r
    """
    results = connection.query(cypher_query, db="discogs")
    return release_nodes_to_df(results)


def get_release_tracklist(connection, releaseId):
    # Find all relationships (Main, Extra or In-Tracklist) with a given artist
    cypher_query = f"""
    MATCH (a:Artist)-[:Main]->(t:Track)-[:in_tracklist]->(r:Release) 
    WHERE r.`releaseId` = "{releaseId}"
    return DISTINCT t, a, r
    """
    results = connection.query(cypher_query, db="discogs")
    return track_nodes_to_df(results)


def get_track_artists(connection, trackId):
    cypher_query = f"""
    MATCH (a:Artist)-[c:Main|Extra]->(t:Track)
    WHERE t.`trackId` = "{trackId}"
    return DISTINCT a, c, t
    """
    results = connection.query(cypher_query, db="discogs")
    return artist_credit_nodes_to_df(results)
    

def parse_artist_nodes(results):
    """ Function to parse a list of returned nodes that contain Artist and Track Nodes/relationships.
        Need to construct a list of nodes and edges to build the cytoscape viz

        Params:
            - results: List of Records which contain Node objects
    """
    cy_nodes = []
    cy_edges = []
    nodes = set()

    for indx, node in enumerate(results):
        source, target = node["a"][" name"], node["r"][" title"]

        if indx == 0:
            class_label = "Artist"
        else:
            class_label = "Release"

        # Use classes to distinguish between Artist Nodes and Track/Release Nodes so we can style
        if source not in nodes:
            nodes.add(source)
            cy_nodes.append({"data": {"id": source, "label": source}, "classes": class_label})

        if target not in nodes:
            nodes.add(target)
            cy_nodes.append({"data": {"id": target, "label": target}, "classes": "Release"})

        cy_edges.append({"data": {"source": source, "target": target}})

    return cy_nodes + cy_edges


if __name__ == "__main__":
    #CALL db.indexes()
    EXPLORIFY_KEY = "music"
    PORT = "7687"  #### Make sure to change port according to Neo4j desktop instance
    conn = Neo4jConnection(uri=f"bolt://localhost:{PORT}", user="neo4j", pwd=EXPLORIFY_KEY)
   
