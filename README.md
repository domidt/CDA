# CDA
This applications provide a widely adaptable Continuous Double Auction (CDA) in oTree v6 via a complete implementation of an experimental asset market with mutliple continuously operating traders and multiple assets. 
Permission to use this software is granted for educational and academic purpose with the requirement of citation.

## Overview
This continuous double auction software is provided in four apps. 
The applications ``singleAsset`` and ``singleAssetInfo`` cover markets with a single asset while ``nAssets`` and ``nAssetsInfo`` cover market environments with multiple (n) assets.
Meanwhile, ``singleAsset`` and ``nAssets`` provide baseline applications with all market functionalities that target users who require intensive modifications.
``singleAssetInfo`` and ``nAssetsInfo`` provide versions, in which participants are acquainted with private information about the buyback value(s).
The latter applications mimic the experiment in [Palan et al. (2020)](#Palan2020), in which the buyback value is defined by coins in a jar and private information consists of accurate information about a partition of coins.

There are existing, well-developed packages for CDA markets, notable examples are [otree_markets](https://github.com/Leeps-Lab/otree_markets) which uses [LEEPS lab's redwood framework](https://github.com/Leeps-Lab/otree-redwood), [high frequency trading](https://github.com/Leeps-Lab/high_frequency_trading/), [otree-double-auction](https://github.com/IOP-Experiments/otree-double-auction), and [otree etf cda](https://github.com/jacopomagnani/otree_etf_cda).
However, to the best of my knowledge, there is no software which is supported by the new oTree version 6 and thus not supported by newer python version without a virtual environment. 
This is why, I started to create this app primarily for classroom games.

### JavaScript
Given the simultaneous placement of limit orders and acceptance via market orders, these applications use [live pages](https://otree.readthedocs.io/en/latest/live.html?highlight=script) extensively.
As a consequence, I do also use JavaScript and call the functions **_liveSend()_** and **_liveRecv()_**.
The corresponding files are placed in the ``_static`` folder, which must be loaded at the beginning of a html in the **_global_scripts_** block.
As another consequence, an error window pops up on clients screen via **\<noscript\>**, when JavaScripts are blocked.

The purposes of individual JavaScript files are depicted in [README_JavaScript.md](README_JavaScript.md).

## Installation
These applications are developed with oTree 6.0.0 using python 3.11.5. 
Running an online or classroom session, you may follow the instructions in [ExpEcoWorkflow_course_repository](https://ploteo.github.io/ExpEcoWorkflow_course_repository).
To make adaptions to these applications, you may need to download both python, which is available free of charge at [python.org/downloads/](https://www.python.org/downloads/), and oTree via the terminal as described by [oTree Setup](https://otree.readthedocs.io/en/latest/install-nostudio.html#install-nostudio) with: 
```
pip3 install -U otree
```

Note that developers of oTree do not recommended the use of text editors to most users and provide [oTree Studio](https://www.otreehub.com) instead.
However, to the best of my knowledge there is no easy workaround for continuous transmission of orders such that the order book works as it should. 
Since my background is not quite computer science, I guess that most code is straightforward to understand.
This said, I am humble enough to add that I benefited sharing the name with a very talented, sophisticated, and patient brother who explained this new world to me.
Finally, the otree Team implemented a very powerful and easily applicable tool for continuous communication between client and server via the **_live_method()_**.

To run CDA online, you need an online deployment via some [server setup](https://otree.readthedocs.io/en/latest/server/intro.html).
The oTree team recommends the use of the [heroku server](https://www.heroku.com/), which now charges a little fee.
The current free way to go is via a [github account](https://github.com/) and the cloud service [render.com](https://www.render.com).
For more detailed instructions you are invited to visit [oTree: Online Deployment](https://ploteo.github.io/ExpEcoWorkflow_course_repository/7/oTree_deployment_printout.html).
The latter free instances shall be fine for little classroom demonstrations, however risky for experimental sessions.


## Sequence

### Instruction page
Instructions are inspired by [Palan et al. (2020)](#Palan2020) and [Merl et al. (2023)](#Merl2023).
The corresponding files that are loaded in ``Instructions.html`` and include most of the text is placed at ``_templates/instructions*.html``.
I focus on markets with a single asset and private information provision such that information consists of accurate information about the amount of coins of specific coin values in a jar.

One information is gathered at the end of the instruction page, which is the number of actual participants.
By clicking the 'I read and understand the instructions' button, participants are sent to the waiting page but they are also set to be participating.
This allows to start a session with a much higher number of participant links in otree, although just a fraction is actually participating. 
Given that some student come late to classes, this can be an advantage.

### Wait-to-start page
As all participants arrive in the *waiting page*, i.e., when the experimenter *'advances'* non-participating users to the waiting page, some material variables are initialised.
First, I retrieve from the *config* variable, that is specified before the start of a session, whether participants roles are fixed or can change in each round.
All participates can either be inactive observers or traders with distinguishable private information.

#### Initialise group
Within the function **initiate_group()**, participants are counted (**count_participants()**), the asset value is defined (**define_asset_value()**), the role structure (**define_role_structure()**) and role information (**define_role_information_structure()**) is defined in information apps as well as roles assigned (**assign_types()**) in round 1 or when roles are randomly assigned each round.
Changes of the role or information structure, i.e. number of participants of a particular role, the information content, overlaps, etc. are set in these functions.

#### Initialise participants
Within the function **set_player_info()**, I distribute information according to the information structure in function **assign_role_attr()**.
Within the function **initiate_player()**, I distribute initial endowments.

### End-of-trial-rounds page
Just at the very beginning of the first payoff-relevant period, a short reminder is shown that asks for any further open question.

### Pre-market page
Before the market starts, participants receive information about their future role, their endowment, and private information in tabular form.
It may be advisable to set a timeout for this page.

### Market page
In the market page the information of the pre-market page is shown again. 
In addition, the entire marketplace is displayed, i.e., where participants can place a limit order, the order book that allows to accept market orders, and a graphic time series of the market transaction prices.
There is also a box with information about the last own transactions and messages about order rejections.

### Results page
After the market timeout, participants see the result page, which provides information about the actual buyback value of the asset and the period income.
I specify the profit function in the function **calc_period_profits()** which reads:

$$ 
\pi=\max(\{\text{base payment} + \text{multiplier} * \text{wealth change}, \text{minimum payment in round}\}). 
$$

$$ \text{wealth change}=\frac{\text{final endowment}}{\text{initial endowment}} $$


### Final results page
In the end of the very last round, participants see a summary of their payoff and a table including each period income.
The final payoff is a random draw of the previous period payoffs defined in the function **calc_final_profit()**.


### Admin report
I implemented a [customised admin report](https://otree.readthedocs.io/en/latest/admin.html#customizing-the-admin-interface-admin-reports) that includes participants period profits and a graphic.
The graphic visualises time series of trading activity in means of best bid, best ask, and transaction prices.
The entries are defined in the function **vars_for_admin_report()** in ``__init__.py`` and the report's layout is defined in ``_templates/admin_report.html``.

## Data download
I implemented [special data tables](https://otree.readthedocs.io/en/latest/misc/advanced.html#extramodel) for limit orders, transactions, and all kind of orders, as I implemented the tables for recordings of the bid-ask spread and a protocol of automatic messages.
For these tables, I define [customised data download](https://otree.readthedocs.io/en/latest/admin.html#custom-data-exports) in the respective ``__init__.py`` files.
Thus, changes in the customised data structure of orders require adjustments of the download process too.

Especially for the applications with multiple assets, I register entries as stings in JSON format, for example {assetID: entry}.
These variables may need some attention to decode.
Currently, I use the package [jsonlite](https://cran.r-project.org/web/packages/jsonlite/index.html) in [R](https://www.r-project.org/).

## Settings and parametrisation
Furthermore, in file ``__init__.py`` you can specify the names of the assets, in the n-assets app via the list ``ASSET_NAMES``. 

### Information and partitions denomination


Disclaimer: The code is provided for educational and academic purposes and you agree that you use such code entirely at your own risk.

- *<a id="Chen2016" href="https://doi.org/10.1016/j.jbef.2015.12.001"> Chen, Daniel L., Martin Schonger, Chris Wickens</a>*. 2016. **oTree—An open-source platform for laboratory, online, and field experiments**. *Journal of Behavioral and Experimental Finance* 9 88-97.
[![DOI:10.1016/j.jbef.2015.12.001](https://zenodo.org/badge/DOI/10.1016/j.jbef.2015.12.001.svg)](https://doi.org/10.1016/j.jbef.2015.12.001)

- *<a id="Merl2023" href="https://doi.org/10.1016/j.finmar.2023.100839"> Merl, Robert, Stefan Palan, Dominik Schmidt, Thomas Stöckl</a>*.  2023. **Insider trading legislation and trader migration**. *Journal of Financial Markets* 66.
[![DOI:10.1016/j.finmar.2023.100839](https://zenodo.org/badge/DOI/10.1016/j.finmar.2023.100839.svg)](https://doi.org/10.1016/j.finmar.2023.100839)

- *<a id="Palan2020" href="https://doi.org/10.1016/j.finmar.2023.100839">Palan, Stefan, Jürgen Huber, Larissa Senninger</a>*. 2020. **Aggregation mechanisms for crowd predictions**. *Experimental Economics* 23 (3) 788-814. 
[![DOI:10.1007/s10683-019-09631-0](https://zenodo.org/badge/DOI/10.1007/s10683-019-09631-0.svg)](https://doi.org/10.1007/s10683-019-09631-0)


