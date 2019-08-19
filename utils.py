from clickhouse_driver import Client
import logging
import datetime
import textwrap
from config import Config
config = Config()


class CHHandler:
    def __init__(self, host, port):
        self.conn = Client(host, port)

    def simple_query(self, query, with_columns=False):
        logging.debug('____________________QUERY____________________')
        response = self.conn.execute(query, with_column_types=with_columns, settings={'max_execution_time': 3600})
        if with_columns:
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
    def __init__(self, dt_start, dt_end, app_name, plat, media, sql_filter, cohort,
                 camptype, rtg, whales, dup_payments, groupby, ad_metrics, ts_break=None):
        self.dt_start, self.dt_end = preproc_dt_range(dt_start, dt_end)
        self.app_name = app_name
        self.plat = plat
        self.media = media
        self.sql_filter = sql_filter
        self.cohort = cohort
        self.camptype = camptype
        self.rtg = rtg
        self.whales = whales
        self.dup_payments = dup_payments

        self.groupby = groupby
        if ts_break:
            self.groupby += 'toStartOf' + ts_break

        self.ad_metrics = ad_metrics
        self.ad_cols = ''
        if not self.media:
            self.ad_cols = set.intersection(*[set(col_list) for col_list in config.AD_METRICS.values()])
        elif self.media in config.AD_METRICS:
            self.ad_cols = config.AD_METRICS[self.media]

        if cohort != 'None':
            today = datetime.datetime.utcnow().date()
            self.dt_border = preproc_dt(today - datetime.timedelta(days=int(cohort)))

        self.filt_global = ''
        if app_name:
            self.filt_global += ' AND AppName = {}'.format(repr(app_name))
        if plat:
            self.filt_global += ' AND Platform = {}'.format(repr(plat))
        if camptype != 'All':
            self.filt_global += ' AND IsRetCampaign = {}'.format(camptype)
        if sql_filter:
            self.filt_global += ' AND ' + sql_filter

    @staticmethod
    def indent(query):
        return textwrap.indent(query, '    ')

    def installs_query(self):
        query = \
        '\nSELECT {}, uniqExact(AppsFlyerID) as Installs, SUM(CostValue) as Cost, SUM(CostValueTax) as CostTaxed{}' \
        '\nFROM appsflyer.installs' \
        "\nWHERE EventName = 'install' AND AttributedTouchTime BETWEEN {} AND {}\n" \
        .format(self.groupby,
                ', ' + ', '.join(['0 as {}'.format(col) for col in self.ad_cols]) if self.ad_metrics else '',
                self.dt_start, self.dt_end) \
        + self.filt_global

        if self.media:
            query += ' AND MediaSource = {}'.format(repr(self.media))
        if self.cohort != 'None':
            query += ' AND InstallTime < {}'.format(self.dt_border)

        query += '\nGROUP BY {}'.format(self.groupby)
        return query

    def currency_query(self, cur):
        query = \
        '\nWITH (\nSELECT avg(Value)' \
        '\nFROM appsflyer.cbr' \
        "\nWHERE Currency = '{}' AND Date BETWEEN {} AND {}" \
        '\n) AS {}' \
        .format(cur, self.dt_start, self.dt_end, cur)
        return query

    def media_query(self, media_source):
        table = config.MediaToTable[media_source]
        query = \
        '\nSELECT {}, SUM(CostValue) as MediaCost, SUM(CostValueTax) as MediaCostTaxed{}' \
        '\nFROM {}' \
        '\nWHERE Date BETWEEN {} AND {}\n' \
        .format(self.groupby.replace('MediaSource', '{} as MediaSource'.format(repr(media_source))),
                ', ' + ', '.join(['SUM({}) as Media{}'.format(col, col) for col in config.AD_METRICS[media_source]])
                if self.ad_metrics else '',
                table, self.dt_start, self.dt_end) \
        + self.filt_global

        if self.cohort != 'None':
            query += ' AND Date < {}'.format(self.dt_border)
        if media_source == 'googleadwords_int':
            currency_query = self.currency_query('USD')
            query = currency_query + query
            query = query.replace('SUM(CostValue) as MediaCost, SUM(CostValueTax) as MediaCostTaxed',
                                  '(SUM(CostValue) / USD) as MediaCost, (SUM(CostValueTax) / USD) as MediaCostTaxed')

        query += '\nGROUP BY {}'.format(self.groupby)
        return query

    def combined_installs_query(self):
        installs_query = self.installs_query()

        if (not self.media) | (self.media in config.SPECIAL_MEDIAS):
            select = \
            '{}, Installs, (Cost + MediaCost) as Cost, (CostTaxed + MediaCostTaxed) as CostTaxed{}' \
            .format(self.groupby,
                    ', ' + ', '.join(['({} + Media{}) as {}'.format(col, col, col) for col in self.ad_cols])
                    if self.ad_metrics else '')

            if not self.media:
                for media_source in config.SPECIAL_MEDIAS:
                    media_query = self.media_query(media_source)
                    installs_query = self.join(installs_query, media_query, select)

            elif self.media in config.SPECIAL_MEDIAS:
                media_query = self.media_query(self.media)
                installs_query = self.join(installs_query, media_query, select)

        return installs_query

    def payments_query(self):
        query = \
        '\nSELECT {}, AppsFlyerID, EventRevenueUSD, EventRevenueUSDTax, af_receipt_id' \
        '\nFROM appsflyer.payments' \
        '\nWHERE AttributedTouchTime BETWEEN {} AND {}\n' \
        .format(self.groupby, self.dt_start, self.dt_end) \
        + self.filt_global

        if self.media:
            query += ' AND MediaSource = {}'.format(repr(self.media))
        if self.cohort != 'None':
            query += ' AND InstallTime < {} AND DaysDiff <= {}'.format(self.dt_border, self.cohort)
        if self.rtg == 'Exclude':
            query += ' AND IsPrimaryAttribution = 1'
        elif self.rtg == 'Include':
            overlap_payments = self.overlap_payments_query()
            query += '\n AND NOT (af_receipt_id IN ({}\n) AND IsPrimaryAttribution = 1)\n' \
                        .format(self.indent(overlap_payments))
        if self.whales == 'Exclude':
            whales = self.whale_query(query)
            query += ' AND AppsFlyerID NOT IN ({}\n)'.format(self.indent(whales))
        if self.dup_payments == 'Remove':
            query += '\nLIMIT 1 BY af_receipt_id'

        agg_query = \
        '\nSELECT {}, uniqExact(AppsFlyerID) as Payers, SUM(EventRevenueUSD) as Gross,' \
        '\nSUM(EventRevenueUSDTax) as GrossClean' \
        '\nFROM ({})' \
        '\nGROUP BY {}' \
        .format(self.groupby, self.indent(query), self.groupby)

        return agg_query

    def overlap_payments_query(self):
        query = \
        '\nSELECT af_receipt_id' \
        '\nFROM appsflyer.payments' \
        '\nWHERE AttributedTouchTime BETWEEN {} AND {}' \
        '\n AND IsPrimaryAttribution == 0' \
        .format(self.dt_start, self.dt_end)

        if self.app_name:
            query += ' AND AppName = {}'.format(repr(self.app_name))
        if self.plat:
            query += ' AND Platform = {}'.format(repr(self.plat))
        if self.media:
            query += ' AND MediaSource = {}'.format(repr(self.media))
        if self.cohort != 'None':
            query += ' AND InstallTime < {} AND DaysDiff <= {}'.format(self.dt_border, self.cohort)

        return query

    def whale_query(self, payments_query):
        threshold = config.WHALE_THRESHOLDS[self.cohort]
        replace_what = '{}, AppsFlyerID, EventRevenueUSD, EventRevenueUSDTax, af_receipt_id'.format(self.groupby)
        replace_with = 'AppsFlyerID, SUM(EventRevenueUSD) as Gross'
        payments_query = payments_query.replace(replace_what, replace_with) + \
        '\nGROUP BY AppsFlyerID' \
        '\nHAVING Gross > {}' \
        .format(threshold)

        query = \
        '\nSELECT AppsFlyerID' \
        '\nFROM ({})' \
        .format(self.indent(payments_query))

        return query

    def join(self, query1, query2, select='*', join_type='ALL FULL JOIN'):
        query = \
        '\nSELECT {}' \
        '\nFROM ({})' \
        '\n{} ({})' \
        '\nUSING {}' \
        .format(select, self.indent(query1), join_type, self.indent(query2), self.groupby)
        return query




# if __name__ == '__main__':
#
#     start_date = '2019-06-01 00:00:00'
#     end_date = '2019-07-01 23:59:59'
#     app = "Forge of Glory"
#     plat = 'ios'
#
#     query = '''
#     SELECT DISTINCT MediaSource FROM appsflyer.installs
#     WHERE AttributedTouchTime BETWEEN {} AND {}
#     AND AppName = {} AND Platform = {}
#     '''.format(repr(start_date), repr(end_date), repr(app), repr(plat))
#
#     from config import Config
#     config = Config()
#     ch = CHHandler(config.DB_HOST, config.DB_PORT)
#
#     s = ch.simple_query(query, True)
#     # p = ch.pandas_query(query)