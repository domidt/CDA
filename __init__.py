from otree.api import *
import time
import random
from operator import itemgetter
import websockets

doc = """Continuous double auction market"""

ASSET_NAMES = 'A'
# the name of the only asset when in single-asset mode


class C(BaseConstants):
    NAME_IN_URL = 'CDA_app'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 12
    base_payment = cu(25)
    multiplier = 90
    min_payment_in_round = cu(0)
    min_payment = cu(4)
    FV_MIN = 30
    FV_MAX = 85
    MarketTime = 210
    decimals = 2


class Subsession(BaseSubsession):
    offerID = models.IntegerField(initial=0)
    orderID = models.IntegerField(initial=0)
    transactionID = models.IntegerField(initial=0)


def vars_for_admin_report(subsession):
    groups = subsession.get_groups()
    period = subsession.round_number
    payoffs = sorted([p.payoff for p in subsession.get_players()])
    trades = [[tx.transactionTime, tx.price] for tx in Transaction.filter() if tx.Period == period]
    bids = [[bx.BATime, bx.bestBid] for bx in BidAsks.filter() if bx.Period == period]
    bids = ['null' if b[1] is None else b for b in bids]
    asks = [[ax.BATime, ax.bestAsk] for ax in BidAsks.filter() if ax.Period == period]
    asks = ['null' if a[1] is None else a for a in asks]
    return dict(
        payoffs=payoffs,
        trades=trades,
        bids=bids,
        asks=asks,
    )


class Group(BaseGroup):
    marketStartTime = models.FloatField()
    marketEndTime = models.FloatField()
    assetValue = models.FloatField(decimal=C.decimals)
    bestAsk = models.FloatField(initial=None, decimal=C.decimals)
    bestBid = models.FloatField(initial=None, decimal=C.decimals)
    MarketTime = models.IntegerField()


def num_players(group: Group):
    return 2


def num_informed(group: Group):
    return 1


def num_traders(group: Group):
    return num_players(group=group)


def asset_value(group: Group):
    # this method describes the BBV structure of an experiment.
    # If defined, it should return an array of values for each asset.
    group.assetValue = round(random.uniform(a=C.FV_MIN, b=C.FV_MAX), C.decimals)
    players = group.get_players()
    for p in players:
        p.assetValue = group.assetValue


def assign_types(group: Group):
    players = group.get_players()
    # this method describes traders characteristics like asymmetric information
    i = 0
    j = 0
    NUM_informed = num_informed(group=group)
    NUM_traders = num_traders(group=group)
    NUM_players = num_players(group=group)
    for p in players:
        if i < NUM_informed and (random.uniform(a=0, b=1) * NUM_traders) < NUM_informed or j == NUM_traders - NUM_informed:
            p.active = True
            p.informed = True
            p.information = get_information(player=p)
            i += 1
        elif j < NUM_traders and (random.uniform(a=0, b=1) * NUM_players) < NUM_traders:
            p.active = True
            p.informed = False
            p.information = 'no information'
            j += 1
        else:
            p.active = False
            p.informed = False
            p.information = 'no information'
        p.allowShort = allow_short(player=p)


def allocate_endowments(group: Group):
    players = group.get_players()
    for p in players:
        initialCash = cash_endowment(player=p)
        p.initialCash = initialCash
        p.cashHolding = initialCash
        initialAssets = asset_endowment(player=p)
        p.initialAssets = initialAssets
        p.assetsHolding = initialAssets
        p.capLong = cash_short_limit(player=p)
        p.capShort = asset_short_limit(player=p)


def get_max_time(group: Group):
    return C.MarketTime


class Player(BasePlayer):
    informed = models.BooleanField(choices=((True, 'informed'), (False, 'uninformed')))
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    information = models.StringField()
    allowShort = models.BooleanField()
    assetValue = models.FloatField(decimal=C.decimals)
    initialCash = models.FloatField(initial=0, decimal=C.decimals)
    initialAssets = models.IntegerField()
    initialEndowment = models.FloatField(initial=0, decimal=C.decimals)
    cashHolding = models.FloatField(initial=0, decimal=C.decimals)
    assetsHolding = models.IntegerField(initial=0)
    endEndowment = models.FloatField(initial=0, decimal=C.decimals)
    capLong = models.FloatField(initial=0, min=0, decimal=C.decimals)
    capShort = models.IntegerField(initial=0, min=0)
    limitVolume = models.IntegerField(initial=0, min=0)
    limitVolumeEntry = models.IntegerField(initial=0, min=0)
    transactedVolume = models.IntegerField(initial=0, min=0)
    cancelledVolume = models.IntegerField(initial=0, min=0)
    cashOffered = models.FloatField(initial=0, min=0, decimal=C.decimals)
    assetsOffered = models.IntegerField(initial=0)
    tradingProfit = models.FloatField(initial=0)
    wealthChange = models.FloatField(initial=0)


def asset_endowment(player: Player):
    return 20


def allow_short(player: Player):
    return True


def asset_short_limit(player: Player):
    group = player.group
    short_allowed = player.allowShort
    if short_allowed:
        return asset_endowment(player=player)
    else:
        return 0


def cash_endowment(player: Player):
    return 2000


def cash_short_limit(player: Player):
    group = player.group
    short_allowed = player.allowShort
    if short_allowed:
        return cash_endowment(player=player)
    else:
        return 0


def get_information(player: Player):
    info = str(player.assetValue)
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
    BidAsks.create(# observe Bids and Asks before the request
        group=group,
        Period=period,
        orderID=group.subsession.orderID,
        bestBid=group.field_maybe_none('bestBid'),
        bestAsk=group.field_maybe_none('bestAsk'),
        BATime=round(float(time.time() - player.group.marketStartTime), C.decimals),
        timing='before',
        operationType=key,
    )
    bids = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID] for offer in offers if offer.active and offer.isBid], reverse=True, key=itemgetter(0))
    # to do limit amount of offers in table
    asks = sorted([[offer.price, offer.remainingVolume, offer.offerID, offer.makerID] for offer in offers if offer.active and not offer.isBid], key=itemgetter(0))
    msgs = News.filter(group=group)
    if asks:
        group.bestAsk = asks[0][0]
        # best_ask = [asks[0]]
        asks = asks
    else:
        group.bestAsk = None
    if bids:
        group.bestBid = bids[0][0]
        # best_bid = [bids[0]]
        bids = bids
    else:
        group.bestBid = None
    BidAsks.create(# observe Bids and Asks after the request
        group=group,
        Period=period,
        orderID=group.subsession.orderID,
        bestBid=group.field_maybe_none('bestBid'),
        bestAsk=group.field_maybe_none('bestAsk'),
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
    yield ['TableName', 'sessionID', 'offerID', 'group', 'Period', 'maker', 'price', 'limitVolume', 'isBid', 'offerID', 'orderID', 'offerTime', 'remainingVolume', 'active', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    limits = Limit.filter()
    for l in limits:
        yield ['Limits', l.group.session.code, l.offerID, l.group.id_in_subsession, l.group.round_number, l.makerID, l.price, l.limitVolume, l.isBid, l.orderID, l.offerTime, l.remainingVolume, l.active, l.bestAskBefore, l.bestBidBefore, l.bestAskAfter, l.bestBidAfter]

    # Export all ExtraModels for Trades
    yield ['TableName', 'sessionID', 'transactionID', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'orderID', 'offerTime', 'transactionTime', 'remainingVolume', 'active', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    trades = Transaction.filter()
    for t in trades:
        yield ['Transactions', t.group.session.code, t.transactionID, t.group.id_in_subsession, t.group.round_number, t.makerID, t.takerID, t.price, t.transactionVolume, t.limitVolume, t.sellerID, t.buyerID, t.isBid, t.offerID, t.orderID, t.offerTime, t.transactionTime, t.remainingVolume, t.active, t.bestAskBefore, t.bestBidBefore, t.bestAskAfter, t.bestBidAfter]

    # Export all ExtraModels for Orders
    yield ['TableName', 'sessionID', 'orderID', 'orderType', 'group', 'Period', 'maker', 'taker', 'price', 'transactionVolume', 'limitVolume', 'sellerID', 'buyerID', 'isBid', 'offerID', 'transactionID', 'offerTime', 'transactionTime', 'remainingVolume', 'active', 'bestAskBefore', 'bestBidBefore', 'bestAskAfter', 'bestBidAfter']
    orders = Order.filter()
    for o in orders:
        yield ['Orders', o.group.session.code, o.orderID, o.orderType, o.group.id_in_subsession, o.group.round_number, o.makerID, o.takerID, o.price, o.transactionVolume, o.limitVolume, o.sellerID, o.buyerID, o.isBid, o.offerID, o.transactionID, o.offerTime, o.transactionTime, o.remainingVolume, o.active, o.bestAskBefore, o.bestBidBefore, o.bestAskAfter, o.bestBidAfter]

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
    # asset_name = models.StringField()
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
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
    bestBidBefore = models.FloatField()
    bestAskBefore = models.FloatField()
    bestAskAfter = models.FloatField()
    bestBidAfter = models.FloatField()


def limit_order(player: Player, data):
    # handle an enter message sent from the frontend to create a limit order
    maker_id = player.id_in_group
    # asset_name = limitdata['asset_name']
    price = round(float(data['limitPrice']), C.decimals)
    is_bid = bool(data['isBid'] == 1)
    limit_volume = int(data['limitVolume'])
    group = player.group
    period = group.round_number
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
    elif is_bid and player.cashHolding + player.capLong - player.cashOffered - limit_volume * price < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient cash available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    # elif is_bid == 'ask' and player.assetsHolding[asset_name] + player.capShort[asset_name] - player.assetsOffered[asset_name] - limit_volume < 0:
    elif not is_bid and player.assetsHolding + player.capShort - player.assetsOffered - limit_volume < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient assets available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    elif (is_bid and group.field_maybe_none('bestAsk') is not None and price > group.bestAsk) or (not is_bid and group.field_maybe_none('bestBid') is not None and price < group.bestBid):
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
        offer_id = offer_id + 1
    offer_time = round(float(time.time() - player.group.marketStartTime), C.decimals)
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
        order_id = order_id + 1
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    if(best_ask_before):
        best_ask_after = best_ask_before
    else:
        best_ask_before = -1
        best_ask_after = -1
    if(best_bid_before):
        best_bid_after = best_bid_before
    else:
        best_bid_before = -1
        best_bid_after = -1
    if(is_bid and (best_bid_before == -1 or price >= best_bid_before)):
        best_bid_after = price
    elif(not is_bid and (best_ask_before == -1 or price <= best_ask_before)):
        best_ask_after = price
    Limit.create(
        offerID=offer_id,
        orderID=order_id,
        makerID=maker_id,
        group=group,
        Period=period,
        # asset_name=asset_name,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=0,
        remainingVolume=limit_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        offerTime=offer_time,
        active=True,
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
        # asset_name=asset_name,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=0,
        remainingVolume=limit_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='limitOrder',
        offerTime=offer_time,
        orderTime=offer_time,
        active=True,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    player.limitVolume += limit_volume
    if is_bid:
        player.cashOffered += limit_volume * price
    else:
        player.assetsOffered += limit_volume


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
    offers[0].active = False
    is_bid = offers[0].isBid
    # asset_name = data['asset_name']
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
        order_id = order_id + 1
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    limitoffers = Limit.filter(group=group)
    best_bid_after = max([offer.price for offer in limitoffers if offer.active and offer.isBid] or [-1])
    best_ask_after = min([offer.price for offer in limitoffers if offer.active and not offer.isBid] or [-1])
    if(not best_ask_before):
        best_ask_before = -1
    if(not best_bid_before):
        best_bid_before = -1
    Order.create(
        orderID=order_id,
        offerID=offer_id,
        makerID=maker_id,
        group=group,
        Period=period,
        # asset_name=asset_name,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=transacted_volume,
        remainingVolume=0,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='cancelLimitOrder',
        offerTime=offer_time,
        orderTime=float(time.time() - player.group.marketStartTime),
        active=False,
        bestAskBefore=best_ask_before,
        bestBidBefore=best_bid_before,
        bestAskAfter=best_ask_after,
        bestBidAfter=best_bid_after,
    )
    player.cancelledVolume += remaining_volume
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
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
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
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))
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
    # asset_name = limit.asset_name
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
    active = limit_entry.active
    if transaction_volume >= remaining_volume:
        transaction_volume = remaining_volume
        active = False
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
    # elif is_bid == 'ask' and player.assetsHolding[asset_name] + player.capShort[asset_name] - player.assetsOffered[asset_name] - limit_volume < 0:
    elif is_bid and player.assetsHolding + player.capShort - player.assetsOffered - transaction_volume < 0:
        News.create(
            player=player,
            playerID=maker_id,
            group=group,
            Period=period,
            msg='Order rejected: insufficient assets available.',
            msgTime=round(float(time.time() - player.group.marketStartTime), C.decimals)
        )
        return
    # elif is_bid == 'bid' and player.assetsHolding[asset_name] + player.capShort[asset_name] - player.assetsOffered[
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
    offer_time = round(float(limit_entry.offerTime), 2)
    players = group.get_players()
    maker = [p for p in players if p.id_in_group == maker_id][0]
    if is_bid:
        [buyer, seller] = [maker, player]
        # maker.assetsOffered[asset_name] -= transaction_volume # undo offer holdings
        maker.cashOffered -= transaction_volume * price
        seller_id = player.id_in_group
        buyer_id = maker.id_in_group
    else:
        [buyer, seller] = [player, maker]
        maker.assetsOffered -= transaction_volume  # undo offer holdings
        seller_id = maker.id_in_group
        buyer_id = seller.id_in_group
    transaction_id = player.subsession.transactionID + 1
    player.subsession.transactionID += 1
    # to prevent duplicates in orderID
    while len(Transaction.filter(group=group, offerID=transaction_id)) > 0:
        transaction_id = transaction_id + 1
    order_id = player.subsession.orderID + 1
    player.subsession.orderID += 1
    # to prevent duplicates in orderID
    while len(Order.filter(group=group, offerID=order_id)) > 0:
        order_id = order_id + 1
    transaction_time = round(float(time.time() - group.marketStartTime), C.decimals)
    limit_entry.transactedVolume += transaction_volume
    limit_entry.active = active
    transacted_volume = limit_entry.transactedVolume
    limit_entry.remainingVolume -= transaction_volume
    buyer.transactedVolume += transaction_volume
    buyer.assetsHolding += transaction_volume
    buyer.cashHolding -= transaction_volume * price
    seller.transactedVolume += transaction_volume
    seller.cashHolding += transaction_volume * price
    seller.assetsHolding -= transaction_volume
    best_ask_before = group.field_maybe_none('bestAsk')
    best_bid_before = group.field_maybe_none('bestBid')
    limitOffers = Limit.filter(group=group)
    best_bid_after = max([offer.price for offer in limitOffers if offer.active and offer.isBid] or [-1])
    best_ask_after = min([offer.price for offer in limitOffers if offer.active and not offer.isBid] or [-1])
    if(not best_ask_before):
        best_ask_before = -1
    if(not best_bid_before):
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
        # asset_name=asset_name,
        price=price,
        transactionVolume=transaction_volume,
        remainingVolume=remaining_volume - transaction_volume,
        amount=transaction_volume * price,
        isBid=is_bid,
        transactionTime=transaction_time,
        offerTime=offer_time,
        active=active,
        bestAskBefore = best_ask_before,
        bestBidBefore = best_bid_before,
        bestAskAfter = best_ask_after,
        bestBidAfter = best_bid_after,
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
        # asset_name=asset_name,
        limitVolume=limit_volume,
        price=price,
        transactedVolume=transacted_volume,
        remainingVolume=remaining_volume - transaction_volume,
        amount=limit_volume * price,
        isBid=is_bid,
        orderType='marketOrder',
        orderTime=transaction_time,
        offerTime=offer_time,
        active=active,
        bestAskBefore = best_ask_before,
        bestBidBefore = best_bid_before,
        bestAskAfter = best_ask_after,
        bestBidAfter = best_bid_after,
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
        asset_value(group=group)
        assign_types(group=group)
        allocate_endowments(group=group)


class PreMarket(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            information=player.information,
            active=player.active,
            assetValue=round(player.assetValue, C.decimals),
            initialCash=round(player.initialCash, C.decimals),
            initialAssets=round(player.initialAssets, C.decimals),
            initialEndowment=round(player.initialEndowment, C.decimals),
        )


class WaitingMarket(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.marketStartTime = round(float(time.time()), C.decimals)
        group.MarketTime = get_max_time(group=group)


class Market(Page):
    live_method = live_method
    timeout_seconds = C.MarketTime

    @staticmethod
    def js_vars(player: Player):
        return dict(id_in_group=player.id_in_group,
                    informed=player.informed,
                    information=player.information,
                    allowShort=player.allowShort,
                    capShort=player.capShort,
                    capLong=player.capLong.__round__(C.decimals),  # round(player.capLong, 2)
                    assetValue=player.assetValue.__round__(C.decimals),
                    cashHolding=player.cashHolding.__round__(C.decimals),
                    assetsHolding=player.assetsHolding.__round__(C.decimals))

    @staticmethod
    def get_timeout_seconds(player: Player):
        group = player.group
        return group.marketStartTime + C.MarketTime - time.time()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        calcPeriodProfits(player=player)


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            assetValue=round(player.assetValue, C.decimals),
            initialEndowment=round(player.initialEndowment, C.decimals),
            endEndowment=round(player.endEndowment, C.decimals),
            tradingProfit=round(player.tradingProfit, C.decimals),
            wealthChange=round(player.wealthChange*100, C.decimals),
            payoff=round(player.payoff, C.decimals),
        )


class FinalResults(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payoff=round(player.participant.payoff / C.NUM_ROUNDS, 0),
            periodPayoff=round(player.in_all_rounds().payoff, C.decimals),
            tradingProfit=round(player.in_all_rounds().tradingProfit, C.decimals),
            wealthChange=round(player.in_all_rounds().wealthChange * 100, C.decimals),

        )



page_sequence = [WaitToStart, PreMarket, WaitingMarket, Market, ResultsWaitPage, Results, FinalResults, ResultsWaitPage]
