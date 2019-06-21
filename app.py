import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html

from config import Config
config = Config()

app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(app, config.USERS)

from tabs import TABS

app.layout = html.Div([
    html.H1('Doshique'),
    dcc.Tabs(id="tabs", value='Main', children=TABS),
])

from callbacks import *

if __name__ == '__main__':
    app.run_server(debug=True)