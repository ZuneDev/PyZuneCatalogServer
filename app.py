from xml.dom.minidom import Document, Element

from flask import Flask, request, Response
import musicbrainzngs

from atom.factory import *

app = Flask(__name__)
musicbrainzngs.set_useragent("Zune", "4.8", "https://github.com/yoshiask/PyZuneCatalogServer")


@app.route("/v3.2/en-US/hubs/music")
def hubs_music():
    with open('reference/catalog.zune.net_v3.2_en-US_hubs_music.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype='text/xml')


@app.route("/v3.2/en-US/music/hub/podcast/")
def hubs_podcasts():
    with open('reference/catalog.zune.net_v3.2_en-US_music_hub_podcast.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype='text/xml')


@app.route("/v3.2/en-US/music/genre/<string:id>/")
def music_genre_details(id: str):
    with open('reference/catalog.zune.net_v3.2_en-US_music_genre.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype='text/xml')


@app.route("/v3.2/en-US/music/genre/<string:id>/albums/")
def music_genre_albums(id: str):
    with open('reference/catalog.zune.net_v3.2_en-US_music_genre.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype='text/xml')


@app.route("/v3.2/en-US/music/genre/")
def music_genre():
    with open('reference/catalog.zune.net_v3.2_en-US_music_genre.xml', 'r') as file:
        data: str = file.read().replace('\n', '')
        return Response(data, mimetype='text/xml')


@app.route("/v3.2/en-US/music/album/<album_id>/")
def music_get_album(album_id: str):
    print(album_id)
    album = musicbrainzngs.get_release_by_id(album_id, includes=["artists", "recordings"])["release"]
    print(album)
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
        track_position: str = track["position"]
        length_ms: str = track["track_or_recording_length"]
        entry: Element = create_entry(doc, track_title, track_id, f"/v3.2/en-US/")

        # Create primaryArtist element
        primary_artist_elem: Element = doc.createElement("primaryArtist")
        artist_id_element: Element = doc.createElement("id")
        set_element_value(artist_id_element, artist_id)
        primary_artist_elem.appendChild(artist_id_element)
        artist_name_element: Element = doc.createElement("name")
        set_element_value(artist_name_element, artist_name)
        primary_artist_elem.appendChild(artist_name_element)
        entry.appendChild(primary_artist_elem)

        # FIXME: Add duration element
        length_elem: Element = doc.createElement("duration")
        set_element_value(length_elem, length_ms)

        # FIXME: Add index element
        index_elem: Element = doc.createElement("index")
        set_element_value(index_elem, track_position)

        feed.appendChild(entry)

    # doc.appendChild(feed)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route("/v3.2/en-US/music/album/<string:id>/<path:fragment>/")
def music_album_details(id: str, fragment: str):
    return fragment


# Get artist information
@app.route("/v3.2/en-US/music/artist/<string:id>/")
def music_get_artist(id: str):
    return music_get_artist_tracks(id)


# Get artist's tracks
@app.route("/v3.2/en-US/music/artist/<string:artist_id>/tracks/")
def music_get_artist_tracks(artist_id: str):
    recordings = musicbrainzngs.browse_recordings(artist_id, limit=100)["recording-list"]
    artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
    artist_name: str = artist["name"]

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, artist_id, artist_name, request.endpoint)

    for recording in recordings:
        id: str = recording["id"]
        title: str = recording["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/en-US/music/artist/{artist_id}/tracks/{id}")
        feed.appendChild(entry)

        # Create primaryArtist element
        primary_artist_elem: Element = doc.createElement("primaryArtist")

        artist_id_element: Element = doc.createElement("id")
        set_element_value(artist_id_element, artist_id)
        primary_artist_elem.appendChild(artist_id_element)

        artist_name_element: Element = doc.createElement("name")
        set_element_value(artist_name_element, artist_name)
        primary_artist_elem.appendChild(artist_name_element)
        entry.appendChild(primary_artist_elem)

    #doc.appendChild(feed)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


# Get artist's albums
@app.route("/v3.2/en-US/music/artist/<string:artist_id>/albums/")
def music_get_artist_albums(artist_id: str):
    releases = musicbrainzngs.browse_releases(artist_id, limit=100)["release-list"]
    artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
    artist_name: str = artist["name"]

    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, artist_id, artist_name, request.endpoint)

    for release in releases:
        id: str = release["id"]
        title: str = release["title"]
        entry: Element = create_entry(doc, title, id, f"/v3.2/en-US/music/artist/{artist_id}/albums/{id}")
        feed.appendChild(entry)

        # Create primaryArtist element
        primary_artist_elem: Element = doc.createElement("primaryArtist")

        artist_id_element: Element = doc.createElement("id")
        set_element_value(artist_id_element, artist_id)
        primary_artist_elem.appendChild(artist_id_element)

        artist_name_element: Element = doc.createElement("name")
        set_element_value(artist_name_element, artist_name)
        primary_artist_elem.appendChild(artist_name_element)
        entry.appendChild(primary_artist_elem)

    #doc.appendChild(feed)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route("/v3.2/en-US/music/artist/<string:id>/<path:fragment>/")
def music_artist_details(id: str, fragment: str):
    return fragment


# Get top tracks
@app.route("/v3.2/en-US/music/chart/zune/tracks/")
def music_chart_tracks():
    recordings = musicbrainzngs.search_recordings("*", limit=100)
    print(recordings)
    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "tracks", "tracks", "/v3.2/en-US/music/chart/zune/tracks")
    for recording in recordings["recording-list"]:
        print(recording)
        # Set track ID and Title
        id: str = recording["id"]
        title: str = recording["title"]
        entry: Element = create_entry(doc, title, id, "/v3.2/en-US/music/collection/features/" + id)

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

        feed.appendChild(entry)
    xml_str = doc.toprettyxml(indent="\t")
    return Response(xml_str, mimetype=MIME_XML)


@app.route("/v3.2/en-US/music/track")
def music_track_details():
    query: str = request.args.get("q")
    response = musicbrainzngs.search_releases(query)
    doc: Document = minidom.Document()
    feed: Element = create_feed(doc, "tracks", "tracks", "/v3.2/en-US/music/chart/zune/tracks")
    for release in response["release-list"]:
        print(release)

        # Set track ID and Title
        id: str = release["id"]
        title: str = release["title"]
        entry: Element = create_entry(doc, title, id, "/v3.2/en-US/music/collection/features/" + id)

        # Get artist ID and Name
        artist = release["artist-credit"][0]["artist"]
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

        feed.appendChild(entry)
    xml_str = doc.toprettyxml(indent="\t")
    print(xml_str)
    return Response(xml_str, mimetype=MIME_XML)


@app.route("/")
def commerce():
    # TODO: Attempt SSL handshake
    return "Howdy, Zune!"


### IMAGES
@app.route("/v3.2/en-US/image/<string:mbid>")
def get_image(mbid: str):
    print("Image request for", mbid)
    import urllib.request
    image = urllib.request.urlopen(f"http://coverartarchive.org/release/{mbid}/front")
    return Response(image.read(), mimetype=MIME_JPG)
