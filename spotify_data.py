""" Module for using and defining functions for the Spotipy library. Useful to connecting to the Spotify web API
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy.util as util

####################################################################################################
# Need to create a Client ID/KEY here: https://developer.spotify.com/dashboard/
# CLIENT_ID = ""
# KEY = ""
# USERNAME = ""  # defines which user to look for for music/spotify data
SCOPE = "playlist-modify-private playlist-modify-public"
####################################################################################################

# credentials = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=KEY)
# token = credentials.get_access_token()
# sp = spotipy.Spotify(auth=token)
# sp = spotipy.Spotify(
#     auth_manager=SpotifyOAuth(
#         client_id=CLIENT_ID, client_secret=KEY, scope=SCOPE, redirect_uri="http://localhost:8080"
#     )
# )

####################################################################################################


def get_artist_id(sp, artist_name):
    """ Retreieve the artist ID given an artist name. If more than one result is returned,
        we will need to implement some functionality to choose which option
    """

    query = f"{artist_name}"
    artist_results = sp.search(q=query, limit=10, type="artist")

    if len(artist_results) == 1:
        return artist_results["artists"]["items"][0]["id"]

    else:
        # TODO: not sure how this should be handled atm
        raise NotImplementedError()


def get_song_data(sp, track, artist):
    """ Retreive song/track name/ID given its name and artist
    """
    if "'" in track:
        track = track.replace("'", "")

    if "'" in artist:
        artist = artist.replace("'", "")

    query = f"artist:{artist} track:{track}"
    track_results = sp.search(q=query, limit=1)

    if len(track_results["tracks"]["items"]) == 1:
        data = track_results["tracks"]["items"][0]
        track_id, track_name = data["id"], data["name"]

        return {"track_id": track_id, "track_name": track_name}
    else:
        return None


def get_album_tracks(sp, album_id):
    """
        Params:
            sp: Spotipy object
            album_id: list of album_ids
    """
    if len(album_id) > 1:
        raise NotImplementedError()

    track_ids = []

    results = sp.albums(album_id)
    album_tracks = results["albums"][0]["tracks"]["items"]

    for track in range(len(album_tracks)):
        track_ids.append(album_tracks[track]["id"])

    return track_ids


def create_playlist(sp, username, playlist_name="explorify", public=True, collaborative=False):
    """ Create a new playlist for a user given their username

        Params:
            sp: Spotipy Object
            username: string username
    """
    playlist_info = sp.user_playlist_create(
        username, playlist_name, public=public, collaborative=collaborative
    )
    return playlist_info["id"]


def add_song_to_playlist(sp, username, playlist_id, tracks):
    """ Add song(s) to a users playlist

        Params:
            - sp: Spotipy Object
            - username: username of user
            - playlist_name: name of users playlist
            - tracks: list of song ID's to add
    """
    sp.user_playlist_add_tracks(username, playlist_id, tracks)
    return None


def collect_data(sp, artist_song_data):
    """ Take in a list of Tuples (Artist Name, Track Name) get required information.
        This function serves as a main function to aggregate artist/song/data
    """
    ids = []
    songs_not_added = []
    for row in artist_song_data:
        artist, song = row["Artist"], row["Song"]
        song_data = get_song_data(sp, song, artist)
        if song_data is not None:
            ids.append(song_data)

        else:
            songs_not_added.append((artist, song))

    return ids, songs_not_added


def get_audio_features(sp, track_names, track_list):
    """ Get Spotify audio features given a list of track ids

        Params:
            track_list: List of Track ID's
    """

    feats = sp.audio_features(track_list)


####################################################################################################
# Testing function calls to the Spotify API

# artist_id = get_artist_id(sp, "red hot chilli peppers")
# song_data = get_song_data(sp, "cant stop", "red hot chilli peppers")
# playlist_id = "59s4unXp4PYkCnFqRkKkwy"
# add_song_to_playlist(sp, "zacburns", playlist_id, [song_data["track_id"]])
# album_id = "7xl50xr9NDkd3i2kBbzsNZ"
# track_ids = get_album_tracks(sp, [album_id])


# if __name__ == '__main__':
