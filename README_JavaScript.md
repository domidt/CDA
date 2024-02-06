# JavaScript

### Baseline script
The ``script.js`` is loaded by every page but the instructions.
Its main purpose is to label values by a certain currency and it defines some local variables.
Specifically, I define the **CURRENCY_LABEL** and within the function **_cu()_** I define how this **CURRENCY_LABEL** is used on values.
More specifically, the **CURRENCY_LABEL** is used to represent cash holding, margin buying limit, and the asset value in the result page when loaded.

### Market scripts
The ``scriptMarket.js`` is only loaded by ``Market.html`` and so are ``sCDAstatic/scriptSAssetMarket.js`` and ``nCDAstatic/scriptnAssetsMarket.js`` in the corresponding market environment.
``scriptMarket.js`` takes care of the order book, such that the process to highlight a selected bid or ask is defined, the **_cancelLimit()_** command to withdraw an own order is defined together with some validation processes; in addition, specifications of the Message and Trade boxes are given. 
Meanwhile, within ``scriptSAssetMarket.js`` and ``scriptnAssetsMarket.js``, I define the substantial commands **_liveRecv()_**, which defines how data sent from the server is handled, **_sendOffer()_**, which defines how limit orders are sent to the server, and **_sendAcc()_**, which defines how market orders are sent to the server.
Any modification of the **_live_method_()** function in ``__init__.py`` must only verify that data is sent and loaded correctly on the clients' side.

### n Assets scripts
The n assets market environment is substantially different for multiple functions as I additionally need to specify the *assetID* in many actions.
I implemented the creation of multiple options for assetIDs in the order book within ``scriptnAssetsMarket.js``.
Furthermore, since I grant separate tables to the asset endowment for n assets, the entries for these tables a loaded via function in ``_static/cCDAstatic/scriptnAssets.js``.

### Graphics
For the graphics that participants see on the trading page, ``chart.js`` sets how the data is used; 
meanwhile, the data and some layout is determined in the corresponding ``__init__.py`` via the variable **_highcharts_series_**, which is included by clients via **_liveRecv()_**.
