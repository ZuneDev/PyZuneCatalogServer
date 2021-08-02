import urllib.request
import urllib.error
import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError
import json

from typing import Union, Tuple


DEEZER_API: str = "https://api.deezer.com"


def get_artist_from_mbid(mbid: str) -> Tuple[Union[int, dict], dict]:
    try:
        mb_artist: dict = musicbrainzngs.get_artist_by_id(mbid, includes=["url-rels", "tags"])["artist"]
    except ResponseError as error:
        return error.cause.code, dict()

    dz_artist = get_artist_from_mbobj(mb_artist)
    return dz_artist, mb_artist


def get_artist_from_mbobj(mbobj: dict) -> Union[int, dict]:
    deezer_rel = [x for x in mbobj["url-relation-list"] if "deezer.com" in x["target"]]
    if len(deezer_rel) < 1:
        return 404
    deezer_link: str = deezer_rel[0]["target"].replace("www", "api")
    try:
        response = urllib.request.urlopen(deezer_link)
    except urllib.error.HTTPError as error:
        return error.code

    deezer: dict = json.load(response)
    return deezer


def get_chart() -> Union[int, dict]:
    try:
        response = urllib.request.urlopen(DEEZER_API + "/chart")
    except urllib.error.HTTPError as error:
        return error.code

    return json.load(response)
