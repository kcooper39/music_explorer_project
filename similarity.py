import pandas as pd
import string
import numpy as np
import random

from scipy.spatial import distance
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler

PATH = "dataset/"


def get_song_recommendations(artist=None, album=None, track=None, index=0, path=PATH):

    reclist = (
        pd.concat(
            (
                pd.read_csv(f"{path}SimMatrix1.csv"),
                pd.read_csv(f"{path}SimMatrix2.csv"),
                pd.read_csv(f"{path}SimMatrix3.csv"),
            )
        )
        .reset_index(drop=True)
        .drop("idx", axis=1)
    )
    idxlist = (
        pd.concat(
            (
                pd.read_csv(f"{path}idxmapper1.csv"),
                pd.read_csv(f"{path}idxmapper2.csv"),
                pd.read_csv(f"{path}idxmapper3.csv"),
            )
        )
        .reset_index(drop=True)
        .drop("idx", axis=1)
    )

    idxmapper = idxlist.copy()

    if album:
        album = album.title()
        idxs = idxmapper.index[idxmapper["release"].str.contains(album, regex=False)]
        rand_song = np.random.choice(idxs)
    elif track:
        track = track.title()
        idxs = idxmapper.index[idxmapper["title"].str.contains(track, regex=False)]
        rand_song = np.random.choice(idxs)
    elif artist:
        artist = artist.title()
        idxs = idxmapper.index[idxmapper["artist_name"].str.contains(artist, regex=False)]
        rand_song = np.random.choice(idxs)
    else:
        rand_song = index

    shortlist = list(set(reclist.iloc[rand_song]))
    recommendations = [idxmapper.iloc[rec] for rec in shortlist]

    return recommendations


###################################################################################################################
# Agglomerative Clustering recommendations


def load_and_process_cluster_labels(path):
    clusters = pd.read_csv(f"{path}agglomerative_clustering_labels.csv", index_col=0)

    cond1 = clusters["title"].notnull()
    cond2 = clusters["artist_name"].notnull()
    cond3 = clusters["release"].notnull()

    clusters = clusters[cond1 & cond2 & cond3]
    return clusters


def get_clustering_recommendations(album=None, artist=None, track=None, num_recs=10, path=PATH):
    """ Get random sample of recommendations based on which cluster a given song falls into
    """
    clusters = load_and_process_cluster_labels(path)
    if album:
        result = clusters[clusters["release"].str.contains(album, regex=False, case=False)]
    elif track:
        result = clusters[clusters["title"].str.contains(track, regex=False, case=False)]
    elif artist:
        result = clusters[clusters["artist_name"].str.contains(artist, regex=False, case=False)]
    else:
        return None

    # Get list of clusters the track/album or artist has (Will be >= 1)
    labels = list(result["labels"])

    # Take random sample with n rows from records that fall into the given clusters
    recommendations = clusters[clusters["labels"].isin(labels)].sample(n=num_recs)
    recommendations.columns = ["Title", "Artist", "Track", "labels"]

    return recommendations.drop("labels", axis=1)
