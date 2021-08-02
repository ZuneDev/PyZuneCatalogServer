import urllib.request
import urllib.error
import json
from secrets import IMDB_API_KEY

from typing import Union


IMDB_API: str = "https://imdb-api.com/API"
IMDB_GUID_TITLE_BASE: str = "8b3bbf8f-6c7a-4d87-8c5d-58eb3"
IMDB_GUID_NAME_BASE: str = "352ed211-ae21-4ab9-9e30-821e7"


def get_chart() -> Union[int, dict]:
    try:
        response = urllib.request.urlopen(IMDB_API + "/MostPopularMovies/" + IMDB_API_KEY)
    except urllib.error.HTTPError as error:
        return error.code

    return json.load(response)["items"]
