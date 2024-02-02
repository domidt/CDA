from otree.api import *
import time
import random
from operator import itemgetter
from ast import literal_eval

doc = """Continuous double auction market"""


ASSET_NAMES = ['A', 'B', 'C', 'D']
NUM_ASSETS = len(ASSET_NAMES)


class C(BaseConstants):
    NAME_IN_URL = 'nCDA'
    PLAYERS_PER_GROUP = None
    num_trial_rounds = 1
    NUM_ROUNDS = 14  ## incl. trial periods
    base_payment = cu(25)
    multiplier = 90
    min_payment_in_round = cu(0)
    min_payment = cu(4)
    FV_MIN = 30
    FV_MAX = 85
    num_assets_MIN = 20
    num_assets_MAX = 35
    decimals = 2
    marketTime = 210  ## needed to initialize variables but exchanged by session_config


class Subsession(BaseSubsession):
    offerID = models.IntegerField(initial=0)
    orderID = models.IntegerField(initial=0)
    transactionID = models.IntegerField(initial=0)
    assetID = models.IntegerField(initial=0)


class AssetsInRound(ExtraModel):
    round_number = models.IntegerField()
    assetID = models.IntegerField()


def vars_for_admin_report(subsession):
    ## this function defines the values sent to the admin report page
    groups = subsession.get_groups()
    period = subsession.round_number
    num_assets_in_round = sorted([g.numAssetsInRound for g in groups])
    payoffs = sorted([p.payoff for p in subsession.get_players()])
    market_times = sorted([g.marketTime for g in groups])
    highcharts_series = []
    for i in range(1, NUM_ASSETS + 1):
        trade_data = [{'x': tx.transactionTime, 'y': tx.price, 'name': ASSET_NAMES[tx.assetID - 1]} for tx in Transaction.filter() if tx.Period == period and tx.group in groups and tx.assetID == i]
        highcharts_series.append({'name': ASSET_NAMES[i - 1], 'data': trade_data, 'type': 'scatter', 'id': 'trades', 'marker': {'symbol': 'circle'}})
        bids_data = [{'x': b.BATime, 'y': b.bestBid, 'name': ASSET_NAMES[b.assetID - 1]} for b in BidAsks.filter() if b.Period == period and b.group in groups and b.assetID == i and b.BATime and b.bestBid]
        highcharts_series.append({'name': 'Bids ' + ASSET_NAMES[i - 1], 'data': bids_data, 'type': 'line', 'id': 'bids', 'lineWidth': 2})
        asks_data = [{'x': a.BATime, 'y': a.bestAsk, 'name': ASSET_NAMES[a.assetID - 1]} for a in BidAsks.filter() if a.Period == period and a.group in groups and a.assetID == i and a.BATime and a.bestAsk]
        highcharts_series.append({'name': 'Asks ' + ASSET_NAMES[i - 1], 'data': asks_data, 'type': 'line', 'id': 'bids', 'lineWidth': 2})
    return dict(
        numAssetsInRound=num_assets_in_round,
        marketTimes=market_times,
        payoffs=payoffs,
        series=highcharts_series,
    )


class Group(BaseGroup):
    marketTime = models.FloatField(initial=C.marketTime)
    marketStartTime = models.FloatField()
    marketEndTime = models.FloatField()
    randomisedTypes = models.BooleanField()
    numAssets = models.LongStringField()
    numParticipants = models.IntegerField(initial=0)
    estNumTraders = models.IntegerField()
    numActiveParticipants = models.IntegerField(initial=0)
    assetNames = models.LongStringField()
    assetsInRound = models.LongStringField()
    assetNamesInRound = models.LongStringField()
    numAssetsInRound = models.IntegerField(initial=0)
    aggAssetsValue = models.LongStringField()
    assetValues = models.LongStringField()
    bestAsks = models.LongStringField()
    bestBids = models.LongStringField()
    transactions = models.LongStringField()
    marketBuyOrders = models.LongStringField()
    marketSellOrders = models.LongStringField()
    transactedVolume = models.LongStringField()
    marketBuyVolume = models.LongStringField()
    marketSellVolume = models.LongStringField()
    limitOrders = models.LongStringField()
    limitBuyOrders = models.LongStringField()
    limitSellOrders = models.LongStringField()
    limitVolume = models.LongStringField()
    limitBuyVolume = models.LongStringField()
    limitSellVolume = models.LongStringField()
    cancellations = models.LongStringField()
    cancelledVolume = models.LongStringField()


def random_types(group: Group):
    return group.session.config['randomise_types']


def num_traders(group: Group):
    return group.session.config['est_num_traders']


def assign_types(group: Group):
    # this method allocates traders' types at the beginning of the session or when randomised.
    ## this code is run when all participants arrived via the initiate group function
    players = group.get_players()
    if group.randomisedTypes or Subsession.round_number == 1:
        ii = group.numParticipants  # number of traders without type yet
        role_structure = {'observer': 0, 'trader': ii}
        for r in ['observer', 'trader']:  # for each role
            k = 0  # number of players assigned this role
            max_k = role_structure[r]  # number of players to be assigned with this role
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


def define_assets_in_round(group: Group):
    ## this function defines the assets available to trade in each round
    assets_sequence = {1: [1, 2],
                               2: [3, 4],
                               3: [1, 2],
                               4: [3, 4],
                               5: [1, 2],
                               6: [3, 4],
                               7: [1, 2],
                               8: [3, 4],
                               9: [1, 2],
                               10: [3, 4],
                               11: [1, 2],
                               12: [3, 4],
                               13: [1, 2],
                               14: [3, 4]
                               }
    group.assetsInRound = str(assets_sequence[group.round_number])
    group.assetNamesInRound = str([ASSET_NAMES[r - 1] for r in assets_sequence[group.round_number]])
    for r in assets_sequence[group.round_number]:
        group.numAssetsInRound += 1


def define_asset_value(group: Group):
    ## this method describes the BBV structure of an this round.
    asset_ids = literal_eval(group.assetsInRound)
    values = {a: round(random.uniform(a=C.FV_MIN, b=C.FV_MAX), C.decimals) for a in asset_ids}
    group.assetValues = str(values)


def count_participants(group: Group):
    if group.round_number == 1:
        for p in group.get_players():
            if p.isParticipating == 1:
                group.numParticipants += 1
    else:  ## since player.isParticipating is not newly assign with a value by a click or a timeout, I take the value from the previous round
        for p in group.get_players():
            pr = p.in_round(group.round_number - 1)
            p.isParticipating = pr.isParticipating
        group.numParticipants = group.session.vars['numParticipants']
    group.session.vars['numParticipants'] = group.numParticipants


def initiate_group(group: Group):
    ## this code is run when everyone arrived and the market is about to start
    count_participants(group=group)
    define_assets_in_round(group=group)
    define_asset_value(group=group)
    assign_types(group=group)
    initialize_vars(group=group)
    assets_in_round = literal_eval(group.assetsInRound)
    group.numAssets = str(set_initial(0, assets_in_round))


def get_max_time(group: Group):
    return group.session.config['market_time']


def initialize_vars(group: Group):
    # set initial values in groups to zero resp. None
    asset_ids = literal_eval(group.assetsInRound)
    group.transactions = str(set_initial(0, asset_ids))
    group.marketBuyOrders = str(set_initial(0, asset_ids))
    group.marketSellOrders = str(set_initial(0, asset_ids))
    group.transactedVolume = str(set_initial(0, asset_ids))
    group.marketBuyVolume = str(set_initial(0, asset_ids))
    group.marketSellVolume = str(set_initial(0, asset_ids))
    group.limitOrders = str(set_initial(0, asset_ids))
    group.limitBuyOrders = str(set_initial(0, asset_ids))
    group.limitSellOrders = str(set_initial(0, asset_ids))
    group.limitVolume = str(set_initial(0, asset_ids))
    group.limitBuyVolume = str(set_initial(0, asset_ids))
    group.limitSellVolume = str(set_initial(0, asset_ids))
    group.cancellations = str(set_initial(0, asset_ids))
    group.cancelledVolume = str(set_initial(0, asset_ids))
    group.bestAsks = str(set_initial(None, asset_ids))
    group.bestBids = str(set_initial(None, asset_ids))
    # set initial values in players to zero
    players = group.get_players()
    for p in players:
        p.assetsOffered = str(set_initial(0, asset_ids))
        p.transactions = str(set_initial(0, asset_ids))
        p.marketOrders = str(set_initial(0, asset_ids))
        p.marketBuyOrders = str(set_initial(0, asset_ids))
        p.marketSellOrders = str(set_initial(0, asset_ids))
        p.transactedVolume = str(set_initial(0, asset_ids))
        p.marketOrderVolume = str(set_initial(0, asset_ids))
        p.marketBuyVolume = str(set_initial(0, asset_ids))
        p.marketSellVolume = str(set_initial(0, asset_ids))
        p.limitOrders = str(set_initial(0, asset_ids))
        p.limitBuyOrders = str(set_initial(0, asset_ids))
        p.limitSellOrders = str(set_initial(0, asset_ids))
        p.limitVolume = str(set_initial(0, asset_ids))
        p.limitBuyVolume = str(set_initial(0, asset_ids))
        p.limitSellVolume = str(set_initial(0, asset_ids))
        p.limitOrderTransactions = str(set_initial(0, asset_ids))
        p.limitBuyOrderTransactions = str(set_initial(0, asset_ids))
        p.limitSellOrderTransactions = str(set_initial(0, asset_ids))
        p.limitVolumeTransacted = str(set_initial(0, asset_ids))
        p.limitBuyVolumeTransacted = str(set_initial(0, asset_ids))
        p.limitSellVolumeTransacted = str(set_initial(0, asset_ids))
        p.cancellations = str(set_initial(0, asset_ids))
        p.cancelledVolume = str(set_initial(0, asset_ids))


def set_initial(value, ids):
    return {id: value for id in ids}


class Player(BasePlayer):
    isParticipating = models.BooleanField(choices=((True, 'active'), (False, 'inactive')), initial=0)  ## describes whether this participant is participating in this round, i.e., whether they pressed the 'next' button.
    isObserver = models.BooleanField(choices=((True, 'active'), (False, 'inactive')), initial=0)  ## describes a participant role as active trader or observer
    roleID = models.StringField()
    allowShort = models.BooleanField(initial=True)
    allowLong = models.BooleanField(initial=True)
    assetValues = models.LongStringField()
    initialCash = models.FloatField(initial=0, decimal=C.decimals)
    initialAssets = models.LongStringField()
    initialEndowment = models.FloatField(initial=0, decimal=C.decimals)
    cashHolding = models.FloatField(initial=0, decimal=C.decimals)
    assetsHolding = models.LongStringField()
    endEndowment = models.FloatField(initial=0, decimal=C.decimals)
    capLong = models.FloatField(initial=0, min=0, decimal=C.decimals)
    capShort = models.LongStringField()
    transactions = models.LongStringField()
    marketOrders = models.LongStringField()
    marketBuyOrders = models.LongStringField()
    marketSellOrders = models.LongStringField()
    transactedVolume = models.LongStringField()
    marketOrderVolume = models.LongStringField()
    marketBuyVolume = models.LongStringField()
    marketSellVolume = models.LongStringField()
    limitOrders = models.LongStringField()
    limitBuyOrders = models.LongStringField()
    limitSellOrders = models.LongStringField()
    limitVolume = models.LongStringField()
    limitBuyVolume = models.LongStringField()
    limitSellVolume = models.LongStringField()
    limitOrderTransactions = models.LongStringField()
    limitBuyOrderTransactions = models.LongStringField()
    limitSellOrderTransactions = models.LongStringField()
    limitVolumeTransacted = models.LongStringField()
    limitBuyVolumeTransacted = models.LongStringField()
    limitSellVolumeTransacted = models.LongStringField()
    cancellations = models.LongStringField()
    cancelledVolume = models.LongStringField()
    cashOffered = models.FloatField(initial=0, min=0, decimal=C.decimals)
    assetsOffered = models.LongStringField()
    tradingProfit = models.FloatField(initial=0)
    wealthChange = models.FloatField(initial=0)


def asset_endowment(player: Player):
    group = player.group
    asset_ids = literal_eval(group.assetsInRound)
    return {asset_id: int(random.uniform(a=C.num_assets_MIN, b=C.num_assets_MAX)) for asset_id in asset_ids}


def short_allowed(player: Player):
    group = player.group
    return group.session.config['short_selling']


def long_allowed(player: Player):
    group = player.group
    return group.session.config['margin_buying']


def asset_short_limit(player: Player):
    if player.allowShort:
        return literal_eval(player.initialAssets)
    else:
        asset_ids = literal_eval(player.group.assetsInRound)
        return set_initial(0, asset_ids)


def cash_endowment(player: Player):
    group = player.group
    assets_in_round = literal_eval(group.assetsInRound)
    sum_asset_value = 0
    num_assets = 0
    for i in assets_in_round:
        num_assets += 1
        sum_asset_value += literal_eval(group.assetValues)[i]
    avg_asset_value = sum_asset_value / num_assets
    return float(round(random.uniform(a=C.num_assets_MIN, b=C.num_assets_MAX) * avg_asset_value, C.decimals))  ## the multiplication with the asset value garanties a cash to asset ratio of 1 in the market


def cash_long_limit(player: Player):
    if player.allowLong:
        return player.initialCash
    else:
        return 0


def assign_role_attr(player: Player, role_id):
    group = player.group
    if role_id == 'observer':
        player.participant.vars['isObserver'] = True
    elif role_id == 'trader':
        player.participant.vars['isObserver'] = False


def initiate_player(player: Player):
    group = player.group
    num_assets = literal_eval(group.numAssets)
    ## isObserver and isParticipating are set here since there is no function which assigns roles after the first round. These variables can be useful to exclude slow or inactive participants from role assignments.
    if not player.isObserver:
        initial_cash = cash_endowment(player=player)
        player.initialCash = initial_cash
        player.cashHolding = initial_cash
        player.allowLong = long_allowed(player=player)
        player.capLong = cash_long_limit(player=player)
        initial_assets = asset_endowment(player=player)
        player.initialAssets = str(initial_assets)
        assets_in_round = literal_eval(group.assetsInRound)
        for i in assets_in_round:
            num_assets[i] += initial_assets[i]
        player.assetsHolding = str(initial_assets)
        player.allowShort = short_allowed(player=player)
        player.capShort = str(asset_short_limit(player=player))
    group.numAssets = str(num_assets)


def set_player(player: Player):
    ## before this function, role_structure and within this function get_role_att is run
    assign_role_attr(player=player, role_id=player.field_maybe_none('roleID'))
    player.isObserver = player.participant.vars['isObserver']


def live_method(player: Player, data):
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
    assets_in_round = literal_eval(group.assetsInRound)
    if transactions:
        for i in assets_in_round:
            hc_data = [{'x': tx.transactionTime, 'y': tx.price, 'name': ASSET_NAMES[tx.assetID - 1]} for tx in Transaction.filter(group=group, assetID=i)]
            highcharts_series.append({'name': ASSET_NAMES[i - 1], 'data': hc_data})
    else:
        highcharts_series = []
    best_bids = literal_eval(group.field_maybe_none('bestBids'))
    best_asks = literal_eval(group.field_maybe_none('bestAsks'))
    for i in assets_in_round:
        if best_bids[i]:
            best_bid = best_bids[i]
        else:
            best_bid = None
        if best_asks[i]:
            best_ask = best_asks[i]
        else:
            best_ask = None
        BidAsks.create(# observe Bids and Asks of respective asset before the request
            group=group,
            Period=period,
            orderID=group.subsession.orderID,
            assetID=i,
            assetName=ASSET_NAMES[i - 1],
            bestBid=best_bid,
            bestAsk=best_ask,
            BATime=round(float(time.time() - player.group.marketStartTime), C.decimals),
            timing='before',
            operationType=key,
        )
    bids = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID, offer.assetID, False] for offer in offers if offer.isActive and offer.isBid], reverse=True, key=itemgetter(0))
    # to do limit amount of offers in table
    asks = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID, offer.assetID, False] for offer in offers if offer.isActive and not offer.isBid], key=itemgetter(0))
    msgs = News.filter(group=group)
    for i in assets_in_round:
        asks_asset = [[p, vol, offer_id, maker_ID, asset_ID, is_best] for p, vol, offer_id, maker_ID, asset_ID, is_best in asks if asset_ID == i]
        if asks_asset:
            best_ask = asks_asset[0][0]
        else:
            best_ask = None
        best_asks[i] = best_ask
        bids_asset = [[p, vol, offer_id, maker_ID, asset_ID, is_best] for p, vol, offer_id, maker_ID, asset_ID, is_best in bids if asset_ID == i]
        if bids_asset:
            best_bid = bids_asset[0][0]
        else:
            best_bid = None
        best_bids[i] = best_bid
        BidAsks.create(# observe Bids and Asks after the request
            group=group,
            Period=period,
            orderID=group.subsession.orderID,
            assetID=i,
            assetName=ASSET_NAMES[i - 1],
            bestBid=best_bid,
            bestAsk=best_ask,
            BATime=round(float(time.time() - player.group.marketStartTime), C.decimals),
            timing='after',
            operationType=key,
        )
    group.bestAsks = str(best_asks)
    group.bestBids = str(best_bids)
    if key == 'market_start':
        players = [player]
    return {
        p.id_in_group: dict(
            bids=bids,
            asks=asks,
            trades=sorted([[t.price, t.transactionVolume, t.transactionTime, t.sellerID, t.assetID] for t in transactions if (t.makerID == p.id_in_group or t.takerID == p.id_in_group)], reverse=True, key=itemgetter(2)),
            cashHolding=p.cashHolding,
            assetsHolding=literal_eval(p.assetsHolding),
            highcharts_series=highcharts_series,
            news=sorted([[m.msg, m.msgTime, m.playerID] for m in msgs if m.playerID == p.id_in_group], reverse=True, key=itemgetter(1)),
            bestAsks=literal_eval(group.field_maybe_none('bestAsks')),
            bestBids=literal_eval(group.field_maybe_none('bestBids')),
        )
        for p in players
    }


def calcPeriodProfits (player: Player):
    asset_values = literal_eval(player.assetValues)
    initial_assets = literal_eval(player.initialAssets)
    assets_holding = literal_eval(player.assetsHolding)
    initial_endowment = player.initialCash
    end_endowment = player.cashHolding
    assets_in_round = literal_eval(player.group.assetsInRound)
    for i in assets_in_round:
        initial_endowment += asset_values[i] * initial_assets[i]
        end_endowment += asset_values[i] * assets_holding[i]
    player.initialEndowment = initial_endowment
    player.endEndowment = end_endowment
    player.tradingProfit = end_endowment - initial_endowment
    if not player.isObserver:
        player.wealthChange = (end_endowment - initial_endowment) / initial_endowment
    else:
        player.wealthChange = 0
    player.payoff = max(C.base_payment + C.multiplier * player.wealthChange, C.min_payment_in_round)


def accumulate_orders(var, asset_id):
    a = literal_eval(var)
    a[asset_id] += 1
    return str(a)


def accumulate_volume(var, asset_id, new_volume):
    a = literal_eval(var)
    a[asset_id] += new_volume
    return str(a)


def custom_export(players):
    # Export all ExtraModels for Limits
    yield ['TableName', 'sessionID', 'offerID', 'group', 'Period', 'assetID', 'assetName', 'maker', 'price', 'limitVolume', 'isBid', 'offerID', 'orderID', 'offerTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    limits = Limit.filter()
    for l in limits:
        yield ['Limits', l.group.session.code, l.offerID, l.group.id_in_subsession, l.group.round_number, l.assetID, l.assetName, l.makerID, l.price, l.limitVolume, l.isBid, l.orderID, l.offerTime, l.remainingVolume, l.isActive, l.bestAskBefore, l.bestBidBefore, l.bestAskAfter, l.bestBidAfter]

    # Export all ExtraModels for Trades
    yield ['TableName', 'sessionID', 'transactionID', 'group', 'Period', 'assetID', 'assetName', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'orderID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    trades = Transaction.filter()
    for t in trades:
        yield ['Transactions', t.group.session.code, t.transactionID, t.group.id_in_subsession, t.group.round_number, t.assetID, t.assetName, t.makerID, t.takerID, t.price, t.transactionVolume, t.limitVolume, t.sellerID, t.buyerID, t.isBid, t.offerID, t.orderID, t.offerTime, t.transactionTime, t.remainingVolume, t.isActive, t.bestAskBefore, t.bestBidBefore, t.bestAskAfter, t.bestBidAfter]

    # Export all ExtraModels for Orders
    yield ['TableName', 'sessionID', 'orderID', 'orderType', 'group', 'Period', 'assetID', 'assetName', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'transactionID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    orders = Order.filter()
    for o in orders:
        yield ['Orders', o.group.session.code, o.orderID, o.orderType, o.group.id_in_subsession, o.group.round_number, o.assetID, o.assetName, o.makerID, o.takerID, o.price, o.transactionVolume, o.limitVolume, o.sellerID, o.buyerID, o.isBid, o.offerID, o.transactionID, o.offerTime, o.transactionTime, o.remainingVolume, o.isActive, o.bestAskBefore, o.bestBidBefore, o.bestAskAfter, o.bestBidAfter]

    # Export all ExtraModels for BidAsk
    yield ['TableName', 'sessionID', 'orderID', 'operationType', 'group', 'Period', 'assetID', 'assetName', 'bestAsk', 'bestBid', 'BATime', 'timing']
    bidasks = BidAsks.filter()
    for b in bidasks:
        yield ['BidAsks', b.group.session.code, b.orderID, b.operationType, b.group.id_in_subsession, b.group.round_number, b.assetID, b.assetName, b.bestAsk, b.bestBid, b.BATime, b.timing]

    # Export all ExtraModels for News
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
    assetID = models.IntegerField()
    assetName = models.StringField()
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
    # handle an enter message sent from the frontend to create a limit order
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
    assets_in_round = literal_eval(group.assetsInRound)
    if not (data['isBid'] >= 0 and data['limitPrice'] and data['limitVolume'] and data['assetID']):
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
    asset_id = int(data['assetID'])
    asset_name = str(ASSET_NAMES[asset_id - 1])
    if not (price > 0 and limit_volume > 0):
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            assetID=asset_id,
            assetName=asset_name,
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
            assetID=asset_id,
            assetName=asset_name,
            msg='Order rejected: insufficient cash available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    if not asset_id in assets_in_round:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            assetID=asset_id,
            assetName=asset_name,
            msg='Order rejected: misspecified asset.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    assets_holdings = literal_eval(player.assetsHolding)
    cap_shorts = literal_eval(player.capShort)
    assets_offers = literal_eval(player.assetsOffered)
    best_asks_before = literal_eval(group.field_maybe_none('bestAsks'))
    best_bids_before = literal_eval(group.field_maybe_none('bestBids'))
    assets_holding = assets_holdings[asset_id]
    cap_short = cap_shorts[asset_id]
    assets_offered = assets_offers[asset_id]
    best_ask_before = best_asks_before[asset_id]
    best_bid_before = best_bids_before[asset_id]
    if not is_bid and assets_holding + cap_short - assets_offered - limit_volume < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            assetID=asset_id,
            assetName=asset_name,
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
            assetID=asset_id,
            assetName=asset_name,
            msg='Order rejected: there is a limit order with the same or a more interesting price available in the order book.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    offer_id = player.subsession.offerID + 1
    player.subsession.offerID += 1
    # to prevent duplicates in offerID
    while len(Limit.filter(group=group, offerID=offer_id)) > 0:
        offer_id += 1
    offer_time = round(float(time.time() - player.group.marketStartTime), C.decimals)
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
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
        assetID=asset_id,
        assetName=asset_name,
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
        assetID=asset_id,
        assetName=asset_name,
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
    player.limitOrders = accumulate_orders(player.limitOrders, asset_id)
    player.limitVolume = accumulate_volume(player.limitVolume, asset_id, limit_volume)
    group.limitOrders = accumulate_orders(group.limitOrders, asset_id)
    group.limitVolume = accumulate_volume(group.limitVolume, asset_id, limit_volume)
    if is_bid:
        player.cashOffered += limit_volume * price
        player.limitBuyOrders = accumulate_orders(player.limitBuyOrders, asset_id)
        player.limitBuyVolume = accumulate_volume(player.limitBuyVolume, asset_id, limit_volume)
        group.limitBuyOrders = accumulate_orders(player.limitBuyOrders, asset_id)
        group.limitBuyVolume = accumulate_volume(group.limitBuyVolume, asset_id, limit_volume)
    else:
        assets_offers[asset_id] += limit_volume
        player.limitSellOrders = accumulate_orders(player.limitSellOrders, asset_id)
        player.limitSellVolume = accumulate_volume(player.limitSellVolume, asset_id, limit_volume)
        group.limitSellOrders = accumulate_orders(group.limitSellOrders, asset_id)
        group.limitSellVolume = accumulate_volume(group.limitSellVolume, asset_id, limit_volume)
        player.assetsOffered = str(assets_offers)


def cancel_limit(player: Player, data):
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
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
    # update Limit db entry
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
    asset_id = offers[0].assetID
    asset_name = offers[0].assetName
    if price != float(data['limitPrice']) or is_bid != bool(data['isBid'] == 1):
        print('Odd request when player', maker_id, 'cancelled an order', data)
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
        order_id += 1
    best_asks = literal_eval(group.field_maybe_none('bestAsks'))
    best_bids = literal_eval(group.field_maybe_none('bestBids'))
    best_ask_before = best_asks[asset_id]
    best_bid_before = best_bids[asset_id]
    limitoffers = Limit.filter(group=group)
    best_bid_after = max([offer.price for offer in limitoffers if offer.isActive and offer.assetID == asset_id and offer.isBid] or [-1])
    best_ask_after = min([offer.price for offer in limitoffers if offer.isActive and offer.assetID == asset_id and not offer.isBid] or [-1])
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
        assetID=asset_id,
        assetName=asset_name,
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
    player.cancellations = accumulate_orders(player.cancellations, asset_id)
    player.cancelledVolume = accumulate_volume(player.cancelledVolume, asset_id, remaining_volume)
    group.cancellations = accumulate_orders(group.cancellations, asset_id)
    group.cancelledVolume = accumulate_volume(group.cancelledVolume, asset_id, remaining_volume)
    if is_bid:
        player.cashOffered -= remaining_volume * price
    else:
        player.assetsOffered = accumulate_volume(player.assetsOffered, asset_id, -remaining_volume)


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
    assetID = models.IntegerField()
    assetName = models.StringField()
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
    assetID = models.IntegerField()
    assetName = models.StringField()
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
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
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
    asset_id = int(limit_entry.assetID)
    asset_name = str(limit_entry.assetName)
    if not (price > 0 and transaction_volume > 0): # check whether data is valid
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            assetID=asset_id,
            assetName=asset_name,
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
            assetID=asset_id,
            assetName=asset_name,
            msg='Order rejected: insufficient cash available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    assets_holdings = literal_eval(player.assetsHolding)
    cap_shorts = literal_eval(player.capShort)
    assets_offers = literal_eval(player.assetsOffered)
    best_asks_before = literal_eval(group.field_maybe_none('bestAsks'))
    best_bids_before = literal_eval(group.field_maybe_none('bestBids'))
    assets_holding = assets_holdings[asset_id]
    cap_short = cap_shorts[asset_id]
    assets_offered = assets_offers[asset_id]
    best_ask_before = best_asks_before[asset_id]
    best_bid_before = best_bids_before[asset_id]
    if is_bid and assets_holding + cap_short - assets_offered - transaction_volume < 0:
        News.create(
            player=player,
            playerID=taker_id,
            group=group,
            Period=period,
            assetID=asset_id,
            assetName=asset_name,
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
            assetID=asset_id,
            assetName=asset_name,
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
            assetID=asset_id,
            assetName=asset_name,
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
        maker.limitBuyOrderTransactions = accumulate_orders(maker.limitBuyOrderTransactions, asset_id)
        maker.limitBuyVolumeTransacted = accumulate_volume(maker.limitBuyVolumeTransacted, asset_id, transaction_volume)
        player.marketSellOrders = accumulate_orders(player.marketSellOrders, asset_id)
        player.marketSellVolume = accumulate_volume(player.marketSellVolume, asset_id, transaction_volume)
        group.marketSellOrders = accumulate_orders(group.marketSellOrders, asset_id)
        group.marketSellVolume = accumulate_volume(group.marketSellVolume, asset_id, transaction_volume)
        seller_id = player.id_in_group
        buyer_id = maker.id_in_group
    else:
        [buyer, seller] = [player, maker]
        maker.assetsOffered = accumulate_volume(maker.assetsOffered, asset_id, -transaction_volume)  # undo offer holdings
        maker.limitSellOrderTransactions = accumulate_orders(maker.limitSellOrderTransactions, asset_id)
        maker.limitSellVolumeTransacted = accumulate_volume(maker.limitSellVolumeTransacted, asset_id, transaction_volume)
        player.marketBuyOrders = accumulate_orders(player.marketBuyOrders, asset_id)
        player.marketBuyVolume = accumulate_volume(player.marketBuyVolume, asset_id, transaction_volume)
        group.marketBuyOrders = accumulate_orders(group.marketBuyOrders, asset_id)
        group.marketBuyVolume = accumulate_volume(group.marketBuyVolume, asset_id, transaction_volume)
        seller_id = maker.id_in_group
        buyer_id = seller.id_in_group
    transaction_id = player.subsession.transactionID + 1
    player.subsession.transactionID += 1
    # to prevent duplicates in orderID
    while len(Transaction.filter(group=group, offerID=transaction_id)) > 0:
        transaction_id += 1
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
        order_id += 1
    transaction_time = round(float(time.time() - group.marketStartTime), C.decimals)
    limit_entry.transactedVolume += transaction_volume
    limit_entry.isActive = is_active
    transacted_volume = limit_entry.transactedVolume
    limit_entry.remainingVolume -= transaction_volume
    buyer.cashHolding -= transaction_volume * price
    seller.cashHolding += transaction_volume * price
    buyer.transactions = accumulate_orders(buyer.transactions, asset_id)
    buyer.transactedVolume = accumulate_volume(buyer.transactedVolume, asset_id, transaction_volume)
    buyer.assetsHolding = accumulate_volume(buyer.assetsHolding, asset_id, transaction_volume)
    seller.transactions = accumulate_orders(seller.transactions, asset_id)
    seller.transactedVolume = accumulate_volume(seller.transactedVolume, asset_id, transaction_volume)
    seller.assetsHolding = accumulate_volume(seller.assetsHolding, asset_id, -transaction_volume)
    maker.limitOrderTransactions = accumulate_orders(maker.limitOrderTransactions, asset_id)
    maker.limitVolumeTransacted = accumulate_volume(maker.limitVolumeTransacted, asset_id, transaction_volume)
    player.marketOrders = accumulate_orders(player.marketOrders, asset_id)
    player.marketOrderVolume = accumulate_volume(player.marketOrderVolume, asset_id, transaction_volume)
    group.transactions = accumulate_orders(group.transactions, asset_id)
    group.transactedVolume = accumulate_volume(group.transactedVolume, asset_id, transaction_volume)
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
        assetID=asset_id,
        assetName=asset_name,
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
        assetID=asset_id,
        assetName=asset_name,
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
    assetID = models.IntegerField()
    assetName = models.StringField()
    msg = models.StringField()
    msgTime = models.FloatField()


class BidAsks(ExtraModel):
    group = models.Link(Group)
    Period = models.IntegerField()
    assetID = models.IntegerField()
    assetName = models.StringField()
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


class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.randomisedTypes = random_types(group=group)
        initiate_group(group=group)
        players = group.get_players()
        for p in players:
            set_player(player=p)
            p.assetValues = group.assetValues
            initiate_player(player=p)


class PreMarket(Page):
    @staticmethod
    def js_vars(player: Player):
        group = player.group
        return dict(
            allowShort=player.allowShort,
            capShort=literal_eval(player.capShort),
            capLong=player.capLong,
            cashHolding=player.cashHolding,
            assetsHolding=literal_eval(player.assetsHolding),
            numAssetsInRound=group.numAssetsInRound,
            assetNames=ASSET_NAMES,
            assetNamesInRound=literal_eval(group.assetNamesInRound),
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
            allowShort=player.allowShort,
            capShort=literal_eval(player.capShort),
            capLong=player.capLong,  # round(player.capLong, 2)
            cashHolding=player.cashHolding,
            assetsHolding=literal_eval(player.assetsHolding),
            numAssetsInRound=group.numAssetsInRound,
            assetNames=ASSET_NAMES,
            assetNamesInRound=literal_eval(group.assetNamesInRound),
            assetsInRound=literal_eval(group.assetsInRound),
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
            calcPeriodProfits(player=p)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            initialEndowment=round(player.initialEndowment, C.decimals),
            endEndowment=round(player.endEndowment, C.decimals),
            tradingProfit=round(player.tradingProfit, C.decimals),
            wealthChange=round(player.wealthChange*100, C.decimals),
            payoff=cu(round(player.payoff, C.decimals)),
        )

    @staticmethod
    def js_vars(player: Player):
        group = player.group
        return dict(
            cashHolding=player.cashHolding,
            assetsHolding=literal_eval(player.assetsHolding),
            numAssetsInRound=group.numAssetsInRound,
            assetNamesInRound=literal_eval(group.assetNamesInRound),
            assetValues=literal_eval(player.assetValues)
        )


class FinalResults(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payoff=cu(round(player.participant.payoff / C.NUM_ROUNDS, 0)),
            periodPayoff=[round(p.payoff, C.decimals) for p in player.in_all_rounds()],
            tradingProfit=[round(p.tradingProfit, C.decimals) for p in player.in_all_rounds()],
            wealthChange=[round(p.wealthChange, C.decimals) for p in player.in_all_rounds()],
        )



page_sequence = [Instructions, WaitToStart, PreMarket, WaitingMarket, Market, ResultsWaitPage, Results, FinalResults, ResultsWaitPage]
