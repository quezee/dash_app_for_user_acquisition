BI web-app for User Acquisition managers. Based on [Dash](dash.plot.ly) framework.<br>
Was built on top of Clickhouse database containing installs and payments data from [AppsFlyer](appsflyer.com) and some other data sources.

## Contents
   * [How does it work](#how-does-it-work)
   * [Configuration](#configuration)

## How does it work
Page layout is served dynamically on every page request through `app.layout` ([app.py](app.py)).<br>
Callbacks defined in [callbacks.py](callbacks.py) provide interactive functionality like constructing SQL query and receiving data up on pressing `Submit` button.<br>
Front-end consists of control panel to specify which data / metrics you want to analyse and 2 output sections: `Main metrics`, showing query results in an interactive sheet and `Dynamics`, doing the same, but through line plots in time.

## Configuration
Configuration constants should be defined in `environments.json` file, located in root.

**USERS**<br>
Login/Password pairs for authorisation.

**APP_NAMES, PLATFORMS, COHORTS**<br>
Options for corresponding dropdowns/tumblers which should be available for querying.

**WHALE_THRESHOLDS**<br>
Upper thresholds for payments amount to enable whale filtering functionality.

**SPECIAL_MEDIAS, MediaToTable, AD_METRICS**<br>
`SPECIAL_MEDIAS` are media sources, data for which should be querried from dedicated tables (not AppsFlyer ones), since they don't provide AppsFlyer with costs.<br>
`MediaToTable` is a mapping from such medias to their corresponding table names in DB.<br>
`AD_METRICS` is a mapping for other metrics like Clicks/Impressions available for each of special media.

**GROUPERS**<br>
This dictionary is used to map available data breakdowns (`Group by` component in front-end) through `set_groupby_options` callback depending on chosen `Media Source` in dropdown.<br>