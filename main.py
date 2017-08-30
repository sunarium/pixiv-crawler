#!usr/bin/env python3
# -*- coding:utf-8 -*-

import requests

import sys
import os
import time
import json
import io
import random
import getpass
import traceback
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
    initial_auth_payload = { # see comments in __init__
        'get_secure_url': 1,
        'client_id': 'bYGKuGVw91e0NMfPGp44euvGt59s',
        'client_secret': 'HP3RmkgAmEGro0gn1x9ioawQE8WMfvLXDz3ZqxpK',
        'grant_type': 'password'
    }
    search_url = 'https://public-api.secure.pixiv.net/v1/search/works.json'
    initial_search_params = { # see comments in __init__
        'page': 1,
        'per_page': 30,  # DO NOT CHANGE
        'period': 'all',
        'order': 'desc',
        'sort': 'date',  # 'popular' for premium accounts.
        'mode': 'tag',
        'types': 'illustration,manga',
        'image_sizes': 'large',
        'include_stats': True,
        'include_sanity_level': True,
    }
    initial_header = { # see comments in __init__
        'Referer': 'http://spapi.pixiv.net/',
        'User-Agent': 'PixivIOSApp/5.8.7',
    }
    download_header = {
        'Referer': 'https://app-api.pixiv.net/'
    }
    illust_info_url = 'https://public-api.secure.pixiv.net/v1/works/%s.json'
    token_file = 'atoken'

    def __init__(self, username, password, tag='めぐみん'):
        self.username = username
        self.password = password
        # dicts are mutable and class attributes are added to
        #  instances by reference (not copied) upon instance creation.
        # changing e.g. initial_search_params will affect all instances.
        # therefore search_params has to be created at init time.
        self.search_params = self.initial_search_params.copy()
        self.auth_payload = self.initial_auth_payload.copy()
        self.header = self.initial_header.copy()
        self.search_params["q"] = tag
        self.is_premium = False
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
        self.j = None
        self.image_url_list = []
        self.manga_id_list = []
        self.auth()

    # helpers
    @staticmethod
    def fatal(message):
        print('[FATAL]', message)
        sys.exit(1)

    @staticmethod
    def log_json(json_str, filename_prefix='log'):
        filename = filename_prefix + '_' + time.strftime("%m_%d %H_%M_%S", time.gmtime()) + '.json'
        with io.open(filename, 'w', encoding='utf-8') as f:
            f.write(json_str)

    @staticmethod
    def json_to_object(json_text):
        objhook = lambda d: namedtuple('json', d.keys())(*d.values())
        return json.loads(json_text, object_hook=objhook)

    # subroutines

    def recover_token(self):
        try:
            with open(self.token_file, 'r') as f:
                dat = f.read()
            if (not self.username) and (dat[0] != "{"):
                self.access_token = dat
            else:
                dat = json.loads(dat)
                if (not self.username) or (dat["user"] == self.username):
                    self.access_token = dat["token"]
        except (EnvironmentError, json.decoder.JSONDecodeError):
            pass
        except:
            traceback.print_exc()

    def save_token(self):
        try:
            dat = json.dumps({"user": self.username, "token": self.access_token})
            with open(self.token_file, 'w') as f:
                f.write(dat)
        except EnvironmentError:
            pass
        except:
            traceback.print_exc()

    def save_token_old(self):
        try:
            dat = json.dumps({"user": self.username, "token": self.access_token})
            with open(self.token_file, 'w') as f:
                f.write(self.access_token)
        except EnvironmentError:
            pass
        except:
            traceback.print_exc()

    def get_access_token(self):
        self.auth_payload['username'] = self.username
        self.auth_payload['password'] = self.password
        # get access token
        auth_response = self.session.post(self.auth_url, headers=self.auth_header,
                                          data=self.auth_payload)
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
        trial_url = ('https://app-api.pixiv.net/v1/illust/recommended?content_type=illust' +
                    '&filter=for_ios&include_ranking_label=true')
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
            print('Recovered token invalid... using username and password')
            return False

    def search(self, start_page=1, end_page=100, log=False):
        # if self.is_premium:
        #     self.search_params['sort'] = 'popular'

        self.header['Authorization'] = 'Bearer %s' % self.access_token
        print('Token used:', self.access_token)
        for page in range(start_page, end_page+1):
            self.search_params['page'] = page
            r = self.session.get(self.search_url, headers=self.header, params=self.search_params)
            if r.status_code != 200:
                self.fatal('Search Error: %s' % r.text)
            r.encoding = 'utf-8'
            if log:
                self.log_json(r.text)
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

    def save_image_from_url(self, url, folder=''):
        file = os.path.basename(url)
        if not os.path.exists(os.path.join(folder, file)):
            with open(os.path.join(folder, file), 'wb+') as f:
                stream = self.session.get(url, headers=self.download_header, stream=True)
                f.write(stream.content)
            time.sleep(random.randint(1, 4))

    def save_images(self, debug=False):
        total = len(self.image_url_list)
        for i, u in enumerate(self.image_url_list):
            try:
                print('Saving illustration {:4d} of {:4d}...'.format(i, total), end='\r')
                self.save_image_from_url(u)
                if debug:
                    print('Successfully saved %s' % u)

            except Exception as e:
                print('Error in saving %s' % u)
                print(e)
        print('')

    def save_mangas(self):
        total = len(self.manga_id_list)
        for i, _id in enumerate(self.manga_id_list):
            print('Saving manga {:4d} of {:4d}...'.format(i, total), end='\r')
            r = self.session.get(self.illust_info_url % _id, headers=self.header)
            if r.status_code != 200:
                print('Error in getting detailed info on img\n%s' % r.text)
            j = self.json_to_object(r.text)
            for img in j.response[0].metadata.pages:
                self.save_image_from_url(img.image_urls.medium)
        print('')

    def clear(self):
        self.image_url_list = []
        self.manga_id_list = []

    def save_urls(self, suffix=''):
        with open('img_result' + suffix + '.json', 'w') as f:
            f.write(json.dumps(self.image_url_list))
        with open('manga_result' + suffix + '.json', 'w') as f:
            f.write(json.dumps(self.manga_id_list))

    def recover_urls(self, suffix=''):
        with open('img_result' + suffix + '.json', 'r') as f:
            self.image_url_list = json.loads(f.read())
        with open('manga_result' + suffix + '.json', 'r') as f:
            self.manga_id_list = json.loads(f.read())

    def test_run(self):
        self.test_access_token()
        self.get_access_token()
        self.test_access_token()

    def run(self, start_page=1, end_pages=100, log_search=False, save=True):
        self.search(start_page=start_page, end_page=end_pages, log=log_search)

        if save:
            self.save_images()
            self.save_mangas()

    def run_full(self, start=1, end=100):
        self.auth()
        for i in range(start, end + 2, 10):
            self.run(start_page=i, end_pages=i+9)
            self.save_urls('_{:02d}_{:02d}'.format(i, i+9))
            self.clear()
            print(i + 9, 'pages processed.')
            time.sleep(10)

    # used to generate ranking data, don't use
    def sch(self):
        self.header['Authorization'] = 'Bearer %s' % self.access_token
        print('Token used:', self.access_token)
        for page in range(1, 101):
            self.search_params['page'] = page
            r = self.session.get(self.search_url, headers=self.header, params=self.search_params)
            if r.status_code != 200:
                self.fatal('Search Error: %s' % r.text)
            r.encoding = 'utf-8'
            self.j = self.json_to_object(r.text)
            self.gen(page // 10)
            if self.j.pagination.next == 'null':
                break
            time.sleep(4)
            print('%2d pages processed' % page, end='\r')

    def gen(self, index):
        f = open(str(index), 'a')
        for res in self.j.response:
            f.write(str(res.id) + '\n')
        f.close()


if __name__ == '__main__':
    if os.path.exists(PixivBot.token_file):
        bft = " (leave blank to use exisiting token)"
    else:
        bft = ""
    username = input("Login (e.g. email){}: ".format(bft))
    password = getpass.getpass("Password{}: ".format(bft))
    tag = input("Tag (default 'めぐみん'): ").strip() or 'めぐみん'
    p = PixivBot(username=username, password=password, tag=tag)
    # p.run(start_page=1, end_pages=60, log_search=True, save=False)
    p.run_full(start=1)
    # p.sch()
