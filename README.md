# CDA
These applications provide a widely adaptable Continuous Double Auction (CDA) in oTree v6 via a complete implementation of an experimental asset market with multiple continuously operating traders and multiple assets. 
Permission to use this software is granted for educational and academic purpose with the requirement of citation.

## Table of content
1. [Overview](#overview)
2. [JavaScript](#javascript)
3. [Installation](#installation)
4. [Sequence](#sequence)
5. [Data download](#data-download)
6. [Settings and parametrisation](#settings-and-parametrisation)
7. [Disclaimer](#disclaimer)
8. [References](#reference)

## Overview
Continuous double auctions are provided in four apps. 
The applications ``singleAsset`` and ``singleAssetInfo`` cover markets with a single asset while ``nAssets`` and ``nAssetsInfo`` cover market environments with multiple (n) assets.
Meanwhile, ``singleAsset`` and ``nAssets`` provide baseline applications with all market functionalities that target users who require intensive modifications.
``singleAssetInfo`` and ``nAssetsInfo`` provide versions, in which participants are acquainted with private information about the buyback value(s).
The latter applications mimic the experiment in [Palan et al. (2020)](#Palan2020), in which the buyback value is defined by coins in a jar and private information consists of accurate information about a partition of coins.
To implement an application without major modifications of the code for classroom experiments, you may have a look at the <a href="https://github.com/domidt/CDA/blob/62daf6a2afdc56850f1641285b198ea5af638302/Step_by_step_CDA_otree.pdf" target="_blank">step-by-step description</a>.

There are existing, well-developed packages for CDA markets, notable examples are <a href="https://github.com/Leeps-Lab/otree_markets" target="_blank">otree_markets</a> which uses <a href="https://github.com/Leeps-Lab/otree-redwood" target="_blank">LEEPS lab's redwood framework</a>, <a href="https://github.com/Leeps-Lab/high_frequency_trading/" target="_blank">high frequency trading</a>, <a href="https://github.com/IOP-Experiments/otree-double-auction" target="_blank">otree-double-auction</a>, and <a href="https://github.com/jacopomagnani/otree_etf_cda" target="_blank">otree etf cda</a>.
However, to the best of my knowledge, there is no software which is supported by the new oTree version 6 and thus not supported by newer python version without a virtual environment. 
This is why, I started to create this app primarily for classroom games.

This application adds some more useful tools; for example, participants are now able to specify any volume they want to transact.


## JavaScript
Given the simultaneous placement of limit orders and acceptance via market orders, these applications use <a href="https://otree.readthedocs.io/en/latest/live.html?highlight=script" targer="_blank">live pages</a> extensively.
As a consequence, I do also use JavaScript and call the functions **_liveSend()_** and **_liveRecv()_**.
The corresponding files are placed in the ``_static`` folder, which must be loaded at the beginning of a html in the **_global_scripts_** block.
As another consequence, an error window pops up on clients screen via **\<noscript\>**, when JavaScripts are blocked.

The purposes of individual JavaScript files are depicted in [README_JavaScript.md](README_JavaScript.md).

## Installation
These applications are developed with oTree 6.0.0 using python 3.11.5. 
Running an online or classroom session, you may follow the instructions in <a href="https://ploteo.github.io/ExpEcoWorkflow_course_repository" target="_blank">ExpEcoWorkflow_course_repository</a>.
To make adaptions to these applications, you may need to download both python, which is available free of charge at <a href="https://www.python.org/downloads/" target="_blank">python.org/downloads/</a>, and oTree via the terminal as described by <a href="https://otree.readthedocs.io/en/latest/install-nostudio.html#install-nostudio" target="_blank">oTree Setup</a> with: 
```
pip3 install -U otree
```

Note that developers of oTree do not recommended the use of text editors to most users and provide <a href="https://www.otreehub.com" target="_blank">oTree Studio</a> instead.
However, to the best of my knowledge there is no easy workaround such that the order book is continuously updated and such that orders can be transmitted continuously without using the text editor. 
Since my background is not quite computer science, I guess that most code is straightforward to understand.
This said, I am humble enough to add that I benefited sharing the name with a very talented, sophisticated, and patient brother who explained this new world to me.
Finally, the otree team implemented a very powerful and easily applicable tool for continuous communication between client and server via the **_live_method()_**.

To run CDA online, you need an online deployment via some <a href="https://otree.readthedocs.io/en/latest/server/intro.html" target="_blank">server setup</a>.
The oTree team recommends the use of the <a href="https://www.heroku.com/" target="_blank">heroku server</a>, which now charges a little fee.
The current free way to go is via a <a href="https://github.com/" target="_blank">github account</a> and the cloud service <a href="https://www.render.com" target="_blank">render.com</a>.
For more detailed instructions you are invited to visit <a href="https://ploteo.github.io/ExpEcoWorkflow_course_repository/7/oTree_deployment_printout.html" target="_blank">oTree: Online Deployment</a>.
The latter free instances should be fine for little classroom demonstrations, however risky for experimental sessions.


## Sequence

### Instruction page
Instructions are inspired by [Palan et al. (2020)](#Palan2020) and [Merl et al. (2023)](#Merl2023).
The corresponding files that are loaded in ``Instructions.html`` and include most of the text is placed at ``_templates/instructions*.html``.
In the instructions, I focus on markets with a single asset and private information provision such that information consists of accurate information about the amount of coins of specific coin values in a jar.

One information is gathered at the end of the instruction page, which is the number of actual participants.
By clicking the *'I read and understand the instructions'* button, participants are sent to the waiting page but they are also set to be actively participating.
This allows classroom instructors to start a session with a much higher number of participant links in otree, although just a fraction is actually participating. 
Given that some student come late to classes, this can be an advantage.

### Wait-to-start page
As all participants arrive in the *waiting page*, i.e., when the experimenter *'advances'* non-participating users to the waiting page, some substantial variables are initialised.
First, I retrieve from the *config* variables, which are specified when a nes session is created, whether participants roles are fixed or can change in each round.
All participates can either be inactive observers or traders with distinguishable private information.
There are multiple further substantial variables defined in the wait-to-start page:

#### Initialise group
Within the function **initiate_group()**, participants are counted (**count_participants()**) and the asset value is defined (**define_asset_value()**).
Within apps with private information, the role structure (**define_role_structure()**) and role information (**define_role_information_structure()**) is defined.
Participants' roles are also assigned (**assign_types()**) in round 1 or when roles are randomly assigned each round.
Changes of the role or information structure, i.e. number of participants of a particular role, the information content, overlaps, etc. are set in these functions.

#### Initialise participants
Within the function **set_player_info()**, I distribute information according to the information structure in function **assign_role_attr()** and distribute participant characteristics.
Respectively in apps without information distribution, the function **set_player()** distributes participant characteristics only, i.e., whether they are active traders or inactive observers.
Within the function **initiate_player()**, I distribute initial endowments.

### End-of-trial-rounds page
Just at the very beginning of the first payoff-relevant period, a short reminder is shown that asks for any further open question.

### Pre-market page
Before the market starts, participants receive information about their future role, their endowment, and private information in tabular form.
It may be advisable to set a timeout for this page.

### Waiting-market page
This page makes sure that all participants start simultaneously, saves the market start time, and sets the market end time.

### Market page
In the market page the information of the pre-market page is shown again. 
In addition, the entire marketplace is displayed, i.e., where participants can place a limit order, the order book that allows to accept market orders, and a graphic time series of the market transaction prices.
There is also a box with information about the last own transactions and messages about order rejections.

### Results-wait page
In the waiting page before results, the period income and final payout is calculated. It is important to run these calculations before the actual result page as random number generators would be re-run with each reload of the page and change the result.

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
I implemented a <a href="https://otree.readthedocs.io/en/latest/admin.html#customizing-the-admin-interface-admin-reports" target="_blank">customised admin report</a> that includes participants' period profits and a graphic.
The graphic visualises time series of trading activity in means of best bid, best ask, and transaction prices.
The entries are defined in the function **vars_for_admin_report()** in ``__init__.py`` and the report's layout is defined in ``_templates/admin_report.html``.

## Data download
I implemented <a href="https://otree.readthedocs.io/en/latest/misc/advanced.html#extramodel" target="_blank">special data tables</a> for limit orders, transactions, and all kind of orders, as I implemented the tables for recordings of the bid-ask spread and a protocol of automatic messages.
For these tables, I define <a href="https://otree.readthedocs.io/en/latest/admin.html#custom-data-exports" target="_blank">customised data download</a> in the respective ``__init__.py`` files.
Thus, changes in the customised data structure of orders require adjustments of the download process too.

Especially for the applications with multiple assets, I register entries as stings in JSON format, for example {assetID: entry}.
These variables may need some attention to decode.
Currently, I use the package <a href="https://cran.r-project.org/web/packages/jsonlite/index.html" target="_blank">jsonlite</a> in <a href="https://www.r-project.org/" target="_blank">R</a>.

## Settings and parametrisation
There are five market settings that are set when a new session is created.
As usual in oTree, you are asked to choose the application and set the number of participants.
When clicking on *configurate session* you can set 4 more parameters, which are the market time in seconds, whether roles are randomised between rounds, whether short selling and buying on margin is allowed.

Other settings and parameters are either set in the respective ``__init__.py`` file or transmitted via in comma separated format.
For example, the number of (trial) rounds, the endowment and payment parameters are set in the constants ([C](https://otree.readthedocs.io/en/latest/models.html?highlight=constants#constants)) table.
Furthermore, with n assets you can specify in the ``__init__.py`` file the names of the assets via the list *ASSET_NAMES*. 
For more substantial changes, e.g. changes of the role, endowment, or profit structures, please adapt the respective functions.

### Information and partitions denomination
I think I found a quite convenient approach to distribute information.
This approach is based on information partitions and truthful disclosure of partitions.
The partition names are specified in the ``__init__.py`` file via the list *PARTITIONS_NAMES* and the unit value via the list *PARTITIONS_UNIT_VALUES*.
The amount of units of each partition is specified in comma separated format in the ``_parameters/assetPartition.csv`` file.

Different information structures can similarly be implemented.
Modifications must consider various processes.
There is the process how information is loaded in the function **define_asset_value()** and in the AssetsPartitions table, how roles are attributed with information in the function **define_role_information_structure()**, and how participants are attributed with information in function **assign_role_attr()**.
It is also very important to adjust the way how information is visualised to participants in the respective JavaScript file, which is either ``_static/sCDAstatic/scriptSAssetInfo.js`` or ``_static/nCDAstatic/scriptnAssetsInfo.js``.

## Disclaimer
The code is provided for educational and academic purposes and you agree that you use such code entirely at your own risk.

## References

- *<a id="Chen2016" href="https://doi.org/10.1016/j.jbef.2015.12.001"> Chen, Daniel L., Martin Schonger, Chris Wickens</a>*. 2016. **oTree—An open-source platform for laboratory, online, and field experiments**. *Journal of Behavioral and Experimental Finance* 9 88-97.
[![DOI:10.1016/j.jbef.2015.12.001](https://zenodo.org/badge/DOI/10.1016/j.jbef.2015.12.001.svg)](https://doi.org/10.1016/j.jbef.2015.12.001)

- *<a id="Merl2023" href="https://doi.org/10.1016/j.finmar.2023.100839"> Merl, Robert, Stefan Palan, Dominik Schmidt, Thomas Stöckl</a>*.  2023. **Insider trading legislation and trader migration**. *Journal of Financial Markets* 66.
[![DOI:10.1016/j.finmar.2023.100839](https://zenodo.org/badge/DOI/10.1016/j.finmar.2023.100839.svg)](https://doi.org/10.1016/j.finmar.2023.100839)

- *<a id="Palan2020" href="https://doi.org/10.1016/j.finmar.2023.100839">Palan, Stefan, Jürgen Huber, Larissa Senninger</a>*. 2020. **Aggregation mechanisms for crowd predictions**. *Experimental Economics* 23 (3) 788-814. 
[![DOI:10.1007/s10683-019-09631-0](https://zenodo.org/badge/DOI/10.1007/s10683-019-09631-0.svg)](https://doi.org/10.1007/s10683-019-09631-0)


