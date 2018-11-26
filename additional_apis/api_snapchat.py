import requests
import pandas as pd
import numpy as np
import json
from pandas.io.json import json_normalize

with open('keys/api_keys.json') as f:
    api_keys = json.loads(f.read())['snap']
    CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, ADACCOUNT_ID = (api_keys['client_id'], api_keys['client_secret'],
                                                             api_keys['refresh_token'],
                                                             api_keys['adaccount_id'])

ISO_POSTFIX = 'T00:00:00.00%2B03'


def get_code():
    url = f'https://accounts.snapchat.com/login/oauth2/authorize?\
response_type=code&\
client_id={CLIENT_ID}&\
redirect_uri=https%3A%2F%2Fkefirgames.ru&\
scope=snapchat-marketing-api'
    print(url)
    
def get_tokens(code):
    url = f'https://accounts.snapchat.com/login/oauth2/access_token?\
grant_type=authorization_code&\
client_id={CLIENT_ID}&\
client_secret={CLIENT_SECRET}&\
code={CODE}'
    req = requests.post(url)
    return req.json()


class Snap_data:
    
    def __init__(self, start_time, end_time, fields='spend', campaign_ids=None):
        
        end_time_dt, start_time_dt = pd.Timestamp(end_time), pd.Timestamp(start_time)
        timedelta = (end_time_dt - start_time_dt).days
        if timedelta > 32:
            print('Timedelta exceeds 32 days, breaking the timespan down')
            self.from_to = []
            left_bound = start_time_dt
            while left_bound < pd.Timestamp(end_time):
                right_bound = left_bound + pd.Timedelta(32, unit='d')
                right_bound = min(right_bound, end_time_dt)
                self.from_to.append((left_bound.strftime('%Y-%m-%d'),
                                     right_bound.strftime('%Y-%m-%d')))
                left_bound = right_bound
        else:
            self.from_to = [(start_time, end_time)]
            
        self.campaign_ids = campaign_ids
        self.auth_header = None
        self.url_base = 'https://adsapi.snapchat.com/v1/{}/{}/stats?'
        self.params = {
            'breakdown': 'ad',
            'fields': fields,
            'granularity': 'DAY'
        }
        
        
    def get_auth_header(self):
        url = f'https://accounts.snapchat.com/login/oauth2/access_token?grant_type=refresh_token&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={REFRESH_TOKEN}'
        req = requests.post(url)
        access_token = req.json()['access_token']
        self.auth_header = {"Authorization": f"Bearer {access_token}"}
        
    def api_connect(self, url):
        if not self.auth_header:
            print('Getting auth header')
            self.get_auth_header()
        connected = False
        while not connected:
            req = requests.get(url, headers=self.auth_header)
            if req.status_code == 401:
                print('\nRefreshing auth header')
                self.get_auth_header()
            elif req.status_code != 200:
                print(req.text)
                break
            else:
                print('\nRequest succeeded')
                connected = True
        return req
        
    def get_campaign_ids(self):
        print('\nGetting campaign ids')
        url = f'https://adsapi.snapchat.com/v1/adaccounts/{ADACCOUNT_ID}/campaigns'
        req = self.api_connect(url)
        campaigns = req.json()['campaigns']
        self.campaign_ids = [item['campaign']['id'] for item in campaigns]
        
    def get_campaign_data(self, campaign_id, start_time, end_time):
        url = self.url_base.format('campaigns', campaign_id)
        self.params['start_time'] = start_time + ISO_POSTFIX
        self.params['end_time'] = end_time + ISO_POSTFIX
        url_params = '&'.join([f'{key}={value}' for key, value in self.params.items()])
        req = self.api_connect(url + url_params)
        ads = req.json()['timeseries_stats'][0]['timeseries_stat']['breakdown_stats']['ad']
        data_camp = pd.DataFrame()
        for ad in ads:
            data_ad = pd.DataFrame(ad['timeseries'])
            data_ad['ad_id'] = ad['id']
            data_camp = pd.concat([data_camp, data_ad], ignore_index=True)
        data_camp['campaign_id'] = campaign_id
        print(f'Loaded campaign {campaign_id} {start_time}/{end_time}: {len(data_camp)} rows')
        return data_camp
    
    def get_data(self):
        data = []
        if not self.campaign_ids:
            self.get_campaign_ids()
        for campaign_id in self.campaign_ids:
            print('\n')
            for start_time, end_time in self.from_to:
                data_camp = self.get_campaign_data(campaign_id, start_time, end_time)
                data.append(data_camp)
        self.data = pd.concat(data, ignore_index=True)
        self.data = pd.concat([self.data, json_normalize(self.data.stats)],
                              1, sort=True)
        
        self.data['Install Day'] = pd.to_datetime(self.data.start_time.str.slice(0, 10))
        self.data['spend'] = self.data.spend / 1e6