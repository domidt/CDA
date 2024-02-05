# CDA
This application provides a widely adaptable Continuous Double Auction (CDA) in oTree v5 via a complete implementation of an experimental asset market with mutliple continuously operating traders and multiple assets. 
Permission to use this software is granted for educational and academic purpose with the requirement of citation.

## Overview
This continuous double auction software is provided in four apps. 
The applications ``singleAsset`` and ``singleAssetInfo`` cover markets with a single asset while ``nAssets`` and ``nAssetsInfo`` cover markets with multiple (n) assets.
Meanwhile, ``singleAsset`` and ``nAssets`` provide baseline applications with all market functionalities that target users who require intensive modifications.
``singleAssetInfo`` and ``nAssetsInfo`` provide versions, in which participants are acquainted with information about the buyback value(s).

There are existing, well-developed packages for CDA markets, notable examples are [otree_markets](https://github.com/Leeps-Lab/otree_markets) which uses [LEEPS lab's redwood framework](https://github.com/Leeps-Lab/otree-redwood), [high frequency trading](https://github.com/Leeps-Lab/high_frequency_trading/), [otree-double-auction](https://github.com/IOP-Experiments/otree-double-auction), and [otree etf cda](https://github.com/jacopomagnani/otree_etf_cda).
However, to the best of my knowledge, there is no software which is supported by the new oTree version 6 and thus not supported by newer python version without a virtual environment. 
This is why, I started to create this app primarily for classroom games.

### JavaScript
Given the contemporaneous placement of limit orders and acceptance via market orders, these applications use [live pages](https://otree.readthedocs.io/en/latest/live.html?highlight=script) extensively.
As a consequence, I do also us JavaScript and call the functions **_liveSend()_** and **_liveRecv()_**.
The corresponding files are placed in the ``_static`` folder, they must be loaded at the beginning of a html in the **_global_scripts_** block, and the structure of scripts is the following:
The ``script.js`` is loaded by every page but the instructions and has mainly the purposes to label values by a certain currency and defines some local variables.
The ``scriptMarket.js`` os only loaded by ``Market.html`` 

## Installation
These applications are developed with oTree 6.0.0 using python 3.11.5. 
Running an online or classroom session, you may follow the instructions in [ExpEcoWorkflow_course_repository](https://ploteo.github.io/ExpEcoWorkflow_course_repository).
To make adaptions to these applications, you may need to download both python, which is available free of charge at [https://www.python.org/downloads/](https://www.python.org/downloads/), and oTree via the terminal as described by [oTree Setup](https://otree.readthedocs.io/en/latest/install-nostudio.html#install-nostudio) with: 
```
pip3 install -U otree
```

## Sequence

### Instructions


Several adaption options are implemented. For example in the file ``settings.py`` in ``SESSION_CONFIGS`` you can easily change the duration of a market, whether trader types are randomised between periods, the number of active/inactive as well as the number of informed/uninformed traders. These settings can also be changed ad-hoc in class when creating a session.
Furthermore, in file ``__init__.py`` you can specify the names of the assets, in the n-assets app via the list ``ASSET_NAMES``. The Constants in the same file allow to adapt the number of periods the payout function, given in function ``calcPeriodProfits`` by

$$ 
\pi=\max(\{\text{base payment} + \text{multiplier} * \text{wealthChange}, \text{min payment in round}\}). 
$$

The constants in ``__init__.py`` do also include the limits of the random variables which determine the asset and cash endowment at the beginning of the period and constants include the number of decimals and whether short selling and buys on margin are allowed.


Disclaimer: The code is provided for educational and academic purposes and you agree that you use such code entirely at your own risk.
