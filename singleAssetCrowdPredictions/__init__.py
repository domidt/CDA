from otree.api import *
import time
import random
from operator import itemgetter
from ast import literal_eval

doc = """Continuous double auction market"""

COINS = [1, .2, .05, .01]


class C(BaseConstants):
    NAME_IN_URL = 'crowdCDA'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 4
    base_payment = cu(25)
    multiplier = 90
    min_payment_in_round = cu(0)
    min_payment = cu(4)
    FV_MIN = 30
    FV_MAX = 85
    num_assets_MIN = 20
    num_assets_MAX = 35
    cash_MIN = 20*100
    cash_MAX = 35*100
    decimals = 2
    marketTime = 210
    allowLong = True
    allowShort = True


class Subsession(BaseSubsession):
    offerID = models.IntegerField(initial=0)
    orderID = models.IntegerField(initial=0)
    transactionID = models.IntegerField(initial=0)


def vars_for_admin_report(subsession):
    groups = subsession.get_groups()
    period = subsession.round_number
    payoffs = sorted([p.payoff for p in subsession.get_players()])
    marketTimes = sorted([g.marketTime for g in groups])
    trades = [[tx.transactionTime, tx.price] for tx in Transaction.filter() if tx.Period == period]
    bids = [[bx.BATime, bx.bestBid] for bx in BidAsks.filter() if bx.Period == period]
    bids = ['null' if b[1] is None else b for b in bids]
    asks = [[ax.BATime, ax.bestAsk] for ax in BidAsks.filter() if ax.Period == period]
    asks = ['null' if a[1] is None else a for a in asks]
    return dict(
        marketTimes=marketTimes,
        payoffs=payoffs,
        trades=trades,
        bids=bids,
        asks=asks,
    )


class Group(BaseGroup):
    marketTime = models.FloatField(initial=C.marketTime)
    marketStartTime = models.FloatField()
    marketEndTime = models.FloatField()
    randomisedTypes = models.BooleanField()
    numAssets = models.IntegerField()
    assetNames = models.LongStringField()
    infoStructure = models.LongStringField()
    assetValue = models.FloatField()
    bestAsk = models.FloatField()
    bestBid = models.FloatField()
    players_in_group = models.IntegerField()
    roleList = models.LongStringField()
    roleStructure = models.LongStringField()
    numTraders = models.IntegerField()
    numInformed = models.IntegerField()
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
    return group.session.config['randomise_types']


def num_informed(group: Group):
    return group.session.config['num_informed_traders']


def num_traders(group: Group):
    return group.session.config['num_traders']


def role_structure(group: Group):
    group.roleList = str(['I3', 'I2', 'I1', 'I0', 'inactive'])
    group.players_in_group = len(group.get_players())
    group.numTraders = num_traders(group=group)
    num_I3 = group.session.config['num_I3_traders']  # informed about 1E, 20c, and 5c
    num_I2 = group.session.config['num_I2_traders']  # informed about 1E, 20c
    num_I1 = group.session.config['num_I1_traders']  # informed about 1E
    num_I0 = group.numTraders - num_I3 - num_I2 - num_I1  # uninformed traders
    num_1E_coins = group.session.config['num_1E_coins']
    num_20c_coins = group.session.config['num_20c_coins']
    num_5c_coins = group.session.config['num_5c_coins']
    num_1c_coins = group.session.config['num_1c_coins']
    group.infoStructure = str({1: num_1E_coins, .2: num_20c_coins, .05: num_5c_coins, .01: num_1c_coins})
    group.roleStructure = str({'period': group.round_number, 'inactive': 0, 'I0': num_I0, 'I1': num_I1, 'I2': num_I2, 'I3': num_I3})


def asset_value(group: Group):
    infoStructure = literal_eval(group.infoStructure)
    values = [infoStructure[c] for c in COINS]
    total_value = 0
    for i in range(len(COINS)):
        total_value += values[i] * COINS[i]
    return total_value


def assign_types(group: Group):
    # this method allocates traders' types at the beginning of the session or when randomised.
    players = group.get_players()
    role_list = literal_eval(group.roleList)
    if group.randomisedTypes or Subsession.round_number == 1:
        ii = group.numTraders  # number of traders without type yet
        for r in role_list:  # for each role
            print(r)
            k = 0  # number of players assigned this role
            max_k = literal_eval(group.roleStructure)[r]  # number of players to be assigned with this role
            while k < max_k:  # until enough role 'r' types are assigned
                rand_num = round(random.uniform(a=0, b=1) * ii, 0)
                print('rand', rand_num)
                i = 0
                for p in players:
                    if i < rand_num and not p.field_maybe_none('roleID'):
                        i += 1
                        print('i', i)
                        if rand_num == i:
                            ii -= 1
                            print('assignment', r)
                            p.roleID = str(r)
                            k += 1
                            print('k', k, max_k)
    for p in players:
        p.allowShort = short_allowed(player=p)
        p.allowLong = long_allowed(player=p)
        p.information = str(get_role_attr(player=p, roleID=p.roleID))
        p.isActive = p.participant.vars['isActive']
        p.informed = p.participant.vars['informed']


def define_asset_value(group: Group):
    ## this method describes the BBV structure of an experiment and shares the information in the players table.
    group.assetValue = asset_value(group=group)


def allocate_endowments(group: Group):
    players = group.get_players()
    for p in players:
        initialCash = cash_endowment(player=p)
        p.initialCash = initialCash
        p.cashHolding = initialCash
        p.capLong = cash_long_limit(player=p)
        initialAssets = asset_endowment(player=p)
        p.initialAssets = initialAssets
        p.assetsHolding = initialAssets
        p.capShort = asset_short_limit(player=p)


def get_max_time(group: Group):
    return group.session.config['market_time']


class Player(BasePlayer):
    informed = models.BooleanField(choices=((True, 'informed'), (False, 'uninformed')))
    isActive = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    roleID = models.StringField()
    information = models.LongStringField()
    allowShort = models.BooleanField()
    allowLong = models.BooleanField()
    assetValue = models.FloatField()
    initialCash = models.FloatField(initial=0, decimal=C.decimals)
    initialAssets = models.IntegerField()
    initialEndowment = models.FloatField(initial=0, decimal=C.decimals)
    cashHolding = models.FloatField(initial=0, decimal=C.decimals)
    assetsHolding = models.IntegerField()
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


def asset_endowment(player: Player):
    return int(random.uniform(a=C.num_assets_MIN, b=C.num_assets_MAX))


def short_allowed(player: Player):
    return C.allowShort


def long_allowed(player: Player):
    return C.allowLong


def asset_short_limit(player: Player):
    if player.allowShort:
        return player.initialAssets
    else:
        return 0


def cash_endowment(player: Player):
    return float(round(random.uniform(a=C.cash_MIN, b=C.cash_MAX), C.decimals))


def cash_long_limit(player: Player):
    if player.allowLong:
        return player.initialCash
    else:
        return 0


def get_role_attr(player: Player, roleID):
    group = player.group
    info = {c: None for c in COINS}
    if roleID == 'inactive':
        player.participant.vars['isActive'] = False
        player.participant.vars['informed'] = False
    elif roleID == 'I0':
        player.participant.vars['isActive'] = True
        player.participant.vars['informed'] = False
    elif roleID == 'I1' or roleID == 'I2' or roleID == 'I3':
        player.participant.vars['isActive'] = True
        player.participant.vars['informed'] = True
        if roleID == 'I1':
            info[1] = literal_eval(group.infoStructure)[1]
        elif roleID == 'I2':
            for i in [1,.2]:
                info[i] = literal_eval(group.infoStructure)[i]
        elif roleID == 'I3':
            for i in [1,.2,.05]:
                info[i] = literal_eval(group.infoStructure)[i]
    return info


def live_method(player: Player, data):
    print(data)
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
        highcharts_series = [[tx.transactionTime, tx.price] for tx in Transaction.filter(group=group)]
    else:
        highcharts_series = []
    best_bid = group.field_maybe_none('bestBid')
    best_ask = group.field_maybe_none('bestAsk')
    BidAsks.create(# observe Bids and Asks of respective asset before the request
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
    print('bids', bids)
    # to do limit amount of offers in table
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
    BidAsks.create(# observe Bids and Asks after the request
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
    return {
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


def calcPeriodProfits (player: Player):
    initial_endowment = player.initialCash + player.assetValue * player.initialAssets
    end_endowment = player.cashHolding + player.assetValue * player.assetsHolding
    player.initialEndowment = initial_endowment
    player.endEndowment = end_endowment
    player.tradingProfit = end_endowment - initial_endowment
    player.wealthChange = (end_endowment - initial_endowment) / initial_endowment
    player.payoff = max(C.base_payment + C.multiplier * player.wealthChange, C.min_payment_in_round)


def custom_export(players):
    # Export all ExtraModels for Limits
    yield ['TableName', 'sessionID', 'offerID', 'group', 'Period', 'maker', 'price', 'limitVolume', 'isBid', 'offerID', 'orderID', 'offerTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    limits = Limit.filter()
    for l in limits:
        yield ['Limits', l.group.session.code, l.offerID, l.group.id_in_subsession, l.group.round_number, l.makerID, l.price, l.limitVolume, l.isBid, l.orderID, l.offerTime, l.remainingVolume, l.isActive, l.bestAskBefore, l.bestBidBefore, l.bestAskAfter, l.bestBidAfter]

    # Export all ExtraModels for Trades
    yield ['TableName', 'sessionID', 'transactionID', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'orderID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    trades = Transaction.filter()
    for t in trades:
        yield ['Transactions', t.group.session.code, t.transactionID, t.group.id_in_subsession, t.group.round_number, t.makerID, t.takerID, t.price, t.transactionVolume, t.limitVolume, t.sellerID, t.buyerID, t.isBid, t.offerID, t.orderID, t.offerTime, t.transactionTime, t.remainingVolume, t.isActive, t.bestAskBefore, t.bestBidBefore, t.bestAskAfter, t.bestBidAfter]

    # Export all ExtraModels for Orders
    yield ['TableName', 'sessionID', 'orderID', 'orderType', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'transactionID', 'offerTime', 'transactionTime', 'remainingVolume', 'isActive', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    orders = Order.filter()
    for o in orders:
        yield ['Orders', o.group.session.code, o.orderID, o.orderType, o.group.id_in_subsession, o.group.round_number, o.makerID, o.takerID, o.price, o.transactionVolume, o.limitVolume, o.sellerID, o.buyerID, o.isBid, o.offerID, o.transactionID, o.offerTime, o.transactionTime, o.remainingVolume, o.isActive, o.bestAskBefore, o.bestBidBefore, o.bestAskAfter, o.bestBidAfter]

    # Export all ExtraModels for BidAsk
    yield ['TableName', 'sessionID', 'orderID', 'operationType', 'group', 'Period', 'bestAsk', 'bestBid', 'BATime', 'timing']
    bidasks = BidAsks.filter()
    for b in bidasks:
        yield ['BidAsks', b.group.session.code, b.orderID, b.operationType, b.group.id_in_subsession, b.group.round_number, b.bestAsk, b.bestBid, b.BATime, b.timing]

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
    if not (data['isBid'] >= 0 and data['limitPrice'] and data['limitVolume']):
        print('Player', player.id_in_group, 'placed an odd limit order', data)
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
        print('Player', maker_id, 'placed an odd order', data)
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
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
    maker_id = int(data['makerID'])
    group = player.group
    period = group.round_number
    if maker_id != player.id_in_group:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: you can cancel your own orders only.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    offer_id = int(data['offerID'])
    # update Limit db entry
    offers = [o for o in Limit.filter(group=group) if o.offerID == offer_id]
    if not offers or len(offers) != 1:
        print('Error: too few or too many limits found while cancelling.')
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
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
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
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
    offer_id = int(data['offerID'])
    taker_id = player.id_in_group
    group = player.group
    period = group.round_number
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
        print('Player', taker_id, 'tried to accept via an odd order', data)
        News.create(
            player=player,
            playerID=maker_id,
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
            playerID=maker_id,
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
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient assets available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    elif maker_id == taker_id:
        News.create(
            player=player,
            playerID=maker_id,
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
    # to prevent duplicates in orderID
    while len(Transaction.filter(group=group, offerID=transaction_id)) > 0:
        transaction_id += + 1
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
        order_id += + 1
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
class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.randomisedTypes = random_types(group=group)
        role_structure(group=group)
        define_asset_value(group=group)
        players = group.get_players()
        for p in players:
            p.assetValue = group.assetValue
        assign_types(group=group)
        allocate_endowments(group=group)


class PreMarket(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            isActive=player.isActive,
            initialCash=player.initialCash,
            initialAssets=player.initialAssets,
            allowShort=player.allowShort,
            capShort=player.capShort,
            capLong=player.capLong,
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            id_in_group=player.id_in_group,
            informed=player.informed,
            information=literal_eval(player.information),
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
    def vars_for_template(player: Player):
        return dict(
            allowShort=player.allowShort,
            capShort=player.capShort,
            capLong=player.capLong,  # round(player.capLong, 2)
            cashHolding=player.cashHolding,
            assetsHolding=player.assetsHolding,
        )


    @staticmethod
    def js_vars(player: Player):
        return dict(
            id_in_group=player.id_in_group,
            informed=player.informed,
            information=literal_eval(player.information),
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
            assetValue=player.assetValue,
            initialEndowment=round(player.initialEndowment, C.decimals),
            endEndowment=round(player.endEndowment, C.decimals),
            tradingProfit=round(player.tradingProfit, C.decimals),
            wealthChange=round(player.wealthChange*100, C.decimals),
            payoff=round(player.payoff, C.decimals),
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            assetValue=player.assetValue,
        )


class FinalResults(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payoff=round(player.participant.payoff / C.NUM_ROUNDS, 0),
            periodPayoff=[round(p.payoff, C.decimals) for p in player.in_all_rounds()],
            tradingProfit=[round(p.tradingProfit, C.decimals) for p in player.in_all_rounds()],
            wealthChange=[round(p.wealthChange, C.decimals) for p in player.in_all_rounds()],

        )



page_sequence = [WaitToStart, PreMarket, WaitingMarket, Market, ResultsWaitPage, Results, FinalResults, ResultsWaitPage]
