from clickhouse_driver import Client
import datetime
from config import Config
config = Config()

class CHHandler:
    def __init__(self, host, port):
        self.conn = Client(host, port)

    def simple_query(self, query, column_types=False):
        response = self.conn.execute(query, with_column_types=column_types, settings={'max_execution_time': 3600})
        if column_types:
            data = [dict(zip([col[0] for col in response[1]], row)) for row in response[0]]
            cols = [{'name': col[0], 'id': col[0]} for col in response[1]]
            return data, cols
        data = [{'label': row[0], 'value': row[0]} for row in response]
        return data

    # def pandas_query(self, query):
    #     response = self.conn.execute(query, with_column_types=True, settings={'max_execution_time': 3600})
    #     data = response [0]
    #     cols = [row[0] for row in response [1]]
    #     return pd.DataFrame(data, columns=cols)

def preproc_dt_range(dt_start, dt_end):
    return repr(dt_start + ' 00:00:00'), repr(dt_end + ' 23:59:59')

def preproc_dt(dt):
    return repr(dt.strftime('%Y-%m-%d 00:00:00'))


class QueryConstructor:
    def __init__(self, dt_start, dt_end, app, plat,
                 media, cohort, camptype, rtg, groupby):
        self.dt_start, self.dt_end = preproc_dt_range(dt_start, dt_end)
        self.app = app
        self.plat = plat
        self.media = media
        self.cohort = cohort
        self.camptype = camptype
        self.rtg = rtg
        self.groupby = groupby
        if cohort != 'None':
            today = datetime.datetime.utcnow().date()
            self.dt_border = preproc_dt(today - datetime.timedelta(days=int(cohort)))

    def installs_query(self):
        query = '''
        SELECT {}, uniqExact(AppsFlyerID) as Installs, SUM(CostValue) as Cost, SUM(CostValueTax) as CostTaxed
        FROM appsflyer.installs
        WHERE EventName = 'install' AND AttributedTouchTime BETWEEN {} AND {}
        '''.format(self.groupby, self.dt_start, self.dt_end)
        if self.app:
            query += ' AND AppName = {}'.format(repr(self.app))
        if self.plat:
            query += ' AND Platform = {}'.format(repr(self.plat))
        if self.media:
            query += ' AND MediaSource = {}'.format(repr(self.media))
        if self.cohort != 'None':
            query += ' AND InstallTime < {}'.format(self.dt_border)
        if self.camptype != 'All':
            query += ' AND IsRetCampaign = {}'.format(self.camptype)
        query += ' GROUP BY {}'.format(self.groupby)
        return query

    def media_query(self, media_source):
        table = config.MediaToTable[media_source]
        media_col = '{} as MediaSource, '.format(repr(media_source)) if 'MediaSource' in self.groupby else ''
        query = '''
        SELECT {}, {}SUM(CostValue) as MediaCost, SUM(CostValueTax) as MediaCostTaxed
        FROM {}
        WHERE Date BETWEEN {} AND {}
        '''.format(self.groupby, media_col, table, self.dt_start, self.dt_end)
        if self.app:
            query += ' AND AppName = {}'.format(repr(self.app))
        if self.plat:
            query += ' AND Platform = {}'.format(repr(self.plat))
        if self.cohort != 'None':
            query += ' AND Date < {}'.format(self.dt_border)
        if self.camptype != 'All':
            query += ' AND IsRetCampaign = {}'.format(self.camptype)
        query += ' GROUP BY {}'.format(self.groupby)
        return query

    def inapps_query(self):
        query = '''
        SELECT {}, uniqExact(AppsFlyerID) as Payers, SUM(EventRevenueUSD) as Gross, SUM(EventRevenueUSDTax) as GrossClean
        FROM appsflyer.inapps
        WHERE AttributedTouchTime BETWEEN {} AND {}
        '''.format(self.groupby, self.dt_start, self.dt_end)
        subquery = '''
        SELECT af_receipt_id
        FROM appsflyer.inapps
        WHERE AttributedTouchTime BETWEEN {} AND {}
        AND IsPrimaryAttribution == 0 AND IsRetargeting == 0
        '''.format(self.dt_start, self.dt_end)
        if self.app:
            query += ' AND AppName = {}'.format(repr(self.app))
            subquery += ' AND AppName = {}'.format(repr(self.app))
        if self.plat:
            query += ' AND Platform = {}'.format(repr(self.plat))
            subquery += ' AND Platform = {}'.format(repr(self.plat))
        if self.media:
            query += ' AND MediaSource = {}'.format(repr(self.media))
            subquery += ' AND MediaSource = {}'.format(repr(self.media))
        if self.cohort != 'None':
            query += ' AND InstallTime < {} AND DaysDiff <= {}'.format(self.dt_border, self.cohort)
            subquery += ' AND InstallTime < {} AND DaysDiff <= {}'.format(self.dt_border, self.cohort)
        if self.camptype != 'All':
            query += ' AND IsRetCampaign = {}'.format(self.camptype)
            subquery += ' AND IsRetCampaign = {}'.format(self.camptype)
        if self.rtg == 'Exclude':
            query += ' AND IsPrimaryAttribution = 1'
        elif self.rtg == 'Include':
            query += ' AND NOT (af_receipt_id IN ({}) AND IsPrimaryAttribution = 1)'.format(subquery)
        query += ' GROUP BY {}'.format(self.groupby)
        return query

    def join(self, query1, query2, select='*', join_type='ALL LEFT JOIN'):
        query = '''
        SELECT {}
        FROM ({})
        {}
        ({})
        USING {}
        '''.format(select, query1, join_type, query2, self.groupby)
        return query



if __name__ == '__main__':

    start_date = '2019-06-01 00:00:00'
    end_date = '2019-07-01 23:59:59'
    app = "Forge of Glory"
    plat = 'ios'

    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}
    AND AppName = {} AND Platform = {}
    '''.format(repr(start_date), repr(end_date), repr(app), repr(plat))

    from config import Config
    config = Config()
    ch = CHHandler(config.DB_HOST, config.DB_PORT)

    s = ch.simple_query(query, True)
    # p = ch.pandas_query(query)