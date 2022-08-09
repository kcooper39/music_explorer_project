# Import external dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output, State

import dash_cytoscape as cyto
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import time

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials

# Import files from working directory
from neo4j_connection import Neo4jConnection
from data import get_search_results, get_artist_releases, get_release_tracklist, get_track_artists
from spotify_data import (
    collect_data,
    get_song_data,
    add_song_to_playlist,
    create_playlist,
    get_album_tracks,
    get_artist_id,
    get_audio_features,
)
from similarity import get_song_recommendations, get_clustering_recommendations

##############################################################################################################
# Set up Connection to Neo4j DB
EXPLORIFY_KEY = "music"
PORT = "7687"  #### Make sure to change port according to Neo4j desktop instance
conn = Neo4jConnection(uri=f"bolt://localhost:{PORT}", user="neo4j", pwd=EXPLORIFY_KEY)
conn.query("CREATE INDEX IF NOT EXISTS FOR (t:Track) ON (t.` title`)", db="discogs")
conn.query("CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.` name`)", db="discogs")
conn.query("CREATE INDEX IF NOT EXISTS FOR (r:Release) ON (r.` title`)", db="discogs")
conn.query("CREATE INDEX IF NOT EXISTS FOR (t:Track) ON (t.trackId)", db="discogs")
conn.query("CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.artistID)", db="discogs")
conn.query("CREATE INDEX IF NOT EXISTS FOR (r:Release) ON (r.releaseId)", db="discogs")


##############################################################################################################
# Spotify/Spotipy Setup

# Need to create a Client ID/KEY here: https://developer.spotify.com/dashboard/
SCOPE = "playlist-modify-private playlist-modify-public"
token = None  # Setup for OAuth token for spotify
##############################################################################################################
# Song Recommendations
PATH = "dataset/"

# Need to create a Client ID/KEY here: https://developer.spotify.com/dashboard/
SCOPE = "playlist-modify-private playlist-modify-public"
token = None  # Setup for OAuth token for spotify
##############################################################################################################
# Song Recommendations
PATH = "dataset/"

##############################################################################################################
# Test Data: to remove later

test_data = [
    ("The Beatles", "Here There And Everywhere"),
    ("Red Hot Chili Peppers", "Can't Stop"),
    ("Buckcherry", "Sorry"),
    ("Percy X", "Soul Glo"),
    ("Percy X", "As Is"),
    ("Percy X", "On a Day"),
]
test_df = pd.DataFrame(test_data, columns=["Artist", "Song"])

##############################################################################################################
# Dash App Configurations

# Set up Dash App
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

stylesheet = [
    {
        "selector": "node",
        "style": {
            "width": "data(node_size)",
            "height": "data(node_size)",
            "content": "data(label)",
            "font-size": "3px",
            "text-valign": "center",
            "text-halign": "center",
            "line-break": "anywhere",
            # "word-break": "break-all",
            # "background-color": "#03fc66",  # node color
        },
    },
    {"selector": "edge", "style": {"line-color": "#033dfc",},},  # For all edges  # edge color
    {"selector": ".Artist", "style": {"background-color": "#4db4d7"},},
    {"selector": ".Track", "style": {"background-color": "#4076be"},},
    {"selector": ".Release", "style": {"background-color": "#48bf91"}},
]

##############################################################################################################
# Helper Elements to simplify body layout

# Landing spot for radar chart in the playlist tab
radar_chart_audio_analysis = dbc.Card(
    [
        dbc.CardHeader("Audio Profile Analysis", className="card_header"),
        dbc.CardBody(children=[], id="radar_chart_container"),
    ],
    color="primary",
    inverse=True,
)

# Header for webapp
header = html.Div(
    id="app-header",
    children=[
        html.Img(src=app.get_asset_url("dash-logo.png"), className="plotly-logo"),
        html.H1(
            "Explorify: Music Discovery Platform",
            style={"display": "inline-block"},
            id="title-text",
        ),
    ],
)

# Search bars for recommendations tab
form = dbc.Form(
    [
        dbc.FormGroup(
            [
                dbc.Label("Album", className="mr-2"),
                dbc.Input(type="search", placeholder="Enter an album", id="album_search"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Artist", className="mr-2"),
                dbc.Input(type="search", placeholder="Enter an artist", id="artist_search"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Track", className="mr-2"),
                dbc.Input(type="search", placeholder="Enter a song", id="track_search"),
            ],
            className="mr-3",
        ),
        dbc.Button("Search", color="primary", id="submit_button"),
    ],
    inline=True,
)

# Container for cosine similarity recommendations
cosine_sim_recommendations_container = dbc.Card(
    [
        dbc.CardHeader("Content Similarity: Recommendations", className="card_header"),
        dbc.CardBody(children=[], id="cosine_sim_recommendations"),
    ],
    color="primary",
    inverse=True,
)

clustering_recommendations_container = dbc.Card(
    [
        dbc.CardHeader("Agglomerative Clustering: Recommendations", className="card_header"),
        dbc.CardBody(children=[], id="clustering_recommendations"),
    ],
    color="primary",
    inverse=True,
)

##############################################################################################################
# Dash Content Body

app.layout = html.Div(
    children=[
        header,
        html.Div(id="graph_data", style={"display": "none"}, title="[]"),
        html.Br(),
        html.Div(
            [
                dcc.Tabs(
                    id="explore-tabs",
                    value="explore",
                    children=[
                        dcc.Tab(
                            label="Explore",
                            value="explore",
                            children=[
                                html.Br(),
                                dbc.Row(
                                    children=[
                                        dcc.Input(
                                            id="searchbar",
                                            placeholder="Enter a track, release, or artist here",
                                            type="search",
                                            debounce=True,
                                            style={"width": "35em", "display": "inline-block"},
                                        ),
                                        dcc.RadioItems(
                                            id="search-option",
                                            options=[
                                                {"label": "Track", "value": "Track"},
                                                {"label": "Artist", "value": "Artist"},
                                                {"label": "Release", "value": "Release"},
                                            ],
                                            value="artist",
                                            labelStyle={"display": "inline-block"},
                                            style={"display": "inline-block"},
                                        ),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("Add Node", id="add-node-button"),
                                                dbc.Button("Remove Node", id="remove-node-button"),
                                            ]
                                        ),
                                    ]
                                ),
                                # placeholder for graph/search content
                                html.Div(
                                    className="eight columns",
                                    children=[
                                        cyto.Cytoscape(
                                            id="cytoscape-viz",
                                            # good layout options: 'cose', 'cytoscape-cose-bilkent'
                                            layout={"name": "cose"},
                                            style={"width": "100%", "height": "75vh"},
                                            zoom=0.01,
                                            maxZoom=10,
                                            minZoom=0,
                                            elements=[],
                                            stylesheet=stylesheet,
                                        )
                                    ],
                                ),
                                html.Div(
                                    className="four columns",
                                    style={"backgroundColor": "white"},
                                    children=[
                                        dcc.Tabs(
                                            id="graph-tabs",
                                            value="search_results",
                                            children=[
                                                dcc.Tab(
                                                    label="Search Results",
                                                    value="search_results",
                                                    children=[
                                                        html.Br(),
                                                        html.Div(
                                                            id="search_results",
                                                            children=[
                                                                dash_table.DataTable(
                                                                    id="table",
                                                                    columns=[
                                                                        {
                                                                            "name": "Search Results Will Appear Here",
                                                                            "id": "Search Results",
                                                                        }
                                                                    ],
                                                                    style_header={
                                                                        "textAlign": "center"
                                                                    },
                                                                    data=None,
                                                                    active_cell=None,
                                                                )
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                dcc.Tab(
                                                    label="Selected Data",
                                                    value="node_data",
                                                    children=[
                                                        html.Br(),
                                                        html.Div(
                                                            id="selected-node-table",
                                                            children=[
                                                                dash_table.DataTable(
                                                                    id="selected-node-info",
                                                                    columns=[
                                                                        {
                                                                            "name": "Selected Node Info Will Appear Here",
                                                                            "id": "Selected Node Info",
                                                                        }
                                                                    ],
                                                                    style_header={
                                                                        "textAlign": "center"
                                                                    },
                                                                    data=None,
                                                                    active_cell=None,
                                                                )
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),
                        dcc.Tab(
                            label="Playlist",
                            value="playlist",
                            children=[
                                html.Br(),
                                html.Div(
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Input(
                                                        id="username_box",
                                                        className="credentials_box",
                                                        placeholder="Spotify Username",
                                                        persistence=True,
                                                        type="text",
                                                        size="15",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dcc.Input(
                                                        id="client_id_box",
                                                        className="credentials_box",
                                                        placeholder="Spotify API ClientID",
                                                        persistence=True,
                                                        type="text",
                                                        size="30",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dcc.Input(
                                                        id="client_secret_box",
                                                        className="credentials_box",
                                                        placeholder="Spotify API ClientID Secret",
                                                        persistence=True,
                                                        type="password",
                                                        size="30",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    html.Button(
                                                        "Click to Connect To Spotify",
                                                        id="log_in_button",
                                                        className="mobile_buttons",
                                                    ),
                                                    width="auto",
                                                ),
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Br(),
                                                        # placeholder for spotify connection
                                                        html.Div(id="auth_text", children=[]),
                                                    ]
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                                html.Br(),
                                html.Div(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    # TODO Later: https://stackoverflow.com/questions/12139546/text-color-change-on-hover-over-button
                                                    html.Button(
                                                        "Add songs to Spotify playlist",
                                                        id="add_to_spotify",
                                                        className="mobile_buttons",
                                                    ),
                                                    width={"size": 2},
                                                ),
                                                dbc.Col(
                                                    dcc.Loading(
                                                        id="add_songs_to_playlist_loading",
                                                        type="default",
                                                        children=[
                                                            html.Div(
                                                                id="loading-output-1",
                                                                style={"margin-top": "5%"},
                                                            )
                                                        ],
                                                    ),
                                                    width={"size": 2},
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        children=[],
                                                        id="spotify_connect_text",
                                                        style={"display": "inline-block"},
                                                    )
                                                ),
                                            ],
                                            no_gutters=True,
                                        ),
                                        html.Br(),
                                        dash_table.DataTable(
                                            id="playlist_table",
                                            data=test_df.to_dict("rows"),
                                            columns=[{"name": i, "id": i} for i in test_df.columns],
                                            style_header={
                                                "fontWeight": "bold",
                                                "backgroundColor": "white",
                                            },
                                            style_cell={
                                                "fontFamily": "Open Sans",
                                                "textAlign": "center",
                                                # "padding": "2px 22px",
                                                "whiteSpace": "inherit",
                                                "overflow": "hidden",
                                                "textOverflow": "ellipsis",
                                            },
                                            row_deletable=True,
                                        ),
                                        html.Br(),
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    id="playlist_data",
                                                    children=[],
                                                    style={"float": "left"},
                                                )
                                            )
                                        ),
                                    ],
                                ),
                                html.Div(
                                    children=[
                                        dbc.Row(dbc.Col(html.H3("Audio Analysis Visualization"))),
                                        html.Br(),
                                        dbc.Row(dbc.Col(radar_chart_audio_analysis, width=6)),
                                    ],
                                    id="song-viz",
                                ),
                                html.Br(),
                            ],
                        ),
                        dcc.Tab(
                            label="Recommendations",
                            value="recommendations",
                            children=[
                                html.Br(),
                                html.Div(
                                    id="recommendations_container",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(form, width={"size": 6}),
                                                dbc.Col(
                                                    dcc.Loading(
                                                        id="recommendations_loading",
                                                        type="default",
                                                        children=[
                                                            html.Div(
                                                                id="recommendations_loading_output",
                                                                style={
                                                                    "display": "inline-block",
                                                                    "margin-top": "8%",
                                                                },
                                                            )
                                                        ],
                                                    ),
                                                    width={"size": 2},
                                                ),
                                            ]
                                        ),
                                        html.Br(),
                                        html.Br(),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    cosine_sim_recommendations_container,
                                                    width={"size": 5},
                                                ),
                                                dbc.Col(
                                                    clustering_recommendations_container,
                                                    width={"size": 5},
                                                ),
                                            ],
                                            justify="between",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="eleven columns",
        ),
    ]
)

##############################################################################################################
# Callbacks for Interactivity


@app.callback(Output("selected-node-table", "children"), Input("cytoscape-viz", "tapNode"))
def node_display(node):
    if node is None:
        return dash.no_update
    if node["classes"] in "Artist":
        results = get_artist_releases(conn, node["data"]["id"])
    if node["classes"] in "Release":
        results = get_release_tracklist(conn, node["data"]["id"])
    if node["classes"] in "Track":
        results = get_track_artists(conn, node["data"]["id"])
    table = dash_table.DataTable(
        id="selected-node-info",
        columns=[{"name": i, "id": i} for i in results.columns],
        data=results.to_dict("records"),
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "height": "auto",
            # all three widths are needed
            "minWidth": "180px",
            "width": "180px",
            "maxWidth": "180px",
            "whiteSpace": "normal",
        },
        style_cell_conditional=[{"if": {"column_id": c}, "display": "none"} for c in ["id"]],
    )
    return table


@app.callback(
    Output("graph_data", "title"),
    Input("add-node-button", "n_clicks"),
    Input("remove-node-button", "n_clicks"),
    State("graph_data", "title"),
    State("table", "active_cell"),
    State("table", "data"),
    State("cytoscape-viz", "selectedNodeData"),
    State("selected-node-info", "data"),
    State("selected-node-info", "active_cell"),
    State("graph-tabs", "value"),
)
def edit_graph(
    add_clicks,
    rm_clicks,
    graph_data,
    search_row,
    search_data,
    sel_node,
    node_tab,
    node_row,
    graph_tabs,
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return graph_data
    else:
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if "add-node-button" in trigger:
        if search_row is None and node_row is None:
            return graph_data
        if graph_tabs in "search_results":
            nodes = [node for node in search_data if node["id"] in search_row["row_id"]]
        elif graph_tabs in "node_data":
            nodes = [node for node in node_tab if node["id"] in node_row["row_id"]]
        new_nodes = []
        elements = json.loads(graph_data)
        el_nodes = [el for el in elements if el["data"].get("id", None) is not None]
        for node in nodes:
            if node["label"] == "Artist":
                new_node = {
                    "data": {"id": node["id"], "label": node["Artist"]},
                    "classes": node["label"],
                }
                edges = [
                    {"data": {"source": el["data"]["id"], "target": node["id"]}}
                    for el in el_nodes
                    if node.get("Track", "a9*1n0") in el["data"]["label"]
                ]
                new_nodes.append(new_node)
            elif node["label"] == "Track":
                new_node = {
                    "data": {"id": node["id"], "label": node["Track"]},
                    "classes": node["label"],
                }
                edges = [
                    {"data": {"source": el["data"]["id"], "target": node["id"]}}
                    for el in el_nodes
                    if node.get("Release", "") in el["data"]["label"]
                ]
                new_nodes.append(new_node)
            elif node["label"] == "Release":
                new_node = {
                    "data": {"id": node["id"], "label": node["Release"]},
                    "classes": node["label"],
                }
                edges = [
                    {"data": {"source": el["data"]["id"], "target": node["id"]}}
                    for el in el_nodes
                    if node.get("Artist", "") in el["data"]["label"]
                ]
                new_nodes.append(new_node)
        elements = elements + new_nodes + edges
        elements = json.dumps(elements)
        return elements
    elif "remove-node-button" in trigger:
        graph_data = json.loads(graph_data)
        graph_data = [el for el in graph_data if el["data"] != sel_node[0]]
        graph_data = [
            el
            for el in graph_data
            if str(el["data"].get("source", "bloop")) not in str(sel_node[0]["id"])
        ]
        graph_data = [
            el
            for el in graph_data
            if str(el["data"].get("target", "bloop")) not in str(sel_node[0]["id"])
        ]
        return json.dumps(graph_data)


@app.callback(Output("cytoscape-viz", "elements"), Input("graph_data", "title"))
def get_graph_data(data):
    data = json.loads(data)
    return data


@app.callback(
    Output("search_results", "children"),
    Input("searchbar", "value"),
    Input("search-option", "value"),
)
def render_content(search_term, search_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    else:
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if "search" in trigger:
        results = search(search_term, search_type)
        return results


def search(search_term, search_type):
    if search_term == "":
        return dash.no_update
    search_results = get_search_results(conn, search_term, search_type)
    if search_results is None:
        return dash.no_update
    cols = [{"name": i, "id": i} for i in search_results.columns]
    table = dash_table.DataTable(
        id="table",
        columns=cols,
        data=search_results.to_dict("records"),
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "height": "auto",
            # all three widths are needed
            "minWidth": "180px",
            "width": "180px",
            "maxWidth": "180px",
            "whiteSpace": "normal",
        },
        style_cell_conditional=[{"if": {"column_id": c}, "display": "none"} for c in ["id"]],
    )
    return table


##############################################################################################################
# Callbacks for spotify/spotipy related functionality
@app.callback(
    Output("auth_text", "children"),
    [Input("log_in_button", "n_clicks")],
    state=[
        State("username_box", "value"),
        State("client_id_box", "value"),
        State("client_secret_box", "value"),
    ],
)
def authenticate_spotify(n_clicks, username, client_id, client_secret):
    """ When the button is clicked, spotify will open a new tab to authorize user login so we can
        connect to their account. User/password boxes will server as how we connect other users
        to their Spotify API data
    """
    # Set access token to global variable so we can use elsewhere in the program
    # We can use these tokens to connect to the web API
    global token
    if n_clicks:
        token = util.prompt_for_user_token(
            str(username),
            SCOPE,
            client_id=str(client_id),
            client_secret=str(client_secret),
            redirect_uri="http://localhost:8080",
        )

    if token:
        return "Authentication Succesful. Currently connected to Spotify API"
    else:
        return "Currently not connected to Spotify API"


# Spotify Auth Related Functions
def create_spotipy_object():
    global token
    return spotipy.Spotify(auth=token)


##############################################################################################################
# Callbacks for Playlist tab


@app.callback(Output("loading-output-1", "children"), Input("add_to_spotify", "n_clicks"))
def input_triggers_spinner(n_clicks):
    """ Function to display loading graphic when adding to Spotify since it may take a few seconds
    """
    return None


@app.callback(
    [Output("spotify_connect_text", "children"), Output("radar_chart_container", "children")],
    Input("add_to_spotify", "n_clicks"),
    State("playlist_table", "data"),
    State("username_box", "value"),
)
def add_content_to_spotify_playlist(n_clicks, data, value):
    """ Callback for taking in Dash DataTable (updated version) and adding these
        song/artist pairs to the users spotify playlist

        Params:
            n_clicks: number of clicks logged for the button
            data: List of dictionaries passed from the DataTable
            value: Value of username from the username_box
    """
    if n_clicks is None:
        return [None, None]
    else:
        sp = create_spotipy_object()
        track_info, songs_not_added = collect_data(sp, data)
        track_ids = [t["track_id"] for t in track_info]

        # If tracks are returned from the collect_data() method, create a spotify playlist
        if len(track_ids) >= 1:
            playlist_id = create_playlist(sp, value)

            try:
                add_song_to_playlist(sp, username=value, playlist_id=playlist_id, tracks=track_ids)
            except spotipy.SpotifyException as e:
                pass

        songs_added_element = html.Div(
            [
                html.H3(
                    f"{len(track_ids)} songs were added to your playlist explorify",
                    style={"font-size": 24},
                ),
            ]
        )

        radar_chart = html.Div(
            dcc.Graph(figure=create_audio_analysis_radar_chart(sp, track_info)), id="radar_chart"
        )

        return [songs_added_element, radar_chart]


def create_audio_analysis_radar_chart(sp, track_info):
    """ Function to get audio features for a list of track ids and create a radar chart

        Params:
            sp: Spotipy Object
            track_info: List of dictionaries containing track id, track name:
                - i.e. [{'track_id': '3vS1YWv3FAaKqYsTP4hlV2', 'track_name': 'Soul Glo'}, ...]

    """

    # define which audio features we want to display. Note: all of these have a range between 0 and 1
    audio_feature_names = ["danceability", "energy", "speechiness", "acousticness", "valence"]

    # Get only the track ids so we can use the spotipy function to get audio features
    track_id_list = [track["track_id"] for track in track_info]
    audio_features = sp.audio_features(track_id_list)

    # Combine info together so we can interate through and access each songs relevant data
    data = list(zip(track_info, audio_features))

    traces = []  # list to hold all trace objects
    for song_info, features in data:

        danceability = features["danceability"]
        energy = features["energy"]
        speechniness = features["speechiness"]
        acousticness = features["acousticness"]
        valence = features["valence"]

        feats = [danceability, energy, speechniness, acousticness, valence]
        scatterpolar_objs = go.Scatterpolar(
            r=feats, theta=audio_feature_names, fill="toself", name=song_info["track_name"]
        )
        traces.append(scatterpolar_objs)

    # Get unique tracks for buttons in the radar chart
    unique_tracks = [track["track_name"] for track in track_info]
    num_tracks = len(unique_tracks)

    # Create buttons for the dropdown + default one showing all layered on top of each other
    bool_list = [True] * num_tracks
    buttons = [
        dict(
            label="All",
            method="update",
            args=[{"visible": bool_list}, {"title": "Audio Profile: All Songs"}],
        )
    ]

    for indx, track in enumerate(unique_tracks):

        visible_bool = [False] * num_tracks
        visible_bool[indx] = True

        buttons.append(
            dict(label=track, method="update", args=[{"visible": visible_bool}, {"title": track}])
        )

    # Bsae object for plotly chart
    fig = go.Figure(traces)

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        updatemenus=[dict(active=0, buttons=buttons)],
    )

    return fig


###################################################################################################################
# Callbacks for recommendations tab


@app.callback(
    Output("recommendations_loading_output", "children"), Input("submit_button", "n_clicks")
)
def music_recommendations_loading(n_clicks):
    """ Function to display loading graphic when adding to Spotify since it may take a few seconds
    """
    if n_clicks:
        time.sleep(5)
    return None


@app.callback(
    Output("cosine_sim_recommendations", "children"),
    Input("submit_button", "n_clicks"),
    [
        State("album_search", "value"),
        State("artist_search", "value"),
        State("track_search", "value"),
    ],
)
def display_cosine_sim_recommendations(n_clicks, album, artist, track):
    """ Take in album,  artist and track info from the search bar and get top 5 recommendations
    """
    if n_clicks:

        recommendations = get_song_recommendations(album=album, artist=artist, track=track)

        df = pd.DataFrame(recommendations)
        df.columns = ["Title", "Artist Name", "Release"]

        table = html.Div(
            dash_table.DataTable(
                id="cosine_recs_table",
                data=df.to_dict("rows"),
                columns=[{"name": i.title(), "id": i} for i in df.columns],
                style_header={
                    "fontFamily": "Open Sans",
                    "fontWeight": "bold",
                    "backgroundColor": "white",
                },
                style_cell={
                    "fontFamily": "Open Sans",
                    "color": "black",
                    "textAlign": "center",
                    # "padding": "2px 22px",
                    "whiteSpace": "inherit",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            ),
            id="recommendations_table_div",
        )
        return table


@app.callback(
    Output("clustering_recommendations", "children"),
    Input("submit_button", "n_clicks"),
    [
        State("album_search", "value"),
        State("artist_search", "value"),
        State("track_search", "value"),
    ],
)
def display_clustering_recommendations(n_clicks, album, artist, track, path=PATH):
    """ Function to display and retreieve the agglomerative clustering recommendations
    """
    if n_clicks:
        recommendations = get_clustering_recommendations(
            album=album, artist=artist, track=track, path=path
        )
        if not recommendations.empty:

            table = html.Div(
                dash_table.DataTable(
                    id="clustering_recs_table",
                    data=recommendations.to_dict("rows"),
                    columns=[{"name": i, "id": i} for i in recommendations.columns],
                    style_header={
                        "fontFamily": "Open Sans",
                        "fontWeight": "bold",
                        "backgroundColor": "white",
                    },
                    style_cell={
                        "fontFamily": "Open Sans",
                        "color": "black",
                        "textAlign": "center",
                        # "padding": "2px 22px",
                        "whiteSpace": "inherit",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                ),
                id="clustering_recs_table_div",
            )
            return table

        return html.P("Sorry we cannot find that input", style={"color": "white"})


###################################################################################################################

if __name__ == "__main__":
    app.run_server(debug=True)
