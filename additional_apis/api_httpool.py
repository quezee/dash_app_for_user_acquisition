import pandas as pd
import numpy as np

import requests

from io import BytesIO

from utils import USDRUB

from api_google_sheets import GoogleSheet
gs = GoogleSheet()

URLs_DATA = [
    'https://get.httpool.com/lv/report/77091e07cfb0408183bfd91eed601b3b/lang/en',
    'https://get.httpool.com/pn_tw/report/3930e57a2cef4dbca86d13a5e3cce31e/lang/en',
    'https://get.httpool.com/pn_tw/report/a61987ea9f6849c9ad86214f0eb898ea/lang/en'
]
URL_RENAMES = 'https://docs.google.com/spreadsheets/d/1c7tZKUOcOU2239QqCpkbzcivq2yiRAxCI05LngBPmJU'
HPOOL_RETARGET_URL = 'https://get.httpool.com/pn_tw/report/a61987ea9f6849c9ad86214f0eb898ea/lang/en'
BORDER_DATE = '2018-08-20'
USECOLS = ['Ad campaign', 'Date', 'App installs', 'Spent']
RENAMES_OLD = {
    'httpoolmpu_iOS_Gaming_Male_Japan': 'httpoolmpu_iOS_Streamers_Male_Japan',
    'httpoolmpu_iOS_Gaming_Male_USA': 'httpoolmpu_iOS_Streamers_Male_USA',
    'httpoolmpu_iOS_Gaming_Male_UK': 'httpoolmpu_iOS_Streamers_Male_UK',
    'httpoolmpu_iOS_Gaming_Male_USA_TAP': 'httpoolmpu_iOS_Gaming_Male_USA_UK_Canada_TAP',
    ' httpoolmpu_KR_MAP_iOS_Streamers': 'httpoolmpu_KR_MAP_iOS_Streamers'
}


class Httpool_data:
    
#    __init__ не заводим, т.к. здесь нет переменных для инициализации
 
    def get_data(self):
        
        url_datas = []
        
        for url in URLs_DATA:
            req = requests.get(url, verify=False)
            csv = BytesIO(req.content)
            url_data = pd.read_csv(csv, usecols=USECOLS)
            url_data['url'] = url
            url_data['Date'] = pd.to_datetime(url_data['Date'], dayfirst=True)
            if url == 'https://get.httpool.com/pn_tw/report/3930e57a2cef4dbca86d13a5e3cce31e/lang/en':
                url_data = url_data[url_data['Date'] > BORDER_DATE]
            url_datas.append(url_data)

        self.data = pd.concat(url_datas, ignore_index=True)

    def get_renames(self):
        renames = gs.open_url(URL_RENAMES)
        renames = pd.DataFrame(renames.worksheet('Sheet1').get_all_records())
        renames = renames[renames['New campaign name'] != 'paused']
        renames = renames.set_index('Old campaign name')['New campaign name'].to_dict()
        renames.update(RENAMES_OLD)
        self.renames = renames
        
    def transform_data(self):
        
        self.data['install_week'] = self.data['Date'].dt.to_period('W')
        self.data['install_year_month'] = self.data['Date'].dt.strftime('%Y-%m')
        
        self.data['Spent'] = self.data['Spent'].str.slice(4).str.replace(',','').astype('float')
        self.data['Spent USD'] = self.data['Spent'] / self.data['install_year_month'].map(USDRUB)

        self.data.rename(columns={
            'Ad campaign': 'Campaign',
            'Date': 'Install Day',
            'Spent USD': 'Cost Value'
        }, inplace=True)
        
        self.data['Campaign'].replace(self.renames, inplace=True)        
        
    def get_and_transform(self):
        
        self.get_data()
        self.get_renames()
        self.transform_data()