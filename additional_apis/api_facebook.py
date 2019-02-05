import requests
import pandas as pd
import numpy as np
import json
from utils import PLATS
from time import sleep
from itertools import chain
from math import ceil

with open('keys/api_keys.json') as f:
    MARKER = json.loads(f.read())['fb']

ACCOUNTS = {
    '769428786570565': 'Splitmetrics | Kefir!',
    '784629615050482': 'LDoE | Kefir! | Android',
    '784629325050511': 'LDoE | Kefir! | iOS',
    '784629761717134': 'APAC LDoE | Kefir!',
    '169755003718782': 'Re-targeting LDoE | Kefir',
    '891211047725671': 'Grim Souls | Kefir!',
    '854774491369327': 'FOG | Kefir!',
    '454612108322849': 'Helio Games Ads'
}
FB_RETARGET_ACCOUNT = '169755003718782'
URL_BASE = 'https://graph.facebook.com/v3.2/{OBJECT_ID}/{ENDPOINT}'


class FB_data:

    def __init__(self, accounts=ACCOUNTS, date_preset='last_90d', time_increment=1,
                 level='campaign', fields='campaign_name,spend', breakdowns='country',
                 limit=6000, action_breakdowns=None,
                 time_range=None, time_range_step=None, time_ranges=None, time_ranges_step=None):
        self.accounts = accounts
        self.raw_data = {}
        self.time_range_list = []
        self.time_ranges_list = []
        self.params = {
            'access_token': MARKER,
            'time_increment': time_increment,
            'level': level,
            'fields': fields,
            'breakdowns': breakdowns,
            'action_breakdowns': action_breakdowns,
            'limit': limit
        }
        if time_range:

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
          
        
        elif time_ranges:
            
            if time_ranges_step:
                idx_start = 0
                while idx_start < len(time_ranges):
                    idx_end = idx_start + time_ranges_step
                    time_ranges_slice = time_ranges[idx_start:idx_end]
                    time_ranges_str = ['{"since":"' + time_range[0] + '","until":"' + time_range[1] + '"}'
                                       for time_range in time_ranges_slice]
                    time_ranges_str = '[' + ','.join(time_ranges_str) + ']'
                    self.time_ranges_list.append(time_ranges_str)
                    idx_start = idx_end
                
            else:
                time_ranges_str = ['{"since":"' + time_range[0] + '","until":"' + time_range[1] + '"}' for time_range in time_ranges]
                time_ranges_str = '[' + ','.join(time_ranges_str) + ']'
                self.time_ranges_list.append(time_ranges_str)

                
        else:
            self.params['date_preset'] = date_preset

    def connect(self, url, params=None):
        connected = False
        while not connected:
            try:
                req = requests.get(url, params)
                req_json = req.json()
                if 'error' in req_json:
                    raise Exception(req_json['error']['message'])
                connected = True
            except Exception as e:
                print(f'   {str(e)}\n   reconnecting...')
                sleep(2)
        sleep(3)
        return req
    
    def connect_and_paginate(self, url, object_id):
        req = self.connect(url, self.params).json()
        print(f'  First req len: {len(req["data"])}')
        self.raw_data[object_id].extend(req['data'])
        if 'paging' in req:
            while 'next' in req['paging']:
                next_url = req['paging']['next']
                req = self.connect(next_url).json()
                print(f'  Next req len: {len(req["data"])}')
                self.raw_data[object_id].extend(req['data'])

    def get_raw_data(self, object_id):
        print(f'Account ID: {object_id}')
        url = URL_BASE.format(OBJECT_ID=f'act_{object_id}', ENDPOINT='insights')
        self.raw_data[object_id] = []
        if self.time_range_list:
            for time_range_str in self.time_range_list:
                print(f' Time range: {time_range_str}')
                self.params['time_range'] = time_range_str
                self.connect_and_paginate(url, object_id)
                self.params.pop('time_range')
        elif self.time_ranges_list:
            for time_ranges_str in self.time_ranges_list:
                print(f' Time ranges: {time_ranges_str}')
                self.params['time_ranges'] = time_ranges_str
                self.connect_and_paginate(url, object_id)
                self.params.pop('time_ranges')
        else:
            self.connect_and_paginate(url, object_id)

    def fill_platform(self):
        for plat in PLATS:
            idx = self.data[self.data.campaign_name.str.lower().str.contains(plat)].index
            self.data.loc[idx, 'Platform'] = plat
        idx_rest = self.data[self.data.Platform.isnull()].index
        acc_rest = self.data.loc[idx_rest, 'account_name']
        self.data.loc[idx_rest, 'Platform'] = acc_rest.str.lower().apply(lambda x: [plat for plat in PLATS if plat in x][0])
            
    def get_data(self, fill_platform=True):
        for object_id in self.accounts:
            self.get_raw_data(object_id)
            for row in self.raw_data[object_id]:
                row['account_name'] = self.accounts[object_id]
        data = list(chain.from_iterable(self.raw_data.values()))
        self.data = pd.DataFrame.from_dict(data)
        if fill_platform and 'campaign_name' in self.data:
            self.fill_platform()
            
            
class FB_adset_meta(FB_data):
    
    def __init__(self, adset_ids, limit=6000, fields='start_time,end_time,optimization_goal,attribution_spec,billing_event,bid_amount,daily_budget,targeting,status,bid_strategy'):
        
        self.raw_data = []
        self.adset_ids = adset_ids
        self.params = {
            'access_token': MARKER,
            'fields': fields,
            'limit': limit
        }
        
    def get_raw_data(self, object_id):
        print(f'Adset ID: {object_id}')
        url = URL_BASE.format(OBJECT_ID=object_id, ENDPOINT='')
        req = self.connect(url, self.params)
        self.raw_data.append(req.json())
    
    def get_data(self):
        for object_id in self.adset_ids:
            self.get_raw_data(object_id)
        self.data = pd.DataFrame.from_dict(self.raw_data)
        self.data.set_index('id', inplace=True)
    
    
    
    
                 