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
        'mode': 'tag',
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
    def log_json(json_str, filename_prefix='log'):
        filename = filename_prefix + '_' + time.strftime("%m_%d %H_%M_%S", time.gmtime()) + '.json'
        with io.open(filename, 'w', encoding='utf-8') as f:
            f.write(json_str)

    @staticmethod
    def json_to_object(json_text):
        return json.loads(json_text, object_hook=lambda d: namedtuple('json', d.keys())(*d.values()))

    # subroutines

    def recover_token(self):
        try:
            with open('atoken', 'r') as f:
                self.access_token = f.read()
        except:
            pass

    def save_token(self):
        try:
            with open('atoken', 'w') as f:
                f.write(self.access_token)
        except:
            pass

    def get_access_token(self):
        self.auth_payload['username'] = self.username
        self.auth_payload['password'] = self.password
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
        print('New Token:', self.access_token)

    def auth(self):
        self.recover_token()
        if not self.test_access_token():
            self.get_access_token()

    def test_access_token(self):
        trial_url = 'https://app-api.pixiv.net/v1/illust/recommended?content_type=illust \
        &filter=for_ios&include_ranking_label=true'
        if not self.access_token:
            return False
        print('Token recovered:', self.access_token)
        self.header['Authorization'] = 'Bearer %s' % self.access_token
        r = self.session.get(trial_url, headers=self.header)
        del self.header['Authorization']
        if r.status_code == 200:
            print('Successfully recovered access token')
            return True
        else:
            print('Recovered token no-good... using username and pass')
            return False

    def search(self, pages=100, log=False):
        if self.is_premium:
            self.search_params['sort'] = 'popular'
        self.header['Authorization'] = 'Bearer %s' % self.access_token
        print('Token used:', self.access_token)
        for page in range(1, pages+1):  # grab at most 5000
            self.search_params['page'] = page
            r = self.session.get(self.search_url, headers=self.header, params=self.search_params)
            if r.status_code != 200:
                self.fatal('Search Error: %s' % r.text)
            r.encoding = 'utf-8'
            if log:
                self.log_json(r.text)
                print('Got %d results' % r.json()['pagination']['total'])
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

    def save_image_from_url(self, url):
        file = os.path.basename(url)
        if not os.path.exists(file):
            with open(file, 'wb+') as f:
                stream = self.session.get(url, headers=self.download_header, stream=True)
                f.write(stream.content)

    def save_images(self, debug=False):
        # todo
        # - Added a counter
        # - Add random delay
        total = len(self.image_url_list)
        for i, u in enumerate(self.image_url_list):
            try:
                print('Saving {:4d} of {:4d}...'.format(i, total), end='\n')
                self.save_image_from_url(u)
                if debug:
                    print('Successfully saved %s' % u)
                time.sleep(2)
            except Exception as e:
                print('Error in saving %s' % u)
                print(e)
        self.image_url_list = []

    def save_mangas(self):
        if not os.path.exists('manga'):
            os.makedirs('manga')
        for _id in self.manga_id_list:
            r = self.session.get(self.illust_info_url % _id, headers=self.header)
            if r.status_code != 200:
                self.fatal('Error in getting detailed info on img\n%s' % r.text)
            j = self.json_to_object(r.text)
            for img in j.response[0].metadata.pages:
                filename = os.path.join(os.path.dirname(__file__), 'manga', os.path.basename(img.image_urls.medium))
                self.save_image_from_url(img.image_urls.medium)
            time.sleep(2)
        self.manga_id_list = []

    def test_run(self):
        self.test_access_token()
        self.get_access_token()
        self.test_access_token()

    def run(self, pages=100, log_search=False, save=True):
        self.auth()
        self.search(pages=pages, log=log_search)
        if save:
            self.save_images()
            self.save_mangas()

if __name__ == '__main__':
    p = PixivBot(username='yu_mingqian@sina.com', password='password')
    p.run(pages=1, log_search=True, save=True)
