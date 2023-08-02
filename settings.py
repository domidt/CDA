from os import environ

SESSION_CONFIGS = [
    dict(
        name='crowd',
        display_name='Aggregation mechanisms for crowd predictions',
        app_sequence=['singleAssetCrowdPredictions'],
        num_demo_participants=30,
        num_traders=30,
        num_I3_traders=8,
        num_I2_traders=8,
        num_I1_traders=8,
        num_1E_coins=8,
        num_20c_coins=12,
        num_5c_coins=15,
        num_1c_coins=24,
        market_time=210,
        randomise_types=True,
    ),
    dict(
        name='nAssets',
        display_name='n assets: Continuous double auction',
        app_sequence=['nAssets'],
        num_demo_participants=5,
        num_traders=4,
        num_allinformed_traders=1,
        num_1informed_traders=1,
        market_time=210,
        randomise_types=True,
        ),
    dict(
        name='singleAsset',
        display_name='Single asset: Continuous double auction',
        app_sequence=['singleAsset'],
        num_demo_participants=4,
        num_traders=3,
        num_informed_traders=2,
        market_time=210,
        randomise_types=True,
        ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
SECRET_KEY = '776841529'

DEMO_PAGE_INTRO_HTML = """ """

INSTALLED_APPS = ['otree']
#DEBUG = False
#AUTH_LEVEL = DEMO
