# -*- coding:utf-8 -*-

import requests
import os
import time
import json
import io
from collections import namedtuple

class PixivBot(object):
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
        'page': 1,  # subject to change
        'per_page': 30,  # DO NOT CHANGE
        'period': 'all',
        'order': 'desc',
        'sort': 'date',  # 'popular' for premium accounts.
        'mode': 'text',
        'types': 'illustration,manga',
        'image_sizes': 'large',
        'include_stats': True,
        'include_sanity_level': True
    }
    header = {
        'Referer': 'http://spapi.pixiv.net/',
        'User-Agent': 'PixivIOSApp/5.8.7',
    }
    download_header = {
        'Referer': 'https://app-api.pixiv.net/'
    }
    illust_info_url = 'https://public-api.secure.pixiv.net/v1/works/%s.json'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.is_premium = False
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
        self.j = None
        self.image_url_list = []
        self.manga_id_list = []

    # helpers
    @staticmethod
    def fatal(message):
        print('[FATAL]', message)
        exit()

    @staticmethod
    def log_json(json_file, filename_prefix='log'):
        filename = filename_prefix + '_' + time.strftime("%m_%d %H_%M_%S", time.gmtime()) + '.json'
        with io.open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_file, f, ensure_ascii=False, indent=4)
            f.close()

    @staticmethod
    def json_to_object(json_text):
        return json.loads(json_text, object_hook=lambda d: namedtuple('json', d.keys())(*d.values()))

    # subroutines

    def save_token(self):
        with open('rtoken', 'w') as f:
            f.write(self.refresh_token)
            f.close()
        with open('atoken', 'w') as f:
            f.write(self.access_token)
            f.close()

    def attempt_recover_token(self):
        try:
            f = open('rtoken', 'r')
        except FileNotFoundError:
            return False
        rtoken = f.read()
        f.close()
        self.auth_payload['refresh_token'] = rtoken
        self.auth_payload['grant_type'] = 'refresh_token'
        r = self.session.post(self.auth_url, headers=self.auth_header, data=self.auth_payload)
        if r.status_code != 200:
            del self.auth_payload['refresh_token']
            del self.auth_payload['grant_type']
            print(r.text)
            return False
        else:
            r = r.json()
            self.access_token = r['response']['access_token']
            self.refresh_token = r['response']['refresh_token']
            self.save_token()
            return True

    def get_access_token(self):
        if self.attempt_recover_token():
            return
        if self.refresh_token is None:
            self.auth_payload['username'] = self.username
            self.auth_payload['password'] = self.password
            self.auth_payload['grant_type'] = 'password'
            print('!!!used username and password for login!!!')
        else:
            self.auth_payload['refresh_token'] = self.refresh_token
            self.auth_payload['grant_type'] = 'refresh_token'
        # get access token
        auth_response = self.session.post(self.auth_url, headers=self.auth_header, data=self.auth_payload)
        if auth_response.status_code != 200:
            self.fatal('auth failed!\n%s' % auth_response.text)
        auth_response = auth_response.json()
        self.access_token = auth_response['response']['access_token']
        self.refresh_token = auth_response['response']['refresh_token']
        self.is_premium = auth_response['response']['user']['is_premium']
        # save token to file
        self.save_token()
        print(self.access_token)

    def get_saved_access_token(self):
        with open('atoken', 'r') as f:
            self.access_token = f.read()
            f.close()

    def search(self, pages=100):
        # if self.is_premium:
        #     self.search_params['sort'] = 'popular'
        self.header['Authorization'] = 'Bearer %s' % self.access_token
        for page in range(1, pages):  # grab at most 5000
            self.search_params['page'] = page
            r = self.session.get(self.search_url, headers=self.header, params=self.search_params)
            r.encoding = 'utf-8'
            self.j = self.json_to_object(r.text)
            self.strip_urls()
            if self.j.pagination.next == 'null':
                break

    def search_debug(self):
        self.j = self.json_to_object(open('search.json', 'r', encoding='utf-8'))

    def strip_urls(self, debug=False):
        for i in self.j.response:
            if i.is_manga:
                self.manga_id_list.append(str(i.id))
            else:
                self.image_url_list.append(i.image_urls.large)
        if debug:
            print(self.manga_id_list)
            print(self.image_url_list)

    def save_image_from_url(self, url, file):
        if not os.path.exists(file):
            with open(file, 'wb+') as f:
                stream = self.session.get(url, headers=self.download_header, stream=True)
                f.write(stream.content)
                f.close()

    def save_images(self, debug=False):
        for u in self.image_url_list:
            try:
                filename = os.path.basename(u)
                self.save_image_from_url(u, filename)
                if debug:
                    print('Successfully saved %s' % filename)
            except Exception as e:
                print('Error in saving %s' % u)
                print(e)
        self.image_url_list = []

    def save_mangas(self, debug=False):
        if not os.path.exists('manga'):
            os.makedirs('manga')
        for id in self.manga_id_list:
            r = self.session.get(self.illust_info_url % id, headers=self.header)
            if r.status_code != 200:
                self.fatal('Error in getting detailed info on img\n%s' % r.text)
            j = self.json_to_object(r.text)
            for img in j.response[0].metadata.pages:
                filename = os.path.join(os.path.dirname(__file__), 'manga',os.path.basename(img.image_urls.medium))
                self.save_image_from_url(img.image_urls.medium, filename)
        self.manga_id_list = []

    def test_run(self):
        self.search_debug()
        self.strip_urls(debug=True)
        self.save_images(debug=True)
        self.save_mangas(debug=True)

    def run(self, pages=100):
        self.get_access_token()
        self.search(pages=pages)
        self.strip_urls()
        self.save_images()
        self.save_mangas()

if __name__ == '__main__':
    p = PixivBot(username='yu_mingqian@sina.com', password='password')
    p.run(pages=2)