import requests
import pandas as pd
import numpy as np
import json
from utils import PLATS
from time import sleep
from itertools import chain

with open('keys/api_keys.json') as f:
    MARKER = json.loads(f.read())['fb']

ACCOUNT_IDS = ['784629615050482', '784629325050511', '169755003718782', '891211047725671']
ACCOUNT_NAMES = ['LDoE | Kefir! | Android', 'LDoE | Kefir! | iOS',
                 'Re-targeting LDoE | Kefir', 'Grim Souls | Kefir!']
FB_RETARGET_ACCOUNT = '169755003718782'
URL_BASE = 'https://graph.facebook.com/v3.2/{}/insights'


class FB_data:

    def __init__(self, account_ids=ACCOUNT_IDS, date_preset='last_90d', time_increment=1,
                 level='campaign', fields='campaign_name,spend', breakdowns='country',
                 time_range=None):
        self.account_ids = account_ids
        self.raw_data = {}
        self.headers = {
            'access_token': MARKER,
            'date_preset': date_preset,
            'time_increment': time_increment,
            'level': level,
            'fields': fields,
            'breakdowns': breakdowns,
            'limit': 6000
        }
        if time_range:
            time_range_formatted = '{"since":"' + time_range[0] + '","until":"' + time_range[1] + '"}'
            self.headers['time_range'] = time_range_formatted

    def api_connect(self, url, headers=None):
        connected = False
        while not connected:
            try:
                req = requests.get(url, headers)
                req_json = req.json()
                if 'error' in req_json:
                    raise Exception(req_json['error']['message'])
                connected = True
            except Exception as e:
                print(f'   {str(e)}\n   reconnecting...')
                sleep(2)
        return req

    def get_raw_data(self, account_id):
        print(f'Account ID: {account_id}')
        url = URL_BASE.format(f'act_{account_id}')
        req = self.api_connect(url, self.headers).json()
        print(f'  First req len: {len(req["data"])}')
        self.raw_data[account_id] = req['data']
        while 'next' in req['paging']:
            next_url = req['paging']['next']
            req = self.api_connect(next_url).json()
            print(f'  Next req len: {len(req["data"])}')
            self.raw_data[account_id].extend(req['data'])

    def fill_platform(self):
        for plat in PLATS:
            idx = self.data[self.data.campaign_name.str.lower().str.contains(plat)].index
            self.data.loc[idx, 'Platform'] = plat
        idx_rest = self.data[self.data.Platform.isnull()].index
        acc_rest = self.data.loc[idx_rest, 'account_name']
        self.data.loc[idx_rest, 'Platform'] = acc_rest.str.lower().apply(lambda x: [plat for plat in PLATS if plat in x][0])
            
    def get_data(self, fill_platform=True):
        for i, account_id in enumerate(self.account_ids):
            self.get_raw_data(account_id)
            for row in self.raw_data[account_id]:
                row['account_name'] = ACCOUNT_NAMES[i]
        data = list(chain.from_iterable(self.raw_data.values()))
        self.data = pd.DataFrame.from_dict(data)
        if fill_platform:
            self.fill_platform()