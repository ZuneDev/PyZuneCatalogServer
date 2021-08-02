import urllib.request
import urllib.error
from xml.dom.minidom import Document, Element

from flask import Flask, request, abort, Response
import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError
import api.discogs
import api.deezer
import api.imdb

from atom.factory import *

from locale import *
locale = getdefaultlocale()[0]


app = Flask(__name__)
musicbrainzngs.set_useragent("Zune", "4.8", "https://github.com/ZuneDev/PyZuneCatalogServer")


import re
@app.after_request
def allow_zunestk_cors(response):
    r = request.origin
    if r is None:
        return response
    if re.match(r"https?://(127\.0\.0\.(?:\d*)|localhost(?::\d+)?|(?:\w*\.)*zunes\.(tk|me))", r):
        response.headers.add('Access-Control-Allow-Origin', r)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
        response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
    return response


@app.route(f"/v3.2/<string:locale>/hubs/music")
def hubs_music(locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_hubs_music.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


@app.route(f"/v3.2/<string:locale>/music/genre/<string:id>/")
def music_genre_details(id: str, locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_music_genre.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


@app.route(f"/v3.2/<string:locale>/music/genre/<string:id>/albums/")
def music_genre_albums(id: str, locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_music_genre.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


@app.route(f"/v3.2/<string:locale>/music/genre/")
def music_genre(locale: str):
    from musicbrainz.genrelist import GENRES
    lastpulledlist: datetime = datetime(2021, 2, 21)

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "Genres", "genre", request.endpoint, lastpulledlist)

    for genre_name, genre_id in GENRES.items():
        entry: Element = create_entry(doc, genre_name, genre_id, f"/v3.2/{locale}/music/genre" + genre_id, lastpulledlist)
        feed.appendChild(entry)

    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route(f"/v3.2/<string:locale>/music/album/<string:album_id>/")
def music_get_album(album_id: str, locale: str):
    try:
        album = musicbrainzngs.get_release_by_id(album_id, includes=["artists", "recordings"])["release"]
    except ResponseError as error:
        abort(error.cause.code)
        return
    album_name: str = album["title"]
    artist = album["artist-credit"][0]["artist"]
    artist_id: str = artist["id"]
    artist_name: str = artist["name"]
    tracks = album["medium-list"][0]["track-list"]

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, album_name, album_id, request.endpoint)

    if bool(album["cover-art-archive"]["front"]):
        # Add front cover
        image_elem: Element = doc.createElement("image")
        image_id_elem: Element = create_id(doc, album_id)
        image_elem.appendChild(image_id_elem)
        feed.appendChild(image_elem)

    for track in tracks:
        recording = track["recording"]
        track_id: str = recording["id"]
        track_title: str = recording["title"]
        entry: Element = create_entry(doc, track_title, track_id, f"/v3.2/{locale}/")

        # Set primaryArtist
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        primary_artist_props = {
            "id": artist_id,
            "name": artist_name
        }
        set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
        entry.appendChild(primary_artist_elem)

        try:
            length_ms: int = int(track["track_or_recording_length"])
            # FIXME: Add duration element
            length_elem: Element = doc.createElement("duration")
            length_timespan: str = f"00:00:00.{length_ms:0>3}"
            print("Duration:", length_timespan)
            set_element_value(length_elem, length_timespan)
            entry.appendChild(length_elem)
        except:
            pass

        try:
            track_position: str = track["position"]
            # FIXME: Add track number element
            index_elem: Element = doc.createElement("trackNumber")
            print("Track #:", track_position)
            set_element_value(index_elem, track_position)
            entry.appendChild(index_elem)
        except:
            pass

        try:
            # Add rights
            right: Element = doc.createElement("right")
            right_props = {
                # "providerName": "YouTube",
                "providerCode": "117767492:MP3_DOWNLOAD_UENC_256kb_075",
                "price": 800,
                "priceCurrencyCode": "MPT",
                "licenseType": "Preview",
                "audioEncoding": "MP3",
                "offerId": "urn:uuid:9534a201-2102-11db-89ca-0019b92a3933",
                "paymentTypes": {
                    "paymentType": "Microsoft Points"
                }
                # "offerInstanceId": "urn:uuid:9534a201-2102-11db-89ca-0019b92a3933",
            }
            set_values_as_elements(doc, right, right_props)
            rights: Element = doc.createElement("rights")
            rights.appendChild(right)
            entry.appendChild(rights)
            set_value_as_element(doc, entry, "isActionable", "True")
            set_value_as_element(doc, entry, "canPlay", "True")
        except:
            pass

        feed.appendChild(entry)

    # doc.appendChild(feed)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route(f"/v3.2/<string:locale>/music/album/<string:id>/<path:fragment>/")
def music_album_details(id: str, fragment: str, locale: str):
    return fragment


# Get artist information
@app.route(f"/v3.2/<string:locale>/music/artist/<string:id>/")
def music_get_artist(id: str, locale: str):
    artist, mb_artist = api.discogs.get_artist_from_mbid(id)
    artist_name: str = mb_artist["name"]
    artist_sort_name: str = mb_artist["sort-name"]

    #if type(artist) is int:
    #    abort(artist)
    #    return

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, artist_name, id, request.endpoint)
    artist_props = {
        "id": id,
        "title": artist_name,
        "sortTitle": artist_sort_name,
        "isVariousArtist ": False,
        #"biographyLink": artist["resource_url"],
        # TODO: How to set artist image?
        "backgroundImageId": "7da9ffbf-2b5a-4162-b2eb-5818bd6574f3"
    }
    set_values_as_elements(doc, feed, artist_props)

    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


# Get artist's tracks
@app.route(f"/v3.2/<string:locale>/music/artist/<string:artist_id>/tracks/")
def music_get_artist_tracks(artist_id: str, locale: str):
    try:
        recordings = musicbrainzngs.browse_recordings(artist_id, limit=100)["recording-list"]
    except ResponseError as error:
        abort(error.cause.code)
        return
    artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
    artist_name: str = artist["name"]

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, artist_name, artist_id, request.endpoint)

    for recording in recordings:
        id: str = recording["id"]
        title: str = recording["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/artist/{artist_id}/tracks/{id}")
        feed.appendChild(entry)

        # Create primaryArtist element
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        primary_artist_props = {
            "id": artist_id,
            "name": artist_name
        }
        set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
        entry.appendChild(primary_artist_elem)

    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


# Get artist's albums
@app.route(f"/v3.2/<string:locale>/music/artist/<string:artist_id>/albums/")
def music_get_artist_albums(artist_id: str, locale: str):
    try:
        releases = musicbrainzngs.browse_releases(artist_id, limit=100)["release-list"]
    except ResponseError as error:
        abort(error.cause.code)
        return
    artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
    artist_name: str = artist["name"]

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, artist_name, artist_id, request.endpoint)

    for release in releases:
        id: str = release["id"]
        title: str = release["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/artist/{artist_id}/albums/{id}")
        feed.appendChild(entry)

        # Add front cover
        image_elem: Element = doc.createElement("image")
        image_id_elem: Element = create_id(doc, id)
        image_elem.appendChild(image_id_elem)
        entry.appendChild(image_elem)

        # Create primaryArtist element
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        primary_artist_props = {
            "id": artist_id,
            "name": artist_name
        }
        set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
        entry.appendChild(primary_artist_elem)

    #doc.appendChild(feed)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route(f"/v3.2/<string:locale>/music/artist/<string:id>/primaryImage/")
def music_artist_primaryImage(id: str, locale: str):
    response = api.deezer.get_artist_from_mbid(id)

    artist, mb_artist = response
    if type(artist) is int:
        abort(artist)
        return

    # Request the image from the API and forward it to the Zune software
    try:
        image = urllib.request.urlopen(artist["picture_big"])
        return Response(image.read(), mimetype=MIME_JPG)
    except urllib.error.HTTPError as error:
        abort(error.code)


@app.route("/v3.2/<string:locale>/music/track/<string:mbid>/")
def music_get_track(mbid: str, locale: str):
    try:
        response = musicbrainzngs.get_recording_by_id(mbid, includes=["artist-credits", "releases"])
    except ResponseError as error:
        abort(error.cause.code)
        return
    recording = response["recording"]
    doc: Document = minidom.Document()

    # Set track ID and Title
    id: str = recording["id"]
    title: str = recording["title"]
    feed: Element = create_feed(doc, title, id, request.endpoint)

    entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/track/" + id)
    feed.appendChild(entry)

    # Get artist ID and Name
    artist = recording["artist-credit"][0]["artist"]
    artist_id: str = artist["id"]
    artist_name: str = artist["name"]

    # Create primaryArtist element
    primary_artist_elem: Element = doc.createElement("primaryArtist")

    artist_id_element: Element = doc.createElement("id")
    set_element_value(artist_id_element, artist_id)
    primary_artist_elem.appendChild(artist_id_element)

    artist_name_element: Element = doc.createElement("name")
    set_element_value(artist_name_element, artist_name)
    primary_artist_elem.appendChild(artist_name_element)
    entry.appendChild(primary_artist_elem)

    # Get album ID and Title
    album = recording["release-list"][0]
    album_id: str = album["id"]
    album_name: str = album["title"]

    # Create album elements
    album_id_element: Element = doc.createElement("albumId")
    set_element_value(album_id_element, album_id)
    entry.appendChild(album_id_element)

    album_name_element: Element = doc.createElement("albumTitle")
    set_element_value(album_name_element, album_name)
    entry.appendChild(album_name_element)

    # Add rights
    right: Element = doc.createElement("right")
    right_props = {
        "providerCode": "117767492:MP3_DOWNLOAD_UENC_256kb_075",
        "price": 800,
        "priceCurrencyCode": "MPT",
        "licenseType": "Preview",
        "audioEncoding": "MP3",
        "offerId": "urn:uuid:9534a201-2102-11db-89ca-0019b92a3933",
        "paymentTypes": {
            "paymentType": "Microsoft Points"
        }
    }
    set_values_as_elements(doc, right, right_props)
    rights: Element = doc.createElement("rights")
    rights.appendChild(right)
    entry.appendChild(rights)

    xml_str = doc.toprettyxml(indent="\t")
    print(xml_str)
    return Response(xml_str, mimetype=MIME_XML)


# Get top tracks
@app.route(f"/v3.2/<string:locale>/music/chart/zune/tracks/")
def music_chart_tracks(locale: str):
    deezer = api.deezer.get_chart()
    if type(deezer) is int:
        abort(deezer)
        return

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "tracks", "tracks", f"/v3.2/{locale}/music/chart/zune/tracks")
    for track in deezer["tracks"]["data"]:
        try:
            recording = musicbrainzngs.search_recordings(
                track["artist"]["name"] + ", " + track["album"]["title"] + ", " + track["title"]
                , 1, "text")["recording-list"][0]
        except ResponseError as error:
            #abort(error.cause.code)
            #return
            continue

        # Set track ID and Title
        id: str = recording["id"]
        title: str = recording["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/collection/features/" + id)

        # Get artist ID and Name
        artist = recording["artist-credit"][0]["artist"]
        artist_id: str = artist["id"]
        artist_name: str = artist["name"]

        # Set track information
        track_props = {
            "isExplicit": track["explicit_lyrics"],
            "playRank": track["rank"],
            "isActionable": True,
        }
        set_values_as_elements(doc, entry, track_props)

        # Set primaryArtist
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        primary_artist_props = {
            "id": artist_id,
            "name": artist_name
        }
        set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
        entry.appendChild(primary_artist_elem)

        # Add rights
        right: Element = doc.createElement("right")
        right_props = {
            #"providerName": "YouTube",
            "providerCode": "117767492:MP3_DOWNLOAD_UENC_256kb_075",
            "price": 800,
            "priceCurrencyCode": "MPT",
            "licenseType": "Preview",
            "audioEncoding": "MP3",
            "offerId": "urn:uuid:9534a201-2102-11db-89ca-0019b92a3933",
            "paymentTypes": {
                "paymentType": "Microsoft Points"
            }
            #"offerInstanceId": "urn:uuid:9534a201-2102-11db-89ca-0019b92a3933",
        }
        set_values_as_elements(doc, right, right_props)
        rights: Element = doc.createElement("rights")
        rights.appendChild(right)
        entry.appendChild(rights)

        try:
            track_position: str = track["position"]
            index_elem: Element = doc.createElement("trackNumber")
            set_element_value(index_elem, track_position)
            entry.appendChild(index_elem)
        except:
            pass

        feed.appendChild(entry)
    xml_str = doc.toprettyxml(indent="\t")
    print(xml_str)
    return Response(xml_str, mimetype=MIME_XML)


# Search tracks
@app.route(f"/v3.2/<string:locale>/music/track")
def music_track(locale: str):
    query: str = request.args.get("q")
    try:
        response = musicbrainzngs.search_recordings(query)
    except ResponseError as error:
        abort(error.cause.code)
        return
    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "tracks", "tracks", request.endpoint)
    for recording in response["recording-list"]:
        try:
            # Set track ID and Title
            id: str = recording["id"]
            title: str = recording["title"]
            entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/track/" + id)

            # Get artist ID and Name
            artist = recording["artist-credit"][0]["artist"]
            artist_id: str = artist["id"]
            artist_name: str = artist["name"]

            # Set primaryArtist
            primary_artist_elem: Element = doc.createElement("primaryArtist")
            primary_artist_props = {
                "id": artist_id,
                "name": artist_name
            }
            set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
            entry.appendChild(primary_artist_elem)

            # Get album ID and Title
            album = recording["release-list"][0]
            album_id: str = album["id"]
            album_name: str = album["title"]

            # Set album info
            primary_album_elem: Element = doc.createElement("album")
            primary_album_props = {
                "id": album_id,
                "title": album_name
            }
            set_values_as_elements(doc, primary_album_elem, primary_album_props)
            entry.appendChild(primary_album_elem)

            feed.appendChild(entry)
        except:
            pass
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


# Search albums
@app.route(f"/v3.2/<string:locale>/music/album")
def music_album(locale: str):
    query: str = request.args.get("q")
    try:
        response = musicbrainzngs.search_releases(query)
    except ResponseError as error:
        abort(error.cause.code)
        return
    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, response["title"], response["id"], f"/v3.2/{locale}/music/chart/zune/albums")
    for release in response["release-list"]:
        print(release)

        # Set track ID and Title
        id: str = release["id"]
        title: str = release["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/music/album/" + id)

        # Add front cover
        image_elem: Element = doc.createElement("image")
        image_id_elem: Element = create_id(doc, id)
        image_elem.appendChild(image_id_elem)
        entry.appendChild(image_elem)

        # Get artist ID and Name
        artist = release["artist-credit"][0]["artist"]
        artist_id: str = artist["id"]
        artist_name: str = artist["name"]

        # Set primaryArtist
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        primary_artist_props = {
            "id": artist_id,
            "name": artist_name
        }
        set_values_as_elements(doc, primary_artist_elem, primary_artist_props)
        entry.appendChild(primary_artist_elem)

        feed.appendChild(entry)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


### MOVIES
@app.route(f"/v3.2/<string:locale>/chart/zuneDownload/movie/")
def chart_zunedown_movie(locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_hubs_music.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


@app.route(f"/v3.2/<string:locale>/music/hub/movie/")
def hubs_movie(locale: str):
    imdb = api.imdb.get_chart()
    if type(imdb) is int:
        abort(imdb)
        return

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "Movies", "movies", f"/v3.2/{locale}/music/hub/movie")
    for movie in imdb:
        # Set movie ID and Title
        id: str = api.imdb.IMDB_GUID_TITLE_BASE + movie["id"][2:]
        title: str = movie["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/{locale}/movies/" + id)

        # Set track information
        track_props = {
            "imageId": id,
            "isActionable": True,
        }
        set_values_as_elements(doc, entry, track_props)

        feed.appendChild(entry)
    xml_str = doc.toprettyxml(indent="\t")
    print(xml_str)
    return Response(xml_str, mimetype=MIME_XML)


@app.route(f"/v3.2/<string:locale>/music/hub/video/")
def hubs_video(locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_hubs_music.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


### PODCASTS
@app.route(f"/v3.2/<string:locale>/music/hub/podcast/")
def hubs_podcasts(locale: str):
    with open(f'reference/catalog.zune.net_v3.2_{locale}_music_hub_podcast.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


@app.route(f"/v3.2/<string:locale>/podcast")
def podcast_passthrough(locale: str):
    podcast_url: str = request.args.get('url')
    podcast = urllib.request.urlopen(podcast_url)
    return Response(podcast.read(), mimetype="application/rss+xml")

### Metadata
# fai.music.metaservices.microsoft.com
@app.route("/ZuneAPI/EndPoints.aspx")
def get_metadata_endpoints():
    print(request.full_path)
    with open('reference/catalog.zune.net_v3.2_en-US_hubs_music.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype=MIME_ATOM_XML)


if __name__ == "__main__":
    app.run(port=80, host="127.0.0.2")
