import urllib.request
import urllib.error
import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError
import json

from typing import Union, Tuple


DISCOGS_API: str = "https://api.discogs.com"


def get_artist_from_mbid(mbid: str) -> Tuple[Union[int, dict], dict]:
    try:
        mb_artist: dict = musicbrainzngs.get_artist_by_id(mbid, includes=["url-rels", "tags"])["artist"]
    except ResponseError as error:
        return error.cause.code

    dc_artist: dict = get_artist_from_mbobj(mb_artist)
    return dc_artist, mb_artist


def get_artist_from_mbobj(mbobj: dict) -> Union[int, dict]:
    if "url-relation-list" not in mbobj:
        return 404
    discogs_rel = [x for x in mbobj["url-relation-list"] if x["type"] == "discogs"]
    if len(discogs_rel) < 1:
        return 404
    discogs_link: str = discogs_rel[0]["target"].replace("www", "api").replace("artist", "artists")
    try:
        response = urllib.request.urlopen(discogs_link)
    except urllib.error.HTTPError as error:
        return error.code

    discogs: dict = json.load(response)
    return discogs
