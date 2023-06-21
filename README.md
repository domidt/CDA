# CDA
This application provides a widely adaptable Continuous Double Auction (CDA) in oTree v5 via a complete implementation of an experimental asset market with mutliple continuously operating traders and multiple assets. Permission to use this software is granted for educational and academic purpose with the requirement of citation.

## Overview
This continuous double auction software is provided in two apps, since one covers a simplicistic version with a single asset and more convenient data export, while the other captures markets with multiple (n) assets which are summerised in variables with JSON format. 
There are existing, well developed packages for CDA markets, notable examples are [otree_markets](https://github.com/Leeps-Lab/otree_markets) which uses [LEEPS lab's redwood framework](https://github.com/Leeps-Lab/otree-redwood), [high frequency trading](https://github.com/Leeps-Lab/high_frequency_trading/), and [otree-double-auction](https://github.com/IOP-Experiments/otree-double-auction).
However, to the best of my knowledge, there is no software which is supported by the new oTree version 5 and thus not supported by newer python version without a virtual environment. This is why, I started to create this app primarily for classroom games.

## Installation
This software is developed for oTree 5.10.2 using python 3.11.1. To make adaptions to it, you may need to download both softwares, which are available free of charge at [https://www.python.org/downloads/](https://www.python.org/downloads/) and oTree via: 
```
pip3 install -U otree
```
From here, you may add a new project, and add these apps to it.

Running an online or classroom session, you may follow the instructions in [ExpEcoWorkflow_course_repository](https://ploteo.github.io/ExpEcoWorkflow_course_repository/7/oTree_deployment_printout.html) and add a fork of this repository to your website.

## Adaptions
Several adaption options are implemented. For example in the file settings.py in SESSION_CONFIGS you can easily change the duration of a market, whether trader types are randomised between periods, the number of active/inactive as well as the number of informed/uninformed traders. These settings can also be changed ad-hoc in class when creating a session.
Furthermore, in file __init__.py you can specify the names of the assets, in the n-assets app via the list ASSET_NAMES. The Constants in the same file allow to adapt the number of periods the payout function, given in function 'calcPeriodProfits' by

$$
\pi=\max(\{\text{base payment} + \text{multiplier} * \text{wealthChange}, \text{min payment in round}\}).
$$

The constants in __init__.py do also include the limits of the random variables which determine the asset and cash endowment at the beginning of the period and constants include the number of decimals and whether short selling and buys on margin are allowed.


Disclaimer: The code is provided for educational and academic purposes and you agree that you use such code entirely at your own risk.
