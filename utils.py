import urllib.request
import urllib.error
import json
from typing import Union


def get_json(url: str) -> Union[int, dict]:
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as error:
        return error.code

    return json.load(response)


def format_timespan(tmil: int) -> str:
    tsec = tmil / float(1000)
    min = int(tsec // 60)
    sec = int(tsec % 60)
    mil = tmil - (min * 60000 - sec * 1000)
    return f"00:{min}:{sec}.{mil}"

