import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
# import plotly.graph_objs as go
# from plotly import tools
import datetime

from config import Config
config = Config()
from ch_handler import CHHandler
ch = CHHandler(config.DB_HOST, config.DB_PORT)

from app import app


def preproc_dt_range(dt_start, dt_end):
    return repr(dt_start + ' 00:00:00'), repr(dt_end + ' 23:59:59')

def preproc_dt(dt):
    return repr(dt.strftime('%Y-%m-%d 00:00:00'))


@app.callback(Output('media', 'options'),
              [Input('date_range', 'start_date'), Input('date_range', 'end_date'),
               Input('app', 'value'), Input('plat', 'value')])
def set_media_options(dt_start, dt_end,
                      app, plat):
    dt_start, dt_end = preproc_dt_range(dt_start, dt_end)
    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}'''.format(dt_start, dt_end)
    if app:
        query += ' AND AppName = {}'.format(repr(app))
    if plat:
        query += ' AND Platform = {}'.format(repr(plat))
    data = ch.simple_query(query)
    return data


@app.callback([Output("main_table", "data"), Output("main_table", "columns")],
              [Input('main_submit', 'n_clicks')],
              [State('date_range', 'start_date'), State('date_range', 'end_date'),
               State('app', 'value'), State('plat', 'value'), State('media', 'value'),
               State('main_cohort', 'value'), State('main_camptype', 'value'),
               State('main_rtg', 'value'), State('main_groupby', 'value')])
def update_main_table(n_clicks, dt_start, dt_end, app,
                      plat, media, cohort, camptype, rtg, groupby):
    if not groupby:
        return [], []
    if isinstance(groupby, list):
        groupby = ', '.join(groupby)
    dt_start, dt_end = preproc_dt_range(dt_start, dt_end)
    if cohort != 'None':
        today = datetime.datetime.utcnow().date()
        dt_border = preproc_dt(today - datetime.timedelta(days=int(cohort)))

    q_installs = '''
    SELECT {}, uniqExact(AppsFlyerID) as Installs, SUM(CostValue) as Cost, SUM(CostValueTax) as CostTaxed
    FROM appsflyer.installs
    WHERE EventName = 'install' AND AttributedTouchTime BETWEEN {} AND {}
    '''.format(groupby, dt_start, dt_end)
    if app:
        q_installs += ' AND AppName = {}'.format(repr(app))
    if plat:
        q_installs += ' AND Platform = {}'.format(repr(plat))
    if media:
        q_installs += ' AND MediaSource = {}'.format(repr(media))
    if cohort != 'None':
        q_installs += ' AND InstallTime < {}'.format(dt_border)
    if camptype != 'All':
        q_installs += ' AND IsRetCampaign = {}'.format(camptype)
    q_installs += ' GROUP BY {}'.format(groupby)

    q_inapps = '''
    SELECT {}, uniqExact(AppsFlyerID) as Payers, SUM(EventRevenueUSD) as Gross, SUM(EventRevenueUSDTax) as GrossClean
    FROM appsflyer.inapps
    WHERE AttributedTouchTime BETWEEN {} AND {}
    '''.format(groupby, dt_start, dt_end)
    if app:
        q_inapps += ' AND AppName = {}'.format(repr(app))
    if plat:
        q_inapps += ' AND Platform = {}'.format(repr(plat))
    if media:
        q_inapps += ' AND MediaSource = {}'.format(repr(media))
    if cohort != 'None':
        q_inapps += ' AND InstallTime < {} AND DaysDiff <= {}'.format(dt_border, cohort)
    if camptype != 'All':
        q_inapps += ' AND IsRetCampaign = {}'.format(camptype)
    if rtg == 'Exclude':
        q_inapps += ' AND IsPrimaryAttribution = 1'
    elif rtg == 'Include':
        q_inapps += ' AND IsRetargeting = 0'
    q_inapps += ' GROUP BY {}'.format(groupby)

    query = '''
    SELECT {},
        ROUND(Cost, 1) as Cost,
        ROUND(CostTaxed, 1) as CostTaxed,
        ROUND(Cost/Installs, 2) as CPI,
        Installs, Payers,
        ROUND(100*Payers/Installs, 1) as Paying,
        ROUND(Gross, 1) as Gross,
        ROUND(GrossClean, 1) as GrossClean,
        ROUND(100*GrossClean/CostTaxed, 1) as ROI
    FROM ({})
    ALL FULL JOIN
    ({})
    USING {}
    '''.format(groupby, q_installs, q_inapps, groupby)

    print(query)

    data, cols = ch.simple_query(query, True)
    return data, cols