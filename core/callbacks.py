from app import app
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
# import dash_table_experiments as dt
# import plotly.graph_objs as go
# from plotly import tools

import datetime


@app.callback(Output('filter_media', 'options'),
              [Input('filter_app_name', 'value'), Input('filter_plat', 'value')])
def set_media_options(app_name, plat):
    if not plat:
        return []

    media_list = media_options[(app_name, plat)]
    return [{'label': media, 'value': media} for media in media_list]