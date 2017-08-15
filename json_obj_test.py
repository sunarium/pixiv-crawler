# -*- coding:utf-8 -*-

import json
from collections import namedtuple

if __name__ == '__main__':
    with open('search.json', mode='r', encoding='utf-8') as f:
        json_text = f.read().encode()
    x = json.loads(json_text, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

    print(x.status, len(x.response), x.response[0].image_urls.large)