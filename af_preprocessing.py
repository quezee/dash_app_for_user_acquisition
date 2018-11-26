import numpy as np
import pandas as pd

from utils import *  # константы для преобразования данных (налоги, переименования, курс USD/RUB на месяц и т.д.)

from additional_apis.api_google_sheets import GoogleSheet; gs = GoogleSheet()  # для получения данных из таблиц в Google Sheets
from additional_apis.api_facebook import FB_RETARGET_ACCOUNT, FB_data # для получения данных из Facebook Ads API
from additional_apis.api_httpool import HPOOL_RETARGET_URL, Httpool_data # для получения данных из сервиса Httpool

NOW = pd.Timestamp.today().floor('s')
TODAY = pd.Timestamp.today().floor('d')

class AF_data:
    
    def __init__(self):
        """Заводим даты отсечки данных и др. вспомогательные переменные, вытягиваем сырые данные SQL запросом"""
        
        self.start_day = TODAY - pd.Timedelta(DATE_PRESET, unit='D')
        self.end_day = TODAY - pd.Timedelta(1, unit='d')
        
        # доп. данные от API некоторых рекламных сеток
        self.additional_data = {}
        
        # словарь, ключами которого будут источники (Media Source) из константы NULL_COST_MEDIAS, а значениями -
        # листы сплитов (названий колонок), по которым будет осуществляться мэтчинг поля Cost Value к главной таблице;
        # у каждого Media Source свой сплит, т.к. разбивки, по которым они предоставляют данные, могут быть разными
        self.matching_splits = {}
        
        # наименования ретаргетовых кампаний
        self.retarget_campaigns = set()
        
#        self.installs = *SQL request* (пакуем данные AppsFlyer об установках в pandas.DataFrame)
#        self.inapps = *SQL request* (пакуем данные AppsFlyer о платежах в pandas.DataFrame)
    
    def get_taxes(self):
        """Получаем налоговые коэффициенты по странам (из таблицы в Google Sheets) и мапим их к self.installs"""
        
        tax_sheet = gs.open_url('https://docs.google.com/spreadsheets/d/1njakgwWL4BaRck5yDgHbBBBEiMKA4ErgmsykUh-u4hg')
        tax_ws = tax_sheet.worksheet('iOS Store tax').get_all_values()[1:]
        self.country_taxes = {country: float(tax.replace(',', '.')) for country, tax in tax_ws}
        
    def get_fb_data(self):
        """Получаем и преобразовываем дополнительные данные из Facebook Ads API"""
        
        if DATE_PRESET != 90:
            # Если мы смотрим на данные не за последние 90 дней, то запрос к API должен делаться через параметр
            # time_range (а не date_preset)
            time_range = (self.start_day.strftime(DT_FMT), self.end_day.strftime(DT_FMT))
            fb_data = FB_data(date_preset=None, time_range=time_range)
        else:
            # Иначе - инициализируем объект по умолчанию
            fb_data = FB_data()
        
        # запрашиваем данные
        fb_data.get_data()
        
        # вносим в данные корректировки для совместимости
        fb_data.data['country'].replace({'GB': 'UK'}, inplace=True)
        fb_data.data['spend'] = fb_data.data['spend'].astype(np.float32)
        fb_data.data.rename(columns={
            'campaign_name': 'Campaign',
            'country': 'Country Code',
            'date_start': 'Install Day',
            'spend': 'Cost Value'
        }, inplace=True)
        fb_data.data['Install Day'] = pd.to_datetime(fb_data.data['Install Day'])

        # накидываем налог на spend, Campaign которых содержит строку 'bidalgo_'
        filt = fb_data.data['Campaign'].str.contains('bidalgo_')
        bidalgo_idx = fb_data.data.index[filt]
        fb_data.data.loc[bidalgo_idx, 'spend'] = fb_data.data.loc[bidalgo_idx, 'spend'] * BIDALGO_TAX_MULT
        
        # coхраняем данные
        self.additional_data['Facebook Ads'] = fb_data.data
        
        # сохраняем лист сплитов, по которым будем мэтчить поле Cost Value
        self.matching_splits['Facebook Ads'] = [
            ('Install Day', 'Campaign', 'Country Code'),
            ('Install Day', 'Campaign')
        ]
        # coхраняем массив ретаргет кампаний
        retarget_campaigns = {item['campaign_name'] for item in fb_data.raw_data[FB_RETARGET_ACCOUNT]}
        self.retarget_campaigns.update(retarget_campaigns)        
        
    def get_snap_data(self):
        """Получаем и преобразовываем дополнительные данные из Snap Ads API"""
        
        snap_campaign_ids = self.data['Campaign ID'][self.data['Media Source'] == 'snapchat_int'].unique().tolist()
        
        snap_data = Snap_data(self.start_day.strftime(DT_FMT), TODAY.strftime(DT_FMT),
                              'spend', snap_campaign_ids)
        snap_data.get_data()
        
        # вносим в данные корректировки для совместимости
        snap_data.data.rename(columns={
            'ad_id': 'Ad ID',
            'campaign_id': 'Campaign ID',
            'spend': 'Cost Value'
        }, inplace=True)
        
        # coхраняем данные
        self.additional_data['snapchat_int'] = snap_data.data
        
        # сохраняем лист сплитов, по которым будем мэтчить поле Cost Value
        self.matching_splits['snapchat_int'] = [
            ('Install Day', 'Campaign ID', 'Ad ID'),
            ('Install Day', 'Campaign ID')
        ]

    def get_httpool_data(self):
        """Получаем и преобразовываем дополнительные данные из сервиса Httpool (Twitter)"""
        
        # запрашиваем и преобразовываем данные
        httpool_data = Httpool_data()
        httpool_data.get_and_transform()
        
        httpool_data.data = httpool_data.data[httpool_data.data['Install Day'].between(self.start_day, self.end_day)]
        
        # coхраняем данные, массив ретаргет кампаний и словарь для переименований кампаний в self
        self.additional_data['Twitter'] = httpool_data.data
        
        # сохраняем лист сплитов, по которым будем мэтчить поле Cost Value
        self.matching_splits['Twitter'] = [
            ('Campaign', 'Install Day'),
            ('Campaign', 'Install Week')
        ]                
        retarget_campaigns = set(httpool_data.data[httpool_data.data['url'] == HPOOL_RETARGET_URL]['Campaign'])
        self.retarget_campaigns.update(retarget_campaigns)
        
        self.httpool_renames = httpool_data.renames
        
    def transform_inapps(self):
        """Часть платежей в данных Аппсфлаера временно некорректна (LDoE iOS), поэтому мы подтягиваем этот кусок
        из другой аналитической системы руками (Devtodev) и интегрируем в self.inapps (пока не понятно можно ли
        будет это делать через API).
        Потом корректируем значения некоторых колонок в self.inapps."""

#        inapps_d2d = *SQL request или подтягивать руками*
        self.inapps = pd.concat([self.inapps, inapps_d2d], ignore_index=True)
    
        self.inapps[ID].fillna(self.inapps['AppsFlyer ID'], inplace=True)

    def transform_installs(self):
        """Удаляем дубликаты по определенным колонкам, корректируем значения некоторых колонок,
        добавляем данные, сортируем"""
        
        self.installs.drop_duplicates(subset=[ID, 'Attributed Touch Time'], keep='first', inplace=True)
        self.installs.drop_duplicates(subset=[ID, 'Install Time'], keep='first', inplace=True)
        
        self.installs['App Name'].replace(APP_RENAMES, inplace=True)
        self.installs['Media Source'].fillna(self.installs['Partner'], inplace=True)        
        self.installs[ID].fillna(self.installs['AppsFlyer ID'], inplace=True)
        
        self.installs['tax_country'] = self.installs['Country Code'].map(self.country_taxes).fillna(TAX_OTHERS)
        
        self.installs['Is Retarget Campaign'] = self.installs['Campaign'].isin(self.retarget_campaigns)
        self.installs['Days in game'] = (TODAY - self.installs['Install Time']).dt.total_seconds() / SECONDS_IN_DAY
        
        self.installs['Install Day'] = self.installs['Install Time'].dt.floor('d')
        self.installs['Install Week'] = self.installs['Install Time'].dt.to_period('W')
        
        # вводим колонку с флагом того, является ли данный инсталл ретаргетовым (позже отметим где True)
        self.installs['retarget_event'] = False

        for col in MEDIA_RELATED_COLS:
            self.installs[col].fillna('', inplace=True)
        
        self.installs.sort_values([ID, 'Install Time'], inplace=True)
        
    def separate_data(self):
        """Для правильного отнесения платежей на юзеров по нашей методологии, требуется сначала разбить таблицы
        инсталлов и платежей на относящиеся к неповторяющимся юзерам (по которым прилетал только 1 инсталл)
        и к повторяющимся (неск. инсталлов, т.к. они попали под ретаргетинг)"""
        
        user_counts = self.installs[ID].value_counts()
        duplicate_users = user_counts[user_counts > 1].index.tolist()
        
        self.installs_dup = self.installs[self.installs[ID].isin(duplicate_users)]
        self.installs_unq = self.installs[~self.installs[ID].isin(duplicate_users)]
        del self.installs
        
        self.inapps_dup = self.inapps[self.inapps[ID].isin(duplicate_users)]
        self.inapps_unq = self.inapps[~self.inapps[ID].isin(duplicate_users)]
        del self.inapps
        
    def detect_retarget_installs(self):
        """Перед отнесением платежей на повторяющихся юзеров (из self.installs_dup) требуется определить
        какие из их установок являются ретаргетовым событием.
        А именно, это установки, выполняющие одновременно 3 условия:
          1. первая установка у данного юзера произошла по неретаргетовой кампании
          2. установка является непервой у данного юзера
          3. установка произошла по ретаргетовой кампании"""
        
        # получаем соответствие между юзер ID и флагом того, произошла ли его первая установка по ретаргет кампании 
        first_campaign_is_retarget = self.installs_dup.groupby(ID)['Is Retarget Campaign'].first()
        # выделяем юзеров, изначально пришедших по неретаргетовой кампании
        users_from_nonret = first_campaign_is_retarget[first_campaign_is_retarget == False].index.tolist()
        
        # выделяем индексы инсталлов, выполняющих все 3 условия
        ret_event_idx = self.installs_dup[
            (self.installs_dup[ID].isin(users_from_nonret))&     # 1.
            (self.installs_dup[ID].duplicated())&                # 2.
            (self.installs_dup['Is Retarget Campaign'] == True)  # 3.
        ].index.tolist()

        # отмечаем ретаргетовые инсталлы, индексы сохраняем в self
        self.installs_dup.loc[ret_event_idx, 'retarget_event'] = True
        self.ret_event_idx = ret_event_idx
        
    def transform_retarget_installs(self):
        """Значения некоторых колонок (MEDIA_RELATED_COLS) у ретаргетовых установок должны быть заменены
        на значения у этих же юзеров во время первого инсталла.
        Т.е. мы обнуляем эти значения и заполняем их методом 'forward fill'.
        При этом значения, удаляемые из колонок 'Media Source' и 'Campaign' должны быть предварительно сохранены в
        колонках с аналогичным названием и припиской 'Retarget' (чтобы запомнить по какому 'Media Source' и 'Campaign'
        произошёл ретаргет)."""
        
        for col in MEDIA_RELATED_COLS:
            if col in ['Media Source', 'Campaign']:
                self.installs_dup[f'Retarget {col}'] = self.installs_dup.loc[self.ret_event_idx, col]
            self.installs_dup.loc[self.ret_event_idx, col] = None
            self.installs_dup[col].fillna(method='ffill', inplace=True)
            
    def calculate_inapp_dates_for_dup_users(self):
        """Платежи у нас по сути мапятся не к юзер ID, а к инсталлам, поэтому маппинг платежей к
        повторяющимся юзерам усложняется.
        Сейчас с момента инсталла мы относим платежи по данному ID в течение 60 дней. Если юзер повторно установился
        до окончания этого окна, то к этому повторному инсталлу будут относиться платежи юзера, совершенные после
        окончания предыдущего окна и не позднее 60 дней с момента повторного инсталла.
        
        В этом методе для каждой установки платящего юзера из self.installs_dup мы определяем временное окно,
        в котором платежи от этого юзера будут относиться именно на эту его установку."""
        
        # извлекаем повторяющихся юзеров, по которым есть платежи
        payers_dup = set(self.inapps_dup[ID])
        # делим self.installs_dup на платящих (_p) и неплатящих (_np) (чтобы не считать платёжные окна для неплатящих)
        # и дальше работаем только с первой таблицей
        self.installs_dup_p = self.installs_dup[self.installs_dup[ID].isin(payers_dup)]
        self.installs_dup_np = self.installs_dup[~self.installs_dup[ID].isin(payers_dup)]
        del self.installs_dup
        
        # заводим индексы первых и последних появлений каждого юзера (ID)
        filt = ~self.installs_dup_p[ID].duplicated()
        first_occur_idx = self.installs_dup_p.index[filt]
        filt = ~self.installs_dup_p[ID].duplicated('last')
        last_occur_idx = self.installs_dup_p.index[filt]
        
        # Если у юзера эта установка - первая, то дата начала отнесения платежей к ней будет равна дате самой установки
        self.installs_dup_p['inapps_from'] = self.installs_dup_p.loc[first_occur_idx, 'Install Time']
        # Дата конца отнесения платежей на любую (кроме последней) установку наступает через OBSERV_SPAN дней (60)
        self.installs_dup_p['inapps_to'] = self.installs_dup_p['Install Time'] + pd.Timedelta(OBSERV_SPAN, unit='d')
        # Для последней установки юзера заменяем дату конца отнесения платежей на NOW,
        # чтобы не терять платежи, которые могли быть сделаны после последнего окна
        self.installs_dup_p.loc[last_occur_idx, 'inapps_to'] = NOW
        
        # Теперь нужно поправить даты начала отнесения платежей для установок, являющихся непервыми у данного юзера,
        # чтобы диапазоны inapps_from-inapps_to для всех его установок не пересекались между собой
        filt = self.installs_dup_p[ID].duplicated()
        repeat_idx = self.installs_dup_p.index[filt]
        # С помощью такого сдвига получаем концы предыдущих окон для каждой непервой установки
        # (+1 милисекунда, т.к. для расчетов будут использоваться [закрытые] интервалы)
        prev_inapps_to = self.installs_dup_p['inapps_to'].shift().loc[repeat_idx] + pd.Timedelta(1, unit='ms')
        # Теперь для каждой непервой установки нужно в качестве 'inapps_from' назначить либо дату этой установки,
        # либо конец окна предыдущей установки - смотря что произошло позже
        current_inst_time = self.installs_dup_p.loc[repeat_idx, 'Install Time']
        inapps_from_for_repeat_idx = pd.DataFrame([prev_inapps_to, current_inst_time]).max()
        self.installs_dup_p.loc[repeat_idx, 'inapps_from'] = inapps_from_for_repeat_idx
        
    def calculate_metrics_for_dup(self):
        """Мэтчим платежи к повторным юзерам и считаем метрики:
         - gross - сумма платежей в USD
         - inapps_count - количество платежей
        Примечание: каждая метрика считается несколько раз - по когортам - т.е. только платежи,
        совершенные в первые сутки, третьи сутки, в месяц инсталла и т.д. (константа COHORTS)"""
        
        # сортируем платежи повторных юзеров по юзер ID и времени платежа
        self.inapps_dup.sort_values([ID, 'Event Time'], inplace=True)
        
        # таблицу платежей индексируем по ID и 'Event Time' - так извлечение конкретного ID и его платежей
        # в определённом окне будет быстрее, чем если бы мы обращались к датафрейму через фильтрацию ID и 'Event Time'
        self.inapps_dup.set_index([ID, 'Event Time'], inplace=True)
        
        # создаём колонку с таймстэмпом конца месяца инсталла (понадобится для расчёта когорты 'month')
        self.installs_dup_p['inst_month_end'] = self.installs_dup_p['Install Time'].apply(
            lambda dt: dt.replace(day=dt.daysinmonth, hour=23, minute=59, second=59)
        )
        
        # этот цикл - самый медлительный фрагмент кода (2 мин * 8 итераций)
        # обходим каждую когорту и считаем для неё метрики (по каждому инсталлу у повторяющихся юзеров)
        for cohort in COHORTS:

            # в этой серии if-ов вводится колонка 'inapps_to_cohort' - таймстэмп до которого мы относим платежи на установку
            if cohort is None:
                # когорта отсутствует - метрики считаются по всем платежам юзера (до конца окна)
                gross_col = 'gross'
                inapps_count_col = 'inapps_count'
                self.installs_dup_p['inapps_to_cohort'] = self.installs_dup_p.inapps_to
            elif cohort == 'month':
                # платежи до конца месяца инсталла (либо до конца окна, если оно наступило раньше)
                gross_col = 'gross_month'
                inapps_count_col = 'inapps_count_month'
                self.installs_dup_p['inapps_to_cohort'] = self.installs_dup_p[['inst_month_end', 'inapps_to']].min(1)
            else:
                # платежи до дня 'cohort' с момента инсталла (либо до конца окна, если оно наступило раньше)
                gross_col = f'gross_{cohort}'
                inapps_count_col = f'inapps_count_{cohort}'
                self.installs_dup_p['inapps_to_cohort'] = self.installs_dup_p['Install Time'] + pd.Timedelta(cohort, unit='d')
                self.installs_dup_p['inapps_to_cohort'] = self.installs_dup_p[['inapps_to_cohort', 'inapps_to']].min(1)

            # каждому инсталлу присваиваем лист аргументов, которые будут инпутом в
            # функцию для отнесения на этот инсталл платежей
            matching_args = self.installs_dup_p[[ID, 'inapps_from', 'inapps_to_cohort']].apply(list, 1)
            # проходим по каждому листу аргументов и получаем массив платежей (self.match_inapps_dup реализован ниже)
            inapps_matched = matching_args.apply(self.match_inapps_dup)
            
            # из получившихся массивов считаем суммы и каунты платежей
            self.installs_dup_p[gross_col] = inapps_matched.apply(sum)
            self.installs_dup_p[inapps_count_col] = inapps_matched.apply(len)

            # заменяем нули на пропуски (для однородности - у неплатящих там тоже будут пропуски)
            self.installs_dup_p[gross_col].replace({0: np.nan}, inplace=True)
            self.installs_dup_p[inapps_count_col].replace({0: np.nan}, inplace=True)
            
        # удаляем вспомогательные колонки
        self.installs_dup_p.drop(['inapps_to_cohort', 'inst_month_end'], axis=1, inplace=True)
    
    def match_inapps_dup(self, args):
        """Принимает в качестве аргументов лист из [ID, начало и конец платежного окна].
        Возвращает массив платежей (в USD).
        Используется в методе self.calculate_metrics_for_dup."""

        inapps = self.inapps_dup.loc[args[0], 'Event Revenue USD'][args[1]:args[2]]
        return inapps.values
        
    def calculate_metrics_for_unq(self):
        """Мэтчим платежи к уникальным юзерам и считаем метрики:
         - gross - сумма платежей в USD
         - inapps_count - количество платежей
        Примечание: здесь нет никаких платёжных окон, т.к. 1 юзер == 1 установка"""
        
        # извлекаем уникальных юзеров, по которым есть платежи
        payers_unq = set(self.inapps_unq[ID])
        # делим self.installs_unq на платящих (_p) и неплатящих (_np) и дальше работаем только с первой таблицей
        self.installs_unq_p = self.installs_unq[self.installs_unq[ID].isin(payers_unq)]
        self.installs_unq_np = self.installs_unq[~self.installs_unq[ID].isin(payers_unq)]
        del self.installs_unq
        
        # в кач-ве индекса установим ID, т.к. будем вставлять в эту таблицу колонки с метриками,
        # где индексом так же будет ID
        self.installs_unq_p.set_index(ID, inplace=True)
        
        # заменяем в self.inapps_unq существующий 'Install Time' на тот, который указан у этих же юзеров
        # в таблице инсталлов, чтобы избежать возможных несоответствий
        self.inapps_unq['Install Time'] = self.inapps_unq[ID].map(self.installs_unq_p['Install Time'])
        # оставляем только те платежи 'Event Time', которых произошёл после 'Install Time'
        self.inapps_unq = self.inapps_unq[self.inapps_unq['Event Time'] >= self.inapps_unq['Install Time']]
        
        # создаём колонку с таймстэмпом конца месяца инсталла (понадобится для расчёта когорты 'month')
        self.inapps_unq['inst_month_end'] = self.inapps_unq['Install Time'].apply(
            lambda dt: dt.replace(day=dt.daysinmonth, hour=23, minute=59, second=59)
        )        
        
        # считаем разницу между датой платежа и датой инсталла (в днях)
        self.inapps_unq['datediff'] = (self.inapps_unq['Event Time'] - self.inapps_unq['Install Time']) \
                                        .dt.total_seconds() / SECONDS_IN_DAY
            
        # так же как и в случае с _dup обходим когорты, но теперь расчёты гораздо проще в виду отсутствия окон 
        for cohort in COHORTS:
    
            if cohort is None:
                gross_col = 'gross'
                inapps_count_col = 'inapps_count'
                inapps_matched = inapps_unq
            elif cohort == 'month':
                gross_col = 'gross_month'
                inapps_count_col = 'inapps_count_month'
                inapps_matched = self.inapps_unq[self.inapps_unq['Event Time'] <= self.inapps_unq['inst_month_end']]
            else:
                gross_col = f'gross_{cohort}'
                inapps_count_col = f'inapps_count_{cohort}'
                inapps_matched = self.inapps_unq[self.inapps_unq['datediff'] <= cohort]

            grouper = inapps_matched.groupby(ID)

            self.installs_unq_p[gross_col] = grouper['Event Revenue USD'].sum()
            self.installs_unq_p[inapps_count_col] = grouper.size()
        
        # возвращаем ID из индекса обратно в колонку (для дальнейшей совместимости) 
        self.installs_unq_p.reset_index(inplace=True)
        
    def merge_installs(self):
        """Склеиваем все installs_ таблицы в единый датафрейм."""
        
        self.data = pd.concat([self.installs_dup_p, self.installs_dup_np,
                               self.installs_unq_p, self.installs_unq_np],
                              ignore_index=True, sort=True)
        
        del self.installs_dup_p, self.installs_dup_np, self.installs_unq_p, self.installs_unq_np
        
    def fill_na_costs(self):
        """Заполняем отсутствующие косты (колонка 'Cost Value') значениями из self.additional_data.
        (Некоторые Media Source не передают это поле в AppsFlyer, поэтому мы подтягиваем его из их API)."""
        
        print('Filling NA costs')
        
        for media in NULL_COST_MEDIAS:
        
            print(f'  {media}')
            filt = self.data['Media Source'] == media
            idx = self.data.index[filt]
            
            if not self.data.loc[idx, 'Cost Value'].isnull().all():
                print('    not all costs are null')
                self.data.loc[idx, 'Cost Value'] = np.nan
                
            self.match_costs(media)
    
    def match_costs(self, media):
        """Заполняет пустые 'Cost Value' значениями из доп. данных."""
        
        pass