from os import environ

SESSION_CONFIGS = [
    dict(
        name='sPartitions',
        display_name='single asset: Aggregation mechanisms for crowd predictions on partitions',
        app_sequence=['singleAssetPartitionCDA'],
        num_demo_participants=4,
        est_num_traders=30,
        num_shares_in_market=100,
        market_time=300,
        randomise_types=True,
        short_selling=True,
        margin_buying=True,
    ),
    dict(
        name='nPartitions',
        display_name='n assets: Aggregation mechanisms for crowd predictions with multiple assets on partitions',
        app_sequence=['nAssetsPartitionCDA'],
        num_demo_participants=30,
        num_traders=30,
        market_time=210,
        randomise_types=True,
        short_selling=True,
        margin_buying=True,
    ),
    dict(
        name='singleAsset',
        display_name='Single asset: Continuous double auction',
        app_sequence=['singleAsset'],
        num_demo_participants=4,
        num_traders=3,
        market_time=210,
        randomise_types=True,
        short_selling=True,
        margin_buying=True,
        ),
    dict(
        name='nAssets',
        display_name='n assets: Continuous double auction',
        app_sequence=['nAssets'],
        num_demo_participants=5,
        num_traders=4,
        market_time=210,
        randomise_types=True,
        short_selling=True,
        margin_buying=True,
        ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = ['roleID', 'isActive', 'informed']
SESSION_FIELDS = ['numParticipants']

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
