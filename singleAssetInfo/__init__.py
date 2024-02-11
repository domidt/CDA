from otree.api import *
import time
import random
from operator import itemgetter
from ast import literal_eval

doc = """Continuous double auction market with information partitions"""

PARTITIONS_NAMES = ['2E', '1E', '50c', '20c', '10c', '5c', '2c', '1c']
PARTITIONS_UNIT_VALUES = [2, 1, .5, .2, .1, .05, .02, .01]


class C(BaseConstants):
    NAME_IN_URL = 'sCDAInfo'
    PLAYERS_PER_GROUP = None
    num_trial_rounds = 1
    NUM_ROUNDS = 3  # incl. trial periods
    base_payment = cu(25)
    multiplier = 90
    min_payment_in_round = cu(0)
    min_payment = cu(4)
    num_assets_MIN = 20
    num_assets_MAX = 35
    decimals = 2
    marketTime = 210  # needed to initialize variables but exchanged by session_config


class Subsession(BaseSubsession):
    offerID = models.IntegerField(initial=0)
    orderID = models.IntegerField(initial=0)
    transactionID = models.IntegerField(initial=0)


class AssetsPartitions(ExtraModel):
    assetID = models.IntegerField()
    partitionID = models.IntegerField()
    amount = models.IntegerField()


def vars_for_admin_report(subsession):
    # this function defines the values sent to the admin report page
    groups = subsession.get_groups()
    period = subsession.round_number
    payoffs = sorted([p.payoff for p in subsession.get_players()])
    market_times = sorted([g.marketTime for g in groups])
    highcharts_series = []
    trades = [{'x': tx.transactionTime, 'y': tx.price, 'name': 'Trades'} for tx in Transaction.filter() if tx.Period == period and tx.group in groups]
    highcharts_series.append({'name': 'Trades', 'data': trades, 'type': 'scatter', 'id': 'trades', 'marker': {'symbol': 'circle'}})
    bids = [{'x': bx.BATime, 'y': bx.bestBid, 'name': 'Bids'} for bx in BidAsks.filter() if bx.Period == period and bx.BATime and bx.bestBid]
    highcharts_series.append({'name': 'Bids', 'data': bids, 'type': 'line', 'id': 'bids', 'lineWidth': 2})
    asks = [{'x': ax.BATime, 'y': ax.bestAsk, 'name': 'Asks'} for ax in BidAsks.filter() if ax.Period == period and ax.BATime and ax.bestAsk]
    highcharts_series.append({'name': 'Asks', 'data': asks, 'type': 'line', 'id': 'bids', 'lineWidth': 2})
    return dict(
        marketTimes=market_times,
        payoffs=payoffs,
        series=highcharts_series,
    )


class Group(BaseGroup):
    marketTime = models.FloatField(initial=C.marketTime)
    marketStartTime = models.FloatField()
    marketEndTime = models.FloatField()
    randomisedTypes = models.BooleanField()
    numAssets = models.IntegerField(initial=0)
    numParticipants = models.IntegerField(initial=0)
    numInformed = models.IntegerField()
    numActiveParticipants = models.IntegerField(initial=0)
    assetNames = models.LongStringField()
    aggAssetsValue = models.FloatField()
    assetValue = models.FloatField()
    valueStructureNumUnits = models.LongStringField()
    valueStructureValueUnits = models.LongStringField()
    bestAsk = models.FloatField()
    bestBid = models.FloatField()
    roleList = models.LongStringField()
    roleStructure = models.LongStringField()
    roleInfoStructure = models.LongStringField()
    transactions = models.IntegerField(initial=0, min=0)
    marketBuyOrders = models.IntegerField(initial=0, min=0)
    marketSellOrders = models.IntegerField(initial=0, min=0)
    transactedVolume = models.IntegerField(initial=0, min=0)
    marketBuyVolume = models.IntegerField(initial=0, min=0)
    marketSellVolume = models.IntegerField(initial=0, min=0)
    limitOrders = models.IntegerField(initial=0, min=0)
    limitBuyOrders = models.IntegerField(initial=0, min=0)
    limitSellOrders = models.IntegerField(initial=0, min=0)
    limitVolume = models.IntegerField(initial=0, min=0)
    limitBuyVolume = models.IntegerField(initial=0, min=0)
    limitSellVolume = models.IntegerField(initial=0, min=0)
    cancellations = models.IntegerField(initial=0, min=0)
    cancelledVolume = models.IntegerField(initial=0, min=0)


def random_types(group: Group):
    # this code is run at the first WaitToStart page when all participants arrived
    # this function returns a binary variable to the group table whether roles should be randomised between periods.
    return group.session.config['randomise_types']  # currently the binary value is retrieved from the config variables


def define_role_structure(group: Group):
    # this code is run at the first WaitToStart page, within the initiate_group() function, when all participants arrived
    # this function determines the number of participants of each role
    group.roleList = str(['I3', 'I2', 'I1', 'I0', 'observer'])  # ordered accourding to importance, i.e., the are filled accordingly
    num_participants = group.numParticipants
    num_I3 = int(round(1/4 * num_participants, 0))  # 1/4 is informed about 50c, 20c, and 10c
    num_I2 = int(round(1/4 * num_participants, 0))  # 1/4 is informed about 2E and 2c
    num_I1 = int(round(1/4 * num_participants, 0))  # 1/4 is informed about 1E and 5c
    num_observer = 0
    num_I0 = max(0, num_participants - num_I3 - num_I2 - num_I1 - num_observer)  # uninformed traders
    group.roleStructure = str({'observer': num_observer, 'I0': num_I0, 'I1': num_I1, 'I2': num_I2, 'I3': num_I3})


def define_role_information_structure(group: Group):
    # this code is run at the first WaitToStart page, within the initiate_group() function, when all participants arrived
    # for each role, this function specifies the partitions a role is informed
    group.roleInfoStructure = str({'I0': {'2E': 0, '1E': 0, '50c': 0, '20c': 0, '10c': 0, '5c': 0, '2c': 0, '1c': 0},
                                   'I1': {'2E': 0, '1E': 1, '50c': 0, '20c': 0, '10c': 0, '5c': 1, '2c': 0, '1c': 0},
                                   'I2': {'2E': 1, '1E': 0, '50c': 0, '20c': 0, '10c': 0, '5c': 0, '2c': 1, '1c': 0},
                                   'I3': {'2E': 0, '1E': 0, '50c': 1, '20c': 1, '10c': 1, '5c': 0, '2c': 0, '1c': 0}
                                   })


def assign_types(group: Group):
    # this code is run at the first WaitToStart page, within the initiate_group() function, when all participants arrived
    # this function allocates traders' types at the beginning of the session or when randomised.
    players = group.get_players()
    role_list = literal_eval(group.roleList)
    if group.randomisedTypes or Subsession.round_number == 1:
        ii = group.numParticipants  # number of traders without type yet
        for r in role_list:  # for each role
            k = 0  # number of players assigned this role
            max_k = literal_eval(group.roleStructure)[r]  # number of players to be assigned with this role
            while k < max_k and ii > 0:  # until enough role 'r' types are assigned
                rand_num = round(random.uniform(a=0, b=1) * ii, 0)
                i = 0
                for p in players:
                    if p.isParticipating and i < rand_num and not p.field_maybe_none('roleID'):
                        i += 1
                        if rand_num == i:
                            ii -= 1
                            p.roleID = str(r)
                            p.participant.vars['roleID'] = str(r)
                            k += 1
                    if not p.isParticipating and not p.field_maybe_none('roleID'):
                        p.roleID = str('not participating')
                        p.participant.vars['roleID'] = str('not participating')
    else:
        for p in players:
            p.roleID = p.participant.vars['roleID']


def define_asset_value(group: Group):
    # this code is run at the first WaitToStart page, within the initiate_group() function, when all participants arrived
    # this function determines the BBV and shares the information to the players table.
    if group.round_number > C.num_trial_rounds:
        assets_partition = read_csv('_parameters/assetsPartitions.csv', AssetsPartitions)
        units = {r['partitionID']: r['amount'] for r in assets_partition if r['assetID'] == group.round_number - C.num_trial_rounds}
    else:  # in trail the amount of coins is randomly drawn
        units = {partition_id + 1: int(round(random.uniform(a=0, b=1) * 19 + 1, 0)) for partition_id in range(len(PARTITIONS_NAMES))}
    num_units = {PARTITIONS_NAMES[partition_id]: units[partition_id + 1] for partition_id in range(len(PARTITIONS_NAMES))}
    group.valueStructureNumUnits = str(num_units)
    value_units = {PARTITIONS_NAMES[i]: PARTITIONS_UNIT_VALUES[i] for i in range(len(PARTITIONS_NAMES))}
    group.valueStructureValueUnits = str(value_units)
    total_value = 0
    for name in PARTITIONS_NAMES:
        total_value += value_units[name] * num_units[name]
    group.aggAssetsValue = total_value
    group.assetValue = group.aggAssetsValue  ## / group.numAssets ## The asset should actually just have the value according to the outstanding assets, but this information is negligible for a in-class


def count_participants(group: Group):
    # this code is run at the first WaitToStart page, within the initiate_group() function, when all participants arrived
    # this function determines the number of actual participants.
    if group.round_number == 1:
        for p in group.get_players():
            if p.isParticipating == 1:
                group.numParticipants += 1
    else:  # since player.isParticipating is not newly assign with a value by a click or a timeout, I take the value from the previous round
        for p in group.get_players():
            pr = p.in_round(group.round_number - 1)
            p.isParticipating = pr.isParticipating
        group.numParticipants = group.session.vars['numParticipants']
    group.session.vars['numParticipants'] = group.numParticipants


def initiate_group(group: Group):
    # this code is run at the first WaitToStart page when all participants arrived
    # this function starts substantial calculations on group level.
    count_participants(group=group)
    define_asset_value(group=group)
    define_role_structure(group=group)
    define_role_information_structure(group=group)
    assign_types(group=group)


def get_max_time(group: Group):
    # this code is run at the WaitingMarket page just before the market page when all participants arrived
    # this function returns the duration time of a market.
    return group.session.config['market_time']  # currently the binary value is retrieved from the config variables


class Player(BasePlayer):
    informed = models.BooleanField(choices=((True, 'informed'), (False, 'uninformed')))
    isParticipating = models.BooleanField(choices=((True, 'active'), (False, 'inactive')), initial=0)  ## describes whether this participant is participating in this round, i.e., whether they pressed the 'next' button.
    isObserver = models.BooleanField(choices=((True, 'active'), (False, 'inactive')), initial=0)  ## describes a participant role as active trader or observer
    roleID = models.StringField()
    information = models.LongStringField()
    allowShort = models.BooleanField(initial=True)
    allowLong = models.BooleanField(initial=True)
    assetValue = models.FloatField()
    initialCash = models.FloatField(initial=0, decimal=C.decimals)
    initialAssets = models.IntegerField(initial=0)
    initialEndowment = models.FloatField(initial=0, decimal=C.decimals)
    cashHolding = models.FloatField(initial=0, decimal=C.decimals)
    assetsHolding = models.IntegerField(initial=0)
    endEndowment = models.FloatField(initial=0, decimal=C.decimals)
    capLong = models.FloatField(initial=0, min=0, decimal=C.decimals)
    capShort = models.IntegerField(initial=0, min=0)
    transactions = models.IntegerField(initial=0, min=0)
    marketOrders = models.IntegerField(initial=0, min=0)
    marketBuyOrders = models.IntegerField(initial=0, min=0)
    marketSellOrders = models.IntegerField(initial=0, min=0)
    transactedVolume = models.IntegerField(initial=0, min=0)
    marketOrderVolume = models.IntegerField(initial=0, min=0)
    marketBuyVolume = models.IntegerField(initial=0, min=0)
    marketSellVolume = models.IntegerField(initial=0, min=0)
    limitOrders = models.IntegerField(initial=0, min=0)
    limitBuyOrders = models.IntegerField(initial=0, min=0)
    limitSellOrders = models.IntegerField(initial=0, min=0)
    limitVolume = models.IntegerField(initial=0, min=0)
    limitBuyVolume = models.IntegerField(initial=0, min=0)
    limitSellVolume = models.IntegerField(initial=0, min=0)
    limitOrderTransactions = models.IntegerField(initial=0, min=0)
    limitBuyOrderTransactions = models.IntegerField(initial=0, min=0)
    limitSellOrderTransactions = models.IntegerField(initial=0, min=0)
    limitVolumeTransacted = models.IntegerField(initial=0, min=0)
    limitBuyVolumeTransacted = models.IntegerField(initial=0, min=0)
    limitSellVolumeTransacted = models.IntegerField(initial=0, min=0)
    cancellations = models.IntegerField(initial=0, min=0)
    cancelledVolume = models.IntegerField(initial=0, min=0)
    cashOffered = models.FloatField(initial=0, min=0, decimal=C.decimals)
    assetsOffered = models.IntegerField(initial=0, min=0)
    tradingProfit = models.FloatField(initial=0)
    wealthChange = models.FloatField(initial=0)
    finalPayoff = models.CurrencyField(initial=0)
    selectedRound = models.IntegerField(initial=1)


def asset_endowment(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a participant's initial asset endowment
    return int(random.uniform(a=C.num_assets_MIN, b=C.num_assets_MAX))


def short_allowed(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a binary variable whether short selling is allowed
    group = player.group
    return group.session.config['short_selling']  # currently the binary value is retrieved from the config variables


def long_allowed(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a binary variable whether buying on margin is allowed
    group = player.group
    return group.session.config['margin_buying']  # currently the binary value is retrieved from the config variables


def asset_short_limit(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a participant's short selling limits if that is allowed
    if player.allowShort:
        return player.initialAssets  # currently the short selling limit is set equal to the asset endowment
    else:
        return 0


def cash_endowment(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a participant's initial cash endowment
    group = player.group
    return float(round(random.uniform(a=C.num_assets_MIN, b=C.num_assets_MAX) * group.assetValue, C.decimals))  ## the multiplication with the asset value garanties a cash to asset ratio of 1 in the market


def cash_long_limit(player: Player):
    # this code is run at the first WaitToStart page, within the initiate_player() function, when all participants arrived
    # this function returns a participant's buying on margin limits if that is allowed
    if player.allowLong:
        return player.initialCash  # currently the buying on margin limit is set equal to the cash endowment
    else:
        return 0


def assign_role_attr(player: Player, role_id):
    # this code is run at the first WaitToStart page, within the set_player_info() function, when all participants arrived
    # this function determines a participant's attributes in terms of being active or observer, and distributes information
    group = player.group
    role_info_structure = literal_eval(group.roleInfoStructure)
    num_units = literal_eval(group.valueStructureNumUnits)
    value_units = literal_eval(group.valueStructureValueUnits)
    info = []
    if role_id == 'observer':
        player.participant.vars['isObserver'] = True
        player.participant.vars['informed'] = False
    elif role_id == 'I0':
        player.participant.vars['isObserver'] = False
        player.participant.vars['informed'] = False
    elif role_id in group.roleList:
        player.participant.vars['isObserver'] = False
        player.participant.vars['informed'] = True
        info = [[partition, value_units[partition], num_units[partition], round(value_units[partition] * num_units[partition], C.decimals)] for partition in PARTITIONS_NAMES if role_info_structure[role_id][partition] == 1]
    player.information = str(info)


def initiate_player(player: Player):
    # this code is run at the first WaitToStart page when all participants arrived
    # this function starts substantial calculations on player level.
    group = player.group
    if not player.isObserver:
        initial_cash = cash_endowment(player=player)
        player.initialCash = initial_cash
        player.cashHolding = initial_cash
        player.allowLong = long_allowed(player=player)
        player.capLong = cash_long_limit(player=player)
        initial_assets = asset_endowment(player=player)
        player.initialAssets = initial_assets
        group.numAssets += player.initialAssets
        player.assetsHolding = initial_assets
        player.allowShort = short_allowed(player=player)
        player.capShort = asset_short_limit(player=player)


def set_player_info(player: Player):
    # this code is run at the first WaitToStart page when all participants arrived.
    # this function initiates the information distribution process and retrieves player characteristics from the participants table.
    assign_role_attr(player=player, role_id=player.field_maybe_none('roleID'))
    player.isObserver = player.participant.vars['isObserver']
    player.informed = player.participant.vars['informed']


def live_method(player: Player, data):
    # this code is run at the market page whenever a participants updates the page or a new order is created.
    # this function receives orders and processes them, furthermore, it sends the new order book to participant.
    if not data or 'operationType' not in data:
        return
    key = data['operationType']
    highcharts_series = []
    group = player.group
    period = group.round_number
    players = group.get_players()
    if key == 'limit_order':
        limit_order(player, data)
    elif key == 'cancel_limit':
        cancel_limit(player, data)
    elif key == 'market_order':
        transaction(player, data)
    offers = Limit.filter(group=group)
    transactions = Transaction.filter(group=group)
    if transactions:
        hc_data = [{'x': tx.transactionTime, 'y': tx.price, 'name': 'Trades'} for tx in Transaction.filter(group=group)]
        highcharts_series.append({'name': 'Trades', 'data': hc_data})
    else:
        highcharts_series = []
    best_bid = group.field_maybe_none('bestBid')
    best_ask = group.field_maybe_none('bestAsk')
    BidAsks.create(  # observe Bids and Asks of respective asset before the request
        group=group,
        Period=period,
        orderID=group.subsession.orderID,
        bestBid=best_bid,
        bestAsk=best_ask,
        BATime=round(float(time.time() - player.group.marketStartTime), C.decimals),
        timing='before',
        operationType=key,
    )
    bids = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID] for offer in offers if offer.isActive and offer.isBid], reverse=True, key=itemgetter(0))
    asks = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID] for offer in offers if offer.isActive and not offer.isBid], key=itemgetter(0))
    msgs = News.filter(group=group)
    if asks:
        best_ask = asks[0][0]
        group.bestAsk = best_ask
    else:
        best_ask = None
    if bids:
        best_bid = bids[0][0]
        group.bestBid = best_bid
    else:
        best_bid = None
    BidAsks.create(  # observe Bids and Asks of respective asset after the request
        group=group,
        Period=period,
        orderID=group.subsession.orderID,
        bestBid=best_bid,
        bestAsk=best_ask,
        BATime=round(float(time.time() - player.group.marketStartTime), C.decimals),
        timing='after',
        operationType=key,
    )
    if key == 'market_start':
        players = [player]
    return {  # the next lines define the information send to participants
        p.id_in_group: dict(
            bids=bids,
            asks=asks,
            trades=sorted([[t.price, t.transactionVolume, t.transactionTime, t.sellerID] for t in transactions if (t.makerID == p.id_in_group or t.takerID == p.id_in_group)], reverse = True, key=itemgetter(2)),
            cashHolding=p.cashHolding,
            assetsHolding=p.assetsHolding,
            highcharts_series=highcharts_series,
            news=sorted([[m.msg, m.msgTime, m.playerID] for m in msgs if m.playerID == p.id_in_group], reverse=True, key=itemgetter(1))
        )
        for p in players
    }


def calc_period_profits(player: Player):
    # this code is run at the results wait page.
    # this function assesses a participant's initial and final endowment and calculates the period income.
    initial_endowment = player.initialCash + player.assetValue * player.initialAssets
    end_endowment = player.cashHolding + player.assetValue * player.assetsHolding
    player.initialEndowment = initial_endowment
    player.endEndowment = end_endowment
    player.tradingProfit = end_endowment - initial_endowment
    if not player.isObserver or initial_endowment == 0:
        player.wealthChange = (end_endowment - initial_endowment) / initial_endowment
    else:
        player.wealthChange = 0
    player.payoff = max(C.base_payment + C.multiplier * player.wealthChange, C.min_payment_in_round)


def calc_final_profit(player: Player):
    # this code is run at the final results page.
    # this function performs a random draw of period income and calculates a participant's payoff.
    period_payoffs = [p.payoff for p in player.in_all_rounds()]
    r = int(round(random.uniform(a=0, b=1) * (C.NUM_ROUNDS - C.num_trial_rounds), 0) + C.num_trial_rounds)
    if r < C.num_trial_rounds:
        r = C.num_trial_rounds
    elif r >= C.NUM_ROUNDS:
        r = C.NUM_ROUNDS
    player.selectedRound = r - C.num_trial_rounds
    player.finalPayoff = period_payoffs[r - 1]


def custom_export(players):
    # this function defines the variables that are downloaded in customised tables
    # Export Limits
    yield ['TableName', 'sessionID', 'offerID', 'group', 'Period', 'maker', 'price', 'limitVolume', 'isBid', 'offerID', 'orderID', 'offerTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    limits = Limit.filter()
    for l in limits:
        yield ['Limits', l.group.session.code, l.offerID, l.group.id_in_subsession, l.group.round_number, l.makerID, l.price, l.limitVolume, l.isBid, l.orderID, l.offerTime, l.remainingVolume, l.isActive, l.bestAskBefore, l.bestBidBefore, l.bestAskAfter, l.bestBidAfter]

    # Export Transactions
    yield ['TableName', 'sessionID', 'transactionID', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'orderID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    trades = Transaction.filter()
    for t in trades:
        yield ['Transactions', t.group.session.code, t.transactionID, t.group.id_in_subsession, t.group.round_number, t.makerID, t.takerID, t.price, t.transactionVolume, t.limitVolume, t.sellerID, t.buyerID, t.isBid, t.offerID, t.orderID, t.offerTime, t.transactionTime, t.remainingVolume, t.isActive, t.bestAskBefore, t.bestBidBefore, t.bestAskAfter, t.bestBidAfter]

    # Export Orders
    yield ['TableName', 'sessionID', 'orderID', 'orderType', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'transactionID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    orders = Order.filter()
    for o in orders:
        yield ['Orders', o.group.session.code, o.orderID, o.orderType, o.group.id_in_subsession, o.group.round_number, o.makerID, o.takerID, o.price, o.transactionVolume, o.limitVolume, o.sellerID, o.buyerID, o.isBid, o.offerID, o.transactionID, o.offerTime, o.transactionTime, o.remainingVolume, o.isActive, o.bestAskBefore, o.bestBidBefore, o.bestAskAfter, o.bestBidAfter]

    # Export BidAsk
    yield ['TableName', 'sessionID', 'orderID', 'operationType', 'group', 'Period', 'bestAsk', 'bestBid', 'BATime', 'timing']
    bidasks = BidAsks.filter()
    for b in bidasks:
        yield ['BidAsks', b.group.session.code, b.orderID, b.operationType, b.group.id_in_subsession, b.group.round_number, b.bestAsk, b.bestBid, b.BATime, b.timing]

    # Export News
    yield ['TableName', 'sessionID', 'message', 'group', 'Period', 'playerID', 'msgTime']
    news = News.filter()
    for n in news:
        yield ['BidAsks', n.group.session.code, n.msg, n.group.id_in_subsession, n.group.round_number, n.playerID, n.msgTime]


class Limit(ExtraModel):
    offerID = models.IntegerField()
    orderID = models.IntegerField()
    makerID = models.IntegerField()
    group = models.Link(Group)
    Period = models.IntegerField()
    maker = models.Link(Player)
    limitVolume = models.IntegerField()
    price = models.FloatField(decimal=C.decimals)
    transactedVolume = models.IntegerField()
    remainingVolume = models.IntegerField()
    amount = models.FloatField(decimal=C.decimals)
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    offerTime = models.FloatField(doc="Timestamp (seconds since beginning of trading)")
    isActive = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    bestBidBefore = models.FloatField()
    bestAskBefore = models.FloatField()
    bestAskAfter = models.FloatField()
    bestBidAfter = models.FloatField()


def limit_order(player: Player, data):
    # this code is run at the market page, within the live_method(), whenever a participants aimes to create a limit order.
    # this function processes limit orders and creates new entries in the Limit and Order tables.
    maker_id = player.id_in_group
    group = player.group
    period = group.round_number
    if player.isObserver:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: you are an observer who cannot place a limit order.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if not (data['isBid'] >= 0 and data['limitPrice'] and data['limitVolume']):
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: misspecified price, volume or asset.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    price = round(float(data['limitPrice']), C.decimals)
    is_bid = bool(data['isBid'] == 1)
    limit_volume = int(data['limitVolume'])
    if not (price > 0 and limit_volume > 0):
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: misspecified price or volume.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if is_bid and player.cashHolding + player.capLong - player.cashOffered - limit_volume * price < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient cash available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    if not is_bid and player.assetsHolding + player.capShort - player.assetsOffered - limit_volume < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient assets available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    elif (is_bid and best_ask_before is not None and price > best_ask_before) or (not is_bid and best_bid_before is not None and price < best_bid_before):
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: there is a limit order with the same or a more interesting price available in the order book.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    offer_id = player.subsession.offerID + 1
    player.subsession.offerID += 1
    while len(Limit.filter(group=group, offerID=offer_id)) > 0:  # to prevent duplicates in offerID
        offer_id += 1
    offer_time = round(float(time.time() - player.group.marketStartTime), C.decimals)
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    while len(Order.filter(group=group, offerID=order_id)) > 0:  # to prevent duplicates in orderID
        order_id += 1
    if best_ask_before:
        best_ask_after = best_ask_before
    else:
        best_ask_before = -1
        best_ask_after = -1
    if best_bid_before:
        best_bid_after = best_bid_before
    else:
        best_bid_before = -1
        best_bid_after = -1
    if is_bid and (best_bid_before == -1 or price >= best_bid_before):
        best_bid_after = price
    elif not is_bid and (best_ask_before == -1 or price <= best_ask_before):
        best_ask_after = price
    Limit.create(
        offerID=offer_id,
        orderID=order_id,
        makerID=maker_id,
        group=group,
        Period=period,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=0,
        remainingVolume=limit_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        offerTime=offer_time,
        isActive=True,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    Order.create(
        orderID=order_id,
        offerID=offer_id,
        makerID=maker_id,
        group=group,
        Period=period,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=0,
        remainingVolume=limit_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='limitOrder',
        offerTime=offer_time,
        orderTime=offer_time,
        isActive=True,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    player.limitOrders += 1
    player.limitVolume += limit_volume
    group.limitOrders += 1
    group.limitVolume += limit_volume
    if is_bid:
        player.cashOffered += limit_volume * price
        player.limitBuyOrders += 1
        player.limitBuyVolume += limit_volume
        group.limitBuyOrders += 1
        group.limitBuyVolume += limit_volume
    else:
        player.assetsOffered += limit_volume
        player.limitSellOrders += 1
        player.limitSellVolume += limit_volume
        group.limitSellOrders += 1
        group.limitSellVolume += limit_volume


def cancel_limit(player: Player, data):
    # this code is run at the market page, within the live_method(), whenever a participants aimes to create a limit order.
    # this function processes limit order withdrawals and creates new entries in the Order table.
    if 'offerID' not in data:
        return
    maker_id = int(data['makerID'])
    group = player.group
    period = group.round_number
    if player.isObserver:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: you are an observer who cannot withdraw a limit order.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if maker_id != player.id_in_group:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: you can withdraw your own orders only.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    offer_id = int(data['offerID'])
    # we need to update Limit table entry
    offers = [o for o in Limit.filter(group=group) if o.offerID == offer_id]
    if not offers or len(offers) != 1:
        print('Error: too few or too many limits found while withdrawing.')
        return
    offers[0].isActive = False
    is_bid = offers[0].isBid
    limit_volume = offers[0].limitVolume
    remaining_volume = offers[0].remainingVolume
    price = offers[0].price
    transacted_volume = offers[0].transactedVolume
    offer_time = offers[0].offerTime
    if price != float(data['limitPrice']) or is_bid != bool(data['isBid'] == 1):
        print('Odd request when player', maker_id, 'cancelled an order', data)
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    while len(Order.filter(group=group, offerID=order_id)) > 0:  # to prevent duplicates in orderID
        order_id += 1
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    limitoffers = Limit.filter(group=group)
    best_bid_after = max([offer.price for offer in limitoffers if offer.isActive and offer.isBid] or [-1])
    best_ask_after = min([offer.price for offer in limitoffers if offer.isActive and not offer.isBid] or [-1])
    if not best_ask_before:
        best_ask_before = -1
    if not best_bid_before:
        best_bid_before = -1
    Order.create(
        orderID=order_id,
        offerID=offer_id,
        makerID=maker_id,
        group=group,
        Period=period,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=transacted_volume,
        remainingVolume=0,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='cancelLimitOrder',
        offerTime=offer_time,
        orderTime=float(time.time() - player.group.marketStartTime),
        isActive=False,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    player.cancellations += 1
    player.cancelledVolume += remaining_volume
    group.cancellations += 1
    group.cancelledVolume += remaining_volume
    if is_bid:
        player.cashOffered -= remaining_volume * price
    else:
        player.assetsOffered -= remaining_volume


class Order(ExtraModel):
    orderID = models.IntegerField()
    offerID = models.IntegerField()
    transactionID = models.IntegerField()
    makerID = models.IntegerField()
    takerID = models.IntegerField()
    sellerID = models.IntegerField()
    buyerID = models.IntegerField()
    group = models.Link(Group)
    Period = models.IntegerField()
    limitVolume = models.IntegerField()
    transactionVolume = models.IntegerField()
    transactedVolume = models.IntegerField()
    remainingVolume = models.IntegerField()
    price = models.FloatField(decimal=C.decimals)
    amount = models.FloatField(decimal=C.decimals)
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    orderType = models.StringField()
    orderTime = models.FloatField(doc="Timestamp (seconds since beginning of trading)")
    offerTime = models.FloatField()
    transactionTime = models.FloatField()
    isActive = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    bestBidBefore = models.FloatField()
    bestAskBefore = models.FloatField()
    bestAskAfter = models.FloatField()
    bestBidAfter = models.FloatField()


class Transaction(ExtraModel):
    transactionID = models.IntegerField()
    offerID = models.IntegerField()
    orderID = models.IntegerField()
    makerID = models.IntegerField()
    takerID = models.IntegerField()
    sellerID = models.IntegerField()
    buyerID = models.IntegerField()
    group = models.Link(Group)
    Period = models.IntegerField()
    transactionVolume = models.IntegerField()
    limitVolume = models.IntegerField()
    remainingVolume = models.IntegerField()
    price = models.FloatField(decimal=C.decimals)
    amount = models.FloatField(decimal=C.decimals)
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    offerTime = models.FloatField()
    transactionTime = models.FloatField(doc="Timestamp (seconds since beginning of trading)")
    isActive = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    bestBidBefore = models.FloatField()
    bestAskBefore = models.FloatField()
    bestAskAfter = models.FloatField()
    bestBidAfter = models.FloatField()


def transaction(player: Player, data):
    # this code is run at the market page, within the live_method(), whenever a participants aimes to acccept a limit order, i.e., when a market order is made.
    # this function processes market orders and creates new entries in the Transaction and Order tables, and updates the Limit table.
    if 'offerID' not in data:
        return
    offer_id = int(data['offerID'])
    taker_id = player.id_in_group
    group = player.group
    period = group.round_number
    if player.isObserver:
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: you are an observer who cannot accept a market order.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    limit_entry = Limit.filter(group=group, offerID=offer_id)
    if len(limit_entry) > 1:
        print('Limit entry is not well-defined: multiple entries with the same ID')
    limit_entry = limit_entry[0]
    transaction_volume = int(data['transactionVolume'])
    is_bid = limit_entry.isBid
    price = float(limit_entry.price)
    maker_id = int(limit_entry.makerID)
    remaining_volume = int(limit_entry.remainingVolume)
    limit_volume = int(limit_entry.limitVolume)
    if not (price > 0 and transaction_volume > 0): # check whether data is valid
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: misspecified volume.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if price != float(data['transactionPrice']) or is_bid != bool(data['isBid'] == 1):
        print('Odd request when player', maker_id, 'accepted an order', data, 'while in the order book we find', limit_entry)
    is_active = limit_entry.isActive
    if transaction_volume >= remaining_volume:
        transaction_volume = remaining_volume
        is_active = False
    if not is_bid and player.cashHolding + player.capLong - player.cashOffered - transaction_volume * price < 0:
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient cash available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    if is_bid and player.assetsHolding + player.capShort - player.assetsOffered - transaction_volume < 0:
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient assets available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    elif maker_id == taker_id:
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: own limit orders cannot be transacted.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if (is_bid and best_bid_before and price < best_bid_before) or (not is_bid and best_ask_before and price > best_ask_before) :
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            msg='Order rejected: there is a better offer available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    offer_time = round(float(limit_entry.offerTime), C.decimals)
    players = group.get_players()
    maker = [p for p in players if p.id_in_group == maker_id][0]
    if is_bid:
        [buyer, seller] = [maker, player]
        maker.cashOffered -= transaction_volume * price
        maker.limitBuyOrderTransactions += 1
        maker.limitBuyVolumeTransacted += transaction_volume
        player.marketSellOrders += 1
        player.marketSellVolume += transaction_volume
        group.marketSellOrders += 1
        group.marketSellVolume += transaction_volume
        seller_id = player.id_in_group
        buyer_id = maker.id_in_group
    else:
        [buyer, seller] = [player, maker]
        maker.assetsOffered -= transaction_volume  # undo offer holdings
        maker.limitSellOrderTransactions += 1
        maker.limitSellVolumeTransacted += transaction_volume
        player.marketBuyOrders += 1
        player.marketBuyVolume += transaction_volume
        group.marketBuyOrders += 1
        group.marketBuyVolume += transaction_volume
        seller_id = maker.id_in_group
        buyer_id = seller.id_in_group
    transaction_id = player.subsession.transactionID + 1
    player.subsession.transactionID += 1
    while len(Transaction.filter(group=group, offerID=transaction_id)) > 0:  # to prevent duplicates in transactionID
        transaction_id += 1
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    while len(Order.filter(group=group, offerID=order_id)) > 0:  # to prevent duplicates in orderID
        order_id += 1
    transaction_time = round(float(time.time() - group.marketStartTime), C.decimals)
    limit_entry.transactedVolume += transaction_volume
    limit_entry.isActive = is_active
    transacted_volume = limit_entry.transactedVolume
    limit_entry.remainingVolume -= transaction_volume
    buyer.cashHolding -= transaction_volume * price
    seller.cashHolding += transaction_volume * price
    buyer.transactions += 1
    buyer.transactedVolume += transaction_volume
    buyer.assetsHolding += transaction_volume
    seller.transactions += 1
    seller.transactedVolume += transaction_volume
    seller.assetsHolding -= transaction_volume
    maker.limitOrderTransactions += 1
    maker.limitVolumeTransacted += transaction_volume
    player.marketOrders += 1
    player.marketOrderVolume += transaction_volume
    group.transactions += 1
    group.transactedVolume += transaction_volume
    limitOffers = Limit.filter(group=group)
    best_bid_after = max([offer.price for offer in limitOffers if offer.isActive and offer.isBid] or [-1])
    best_ask_after = min([offer.price for offer in limitOffers if offer.isActive and not offer.isBid] or [-1])
    if not best_ask_before:
        best_ask_before = -1
    if not best_bid_before:
        best_bid_before = -1
    Transaction.create(
        transactionID=transaction_id,
        offerID=offer_id,
        orderID=order_id,
        makerID=maker_id,
        takerID=taker_id,
        sellerID=seller_id,
        buyerID=buyer_id,
        group=group,
        Period=period,
        price=price,
        transactionVolume=transaction_volume,
        remainingVolume=remaining_volume - transaction_volume,
        amount=transaction_volume * price,
        isBid=is_bid,
        transactionTime=transaction_time,
        offerTime=offer_time,
        isActive=is_active,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    Order.create(
        orderID=order_id,
        offerID=offer_id,
        transactionID=transaction_id,
        group=group,
        Period=period,
        makerID=maker_id,
        takerID=taker_id,
        sellerID=seller_id,
        buyerID=buyer_id,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=transacted_volume,
        remainingVolume=remaining_volume - transaction_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='marketOrder',
        orderTime=transaction_time,
        offerTime=offer_time,
        isActive=is_active,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )


class News(ExtraModel):
    player = models.Link(Player)
    playerID = models.IntegerField()
    group = models.Link(Group)
    Period = models.IntegerField()
    msg = models.StringField()
    msgTime = models.FloatField()


class BidAsks(ExtraModel):
    group = models.Link(Group)
    Period = models.IntegerField()
    assetValue = models.StringField()
    orderID = models.IntegerField()
    bestBid = models.FloatField()
    bestAsk = models.FloatField()
    BATime = models.FloatField()
    timing = models.StringField()
    operationType = models.StringField()


# PAGES
class Instructions(Page):
    form_model = 'player'
    form_fields = ['isParticipating']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            numTrials=C.num_trial_rounds,
            numRounds=C.NUM_ROUNDS - C.num_trial_rounds,
        )


class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.randomisedTypes = random_types(group=group)
        initiate_group(group=group)
        players = group.get_players()
        for p in players:
            set_player_info(player=p)
            p.assetValue = group.assetValue
            initiate_player(player=p)


class EndOfTrialRounds(Page):
    template_name = "_templates/endOfTrialRounds.html"

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.num_trial_rounds + 1 and C.num_trial_rounds > 0


class PreMarket(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            round=player.round_number - C.num_trial_rounds,
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            informed=player.informed,
            information=literal_eval(player.information),
            allowShort=player.allowShort,
            capShort=player.capShort,
            capLong=player.capLong,
            cashHolding=player.cashHolding,
        )


class WaitingMarket(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.marketStartTime = round(float(time.time()), C.decimals)
        group.marketTime = get_max_time(group=group)


class Market(Page):
    live_method = live_method
    timeout_seconds = Group.marketTime

    @staticmethod
    def js_vars(player: Player):
        group = player.group
        return dict(
            id_in_group=player.id_in_group,
            informed=player.informed,
            information=literal_eval(player.information),
            allowShort=player.allowShort,
            capShort=player.capShort,
            capLong=player.capLong,  # round(player.capLong, 2)
            cashHolding=player.cashHolding,
            assetsHolding=player.assetsHolding,
            marketTime=group.marketTime,
        )

    @staticmethod
    def get_timeout_seconds(player: Player):
        group = player.group
        return group.marketStartTime + group.marketTime - time.time()


class ResultsWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        for p in players:
            calc_period_profits(player=p)
            if group.round_number == C.NUM_ROUNDS:
                calc_final_profit(player=p)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            assetValue=round(player.assetValue, C.decimals),
            initialEndowment=round(player.initialEndowment, C.decimals),
            endEndowment=round(player.endEndowment, C.decimals),
            tradingProfit=round(player.tradingProfit, C.decimals),
            wealthChange=round(player.wealthChange*100, C.decimals),
            payoff=cu(round(player.payoff, C.decimals)),
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            assetValue=round(player.assetValue, C.decimals),
        )


class FinalResults(Page):
    template_name = "_templates/finalResults.html"

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payoff=cu(round(player.finalPayoff, 0)),
            periodPayoff=[[p.round_number - C.num_trial_rounds, round(p.payoff, C.decimals), round(p.tradingProfit, C.decimals), round(p.wealthChange * 100, C.decimals)] for p in player.in_all_rounds() if p.round_number > C.num_trial_rounds],
        )


page_sequence = [Instructions, WaitToStart, EndOfTrialRounds, PreMarket, WaitingMarket, Market, ResultsWaitPage, Results, FinalResults, ResultsWaitPage]
