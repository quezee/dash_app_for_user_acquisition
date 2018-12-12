DATE_PRESET = 90
SECONDS_IN_DAY = 24 * 60 * 60
ID = 'Customer User ID'
COHORTS = [None, 'month', 1, 3, 7, 14, 28, 60]

APP_RENAMES = {
    'Last Day on Earth: Survival': 'Last Day on Earth',
    'Grim Soul: Survival': 'Grim Soul',
    'Grim Soul: Dark Fantasy Survival': 'Grim Soul',
    
    'Forge of Glory': 'Forge of Glory',
    'Westland Survival - Be a survivor in the Wild West': 'Westland Survival',
    'Westland Survival': 'Westland Survival',
    'Jurassic Survival': 'Jurassic Survival',
}
TAX_GROSS = {
    'Last Day on Earth': 0.93,
    'Grim Soul': 0.93,
    'Forge of Glory': 0.93,
    'Westland Survival': 1,
    'Jurassic Survival': 0.93
}
TAX_COST = 1.18
TAX_OTHERS = 0.3
OBSERV_SPAN = 60
DT_FMT = '%Y-%m-%d'
SURNAMES = ['Zhorina', 'Bosov', 'Baranov', 'Groshev', 'Batyuk', 'Polyansky', 'Ananyev']
USDRUB = {
    '2018-07': 60,
    '2018-08': 60,
    '2018-09': 67.5,
    '2018-10': 65.85,
    '2018-11': 66.36,
    '2018-12': 66.36
}
ODD_MEDIAS = ['AppsFlyer_Test', 'appsflyer_sdk_test_int', 'YouTube', 'AF_test', 'None', 'Kefir',
              'Deep_IOS_Test', 'Deeplink_test', 'deeplink_test']
MEDIA_RELATED_COLS = ['Media Source', 'Campaign', 'Channel', 'Campaign ID', 'Adset', 'Ad',
                      'Ad ID', 'Site ID', 'Sub Site ID', 'Sub Param 1']
PLATS = ['ios', 'android']
BIDALGO_TAX_MULT = 1.04
NULL_COST_MEDIAS = ['Facebook Ads', 'snapchat_int', 'Twitter']
MEDIAS_WITH_SITENAMES = ['adcolony_int', 'ironsource_int', 'chartboosts2s_int', 'vungle_int', 'liftoff_int']
WHALE_QUANT = 0.99
WHALE_THRESHOLD = 50