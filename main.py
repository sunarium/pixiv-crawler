import requests
import os
import time

#constants
default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pixiv_crawl')
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
    'grant_type': 'password',
    'username': 'user_vvpk3532',
    'password': 'qwertyuiop1'
}
search_url = 'https://public-api.secure.pixiv.net/v1/search/works.json'
search_params = {
    'q': 'めぐみん',
    'page': 1,
    'per_page': 50,
    'period': 'all',
    'order': 'desc',
    'sort': 'popular',
    'mode': 'text',
    'types': 'illustration',
    'image_sizes': 'large',
    'include_stats': True,
    'include_sanity_level': True
}
search_header = {
    'Referer': 'http://spapi.pixiv.net/',
    'User-Agent': 'PixivIOSApp/5.8.7',
}

def strip_image_adress(raw_response):
    pass

def save_to_file(image_url, prefix, path=default_path):
    pass

def fatal(fatal_exception):
    print('fatal error:', fatal_exception)
    exit()


'''
#get acess token
try:
    auth_response = requests.post(auth_url, headers=auth_header, data=auth_payload)
except Exception as e:
    fatal('auth:requests error: %s' % e)
if auth_response.status_code != 200:
    fatal('auth:server returned\n%s' % auth_response.text)
access_token = auth_response.json()['response']['access_token']

#search
search_header['Authorization'] = 'Bearer %s' % access_token
try:
    search_response = requests.get(search_url, headers=search_header, params=search_params)
except Exception as e:
    fatal('requests error when searching: %s' % e)
if search_response.status_code != 200:
    fatal('search:server returned\n%s' % auth_response.text)

#debug
with open('res.json', 'w') as f:
    f.write(search_response.text)
    f.close

'''