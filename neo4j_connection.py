""" This is the base module for the Explorify Web App

Notes:
    - When setting up your Neo4j instance, default user: neo4j and password neo4j
    - You will need to set up a password after creating a DB to hold the discogs data
        - Once this is set, to access that DB using the driver, you will need user: neo4j and the password you set for this Db

"""

from neo4j import GraphDatabase


EXPLORIFY_KEY = "music"
PORT = "7687"  #### Make sure to change port according to Neo4j desktop instance


class Neo4jConnection:
    """ Class to help connecting to a Neo4j DB instance

        TODO: See if we can add functionality to tear down/spin up the Neo4J instance
            - This might need to be done through the CLI rather than Python
    """

    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, db=None):
        """ Query a given database from Neo4j

            Params:
                - query: Cypher QL query to match against nodes/relationships in the DB
        """
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = (
                self.__driver.session(database=db) if db is not None else self.__driver.session()
            )
            response = list(session.run(query))

        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response


conn = Neo4jConnection(uri=f"bolt://localhost:{PORT}", user="neo4j", pwd=EXPLORIFY_KEY)

test = """
MATCH (n:Track)
where exists(n.artistID)
return n limit 50
"""
test = conn.query(test, db="discogs")

get_artists = """
MATCH (n:Artist)
where n.` name` starts with 'a'
return n limit 25
"""

res = conn.query(get_artists, db="discogs")
# res2 = conn.query(get_tracks, db="discogs")[0]


############## Accessing Results
# res['n'].keys() to access properties
# res['n'].labels to get type of Node
