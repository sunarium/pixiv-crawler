import requests
import os

access_token = None
user_id = None
refresh_token = None

url = 'https://oauth.secure.pixiv.net/auth/token'
headers = {
    'App-OS': 'ios',
    'App-OS-Version': '10.3.1',
    'App-Version': '6.7.1',
    'User-Agent': 'PixivIOSApp/6.7.1 (iOS 10.3.1; iPhone8,1)',
}
data = {
    'get_secure_url': 1,
    'client_id': 'bYGKuGVw91e0NMfPGp44euvGt59s',
    'client_secret': 'HP3RmkgAmEGro0gn1x9ioawQE8WMfvLXDz3ZqxpK',
    'grant_type': 'password',
    'username': 'user_vvpk3532',
    'password': 'qwertyuiop1'
}
#ar = requests.post(url, headers=headers, data=data).json()
ar = requests.post(url, headers=headers, data=data)

access_token = ar['response']['access_token']
refresh_token = ar['response']['refresh_token']
user_id = ar['response']['user']['id']

search_url = 'https://public-api.secure.pixiv.net/v1/search/works.json'
search_params = {
    'q': 'めぐみん',
    'page': 1,
    'per_page': 50, 
    'period': 'all',
    'order': 'desc',
    'sort': 'date',
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

search_header['Authorization'] = 'Bearer %s' % access_token

sr = requests.get(search_url, headers=search_header, params=search_params)

down_url = 'https://i.pximg.net/img-original/img/2016/03/25/00/11/03/55991735_p0.jpg'
down_header = {
    'Referer': 'https://app-api.pixiv.net/'
}
down_path = os.path.join(os.path.curdir, 'test.jpg')

dr = requests.get(down_url, headers=down_header, stream=True)

print(dr.status_code)

if dr.status_code != 200:
    exit()

with open(down_path, 'wb') as img_file:
    img_file.write(dr.content)
    img_file.close()

print('Success')
