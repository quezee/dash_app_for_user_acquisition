import requests
import pandas as pd
import numpy as np
import json
from utils import PLATS
from time import sleep
from itertools import chain

with open('keys/api_keys.json') as f:
    MARKER = json.loads(f.read())['fb']

ACCOUNTS = {
    '769428786570565': 'Splitmetrics | Kefir!',
    '784629615050482': 'LDoE | Kefir! | Android',
    '784629325050511': 'LDoE | Kefir! | iOS',
    '169755003718782': 'Re-targeting LDoE | Kefir',
    '891211047725671': 'Grim Souls | Kefir!',
    '854774491369327': 'FOG | Kefir!',
    '454612108322849': 'Helio Games Ads'
}
FB_RETARGET_ACCOUNT = '169755003718782'
URL_BASE = 'https://graph.facebook.com/v3.2/{}/insights'


class FB_data:

    def __init__(self, accounts=ACCOUNTS, date_preset='last_90d', time_increment=1,
                 level='campaign', fields='campaign_name,spend', breakdowns='country',
                 limit=6000, action_breakdowns=None, time_range=None, time_range_step=None):
        self.accounts = accounts
        self.raw_data = {}
        self.headers = {
            'access_token': MARKER,
            'time_increment': time_increment,
            'level': level,
            'fields': fields,
            'breakdowns': breakdowns,
            'action_breakdowns': action_breakdowns,
            'limit': limit
        }
        if time_range:
            self.time_range_list = []

            if time_range_step:
                start_time_dt, end_time_dt = pd.Timestamp(time_range[0]), pd.Timestamp(time_range[1])
                left_bound = start_time_dt
                while left_bound < end_time_dt:
                    right_bound = left_bound + pd.Timedelta(time_range_step-1, unit='d')
                    right_bound = min(right_bound, end_time_dt)
                    start_time, end_time = left_bound.strftime('%Y-%m-%d'), right_bound.strftime('%Y-%m-%d')
                    self.time_range_list.append('{"since":"' + start_time + '","until":"' + end_time + '"}')
                    left_bound = right_bound + pd.Timedelta(1, unit='d')

            else:
                self.time_range_list.append('{"since":"' + time_range[0] + '","until":"' + time_range[1] + '"}')
                
        else:
            self.headers['date_preset'] = date_preset

    def connect(self, url, headers=None):
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
    
    def connect_and_paginate(self, url, account_id):
        req = self.connect(url, self.headers).json()
        print(f'  First req len: {len(req["data"])}')
        self.raw_data[account_id].extend(req['data'])
        if 'paging' in req:
            while 'next' in req['paging']:
                next_url = req['paging']['next']
                req = self.connect(next_url).json()
                print(f'  Next req len: {len(req["data"])}')
                self.raw_data[account_id].extend(req['data'])

    def get_raw_data(self, account_id):
        print(f'Account ID: {account_id}')
        url = URL_BASE.format(f'act_{account_id}')
        self.raw_data[account_id] = []
        if 'date_preset' in self.headers:
            self.connect_and_paginate(url, account_id)
        else:
            for time_range_str in self.time_range_list:
                print(f' Time range: {time_range_str}')
                self.headers['time_range'] = time_range_str
                self.connect_and_paginate(url, account_id)            

    def fill_platform(self):
        for plat in PLATS:
            idx = self.data[self.data.campaign_name.str.lower().str.contains(plat)].index
            self.data.loc[idx, 'Platform'] = plat
        idx_rest = self.data[self.data.Platform.isnull()].index
        acc_rest = self.data.loc[idx_rest, 'account_name']
        self.data.loc[idx_rest, 'Platform'] = acc_rest.str.lower().apply(lambda x: [plat for plat in PLATS if plat in x][0])
            
    def get_data(self, fill_platform=True):
        for account_id in self.accounts:
            self.get_raw_data(account_id)
            for row in self.raw_data[account_id]:
                row['account_name'] = self.accounts[account_id]
        data = list(chain.from_iterable(self.raw_data.values()))
        self.data = pd.DataFrame.from_dict(data)
        if fill_platform and 'campaign_name' in self.data:
            self.fill_platform()