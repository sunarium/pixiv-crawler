# -*- coding:utf-8 -*-

####### INSERT USERNAME AND PASSWORD HERE ########
username = 'yu_ming_qian@sina.com'
password = 'password1'
verbose = True
########## DO NOT MODIFY ANYTHING BELOW ##########

import requests
import os
import time
import json
import io

# constants
default_download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pixiv_crawl')

auth_url = 'https://oauth.secure.pixiv.net/auth/token'

auth_header = {
    'App-OS': 'ios',
    'App-OS-Version': '10.3.1',
    'App-Version': '6.7.1',
    'User-Agent': 'PixivIOSApp/6.7.1 (iOS 10.3.1; iPhone8,1)',
}

auth_payload = {
    'get_secure_url': 1,
    'client_id': 'bYGKuGVw91e0NMfPGp44euvGt59s',
    'client_secret': 'HP3RmkgAmEGro0gn1x9ioawQE8WMfvLXDz3ZqxpK',
    'grant_type': 'password'
}

search_url = 'https://public-api.secure.pixiv.net/v1/search/works.json'

search_params = {
    'q': 'めぐみん',
    'page': 1, # subject to change
    'per_page': 50, # DO NOT CHANGE
    'period': 'all',
    'order': 'desc',
    'sort': 'date', # 'popular' for premium accounts.
    'mode': 'text',
    'types': 'illustration, manga',
    'image_sizes': 'large',
    'include_stats': True,
    'include_sanity_level': True
}

search_header = {
    'Referer': 'http://spapi.pixiv.net/',
    'User-Agent': 'PixivIOSApp/5.8.7',
}

illust_info_header = {
    'Referer': 'http://spapi.pixiv.net/',
    'User-Agent': 'PixivIOSApp/5.1.1',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer 8mMXXWT9iuwdJvsVIvQsFYDwuZpRCMePeyagSh30ZdU',
    'Cookie': 'PHPSESSID=500123_{}',
}

illust_info_url = 'https://public-api.secure.pixiv.net/v1/works/{}.json'

# helpers


def fatal(message):
    print('[FATAL]', message)
    exit()


def log_json(json_file, filename_prefix='log'):
    filename = filename_prefix + '_' + time.strftime("%m.%d %H:%M:%S", time.gmtime()) + '.json'
    with io.open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_file, f, ensure_ascii=False, indent=4)
        f.close()

# subroutines


def recover_access_token():
    with open('atoken', 'r') as f:
        return f.read()


def get_access_token():
    auth_payload['username'] = username
    auth_payload['password'] = password
    auth_response = None
    # get access token
    try:
        auth_response = requests.post(auth_url, headers=auth_header, data=auth_payload)
        log_json(auth_response.json(), 'auth')
    except Exception as e:
        fatal('auth:requests error: %s' % e)
    if auth_response.status_code != 200:
        fatal('auth:server returned\n%s' % auth_response.text)

    access_token = auth_response.json()['response']['access_token']
    
    # save access token to file
    with open('token', 'w') as fp:
        fp.write(access_token)
        fp.close()
    return access_token


def strip_image_addresses(raw_response):
    """return a list of original urls that have rating above threshold"""


def save_to_file(image_url, path=default_download_path):
    pass

def main():
    #
    # get auth
    access_token = get_access_token()
    search_header['Authorization'] = 'Bearer %s' % access_token

    # search
    search_response = requests.get(search_url, headers=search_header, params=search_params)
    if search_response.status_code != 200:
        fatal('search:server returned\n%s' % search_response.text)

    # log_json(search_response.json(), 'search')


