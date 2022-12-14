import json
import re

def save_as_json(filename: str, data: dict):
    json_object = json.dumps(data, indent=4)
    with open(filename, 'w') as outfile:
        outfile.write(json_object)

def read_as_json(filename: str) -> dict:
    try:
        with open(filename, 'r') as openfile:
            json_object = json.load(openfile)
    except Exception:
        return None
    else:
        return json_object

def get_domain(url: str) -> str:
    return re.split('(?<!/)/(?!/)', url)[0]


def get_absolute_url(link: str, base_url: str):
    return link if link.startswith('http') or link.startswith('www') else base_url[:len(base_url) - 1] + link


def is_same_domain(url:str, other_url:str) -> str:
    return get_domain(url) == get_domain(other_url)


def weighted_average_emotion(emotions_a: dict, count_a: int, emotions_b: dict, count_b: int) -> dict:
    result = {}
    total = count_a + count_b
    for key in emotions_a:
        result[key] = (emotions_a[key] * count_a + emotions_b[key] * count_b) / total
    return result