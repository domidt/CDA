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
    NUM_ROUNDS = 1
    base_payment = cu(4)
    FV_MIN = 30
    FV_MAX = 85
    MarketTime = 210


class Subsession(BaseSubsession):
    offerID = models.IntegerField(initial=1)
    orderID = models.IntegerField(initial=1)
    transactionID = models.IntegerField(initial=1)


def creating_session(subsession: Subsession):
    players = subsession.get_players()
    groups = subsession.get_groups()
    # this method describes traders characteristics like asymmetric information
    for g in groups:
        i = 1
        j = 1
        NUM_informed = num_informed(group=g)
        NUM_players = num_players(group=g)
        g.assetValue = asset_value(fv_min=C.FV_MIN, fv_max=C.FV_MAX)
        for p in players:
            if i < NUM_informed and round(random.uniform(a=0, b=1) * 10) < 3 or j == NUM_players - NUM_informed:
                p.informed = True
                i += 1
            else:
                p.informed = False
                j += 1
            initialCash = cash_endowment(player=p)
            p.initialCash = initialCash
            p.cashHolding = initialCash
            initialAssets = asset_endowment(player=p)
            p.initialAssets = initialAssets
            p.assetsHolding = initialAssets
            p.capLong = cash_short_limit(player=p)
            p.capShort = asset_short_limit(player=p)
        live_method({'operationType': 'start_market'})


class Group(BaseGroup):
    marketStartTime = models.IntegerField()
    marketEndTime = models.IntegerField()
    allowShort = models.BooleanField()
    assetValue = models.CurrencyField()

def num_players(group: Group):
    return 2

def num_informed(group: Group):
    return 3


def allow_short(group: Group):
    return True


def asset_value(fv_min, fv_max):
    # this method describes the BBV structure of an experiment.
    # If defined, it should return an array of values for each asset.
    return random.uniform(a=fv_min, b=fv_max)


class Player(BasePlayer):
    informed = models.BooleanField(choices=((True, 'informed'), (False, 'uninformed')))
    initialCash = models.CurrencyField()
    initialAssets = models.IntegerField()
    initialEndowment = models.CurrencyField()
    cashHolding = models.CurrencyField()
    assetsHolding = models.IntegerField()
    capLong = models.CurrencyField()
    capShort = models.IntegerField()
    limitVolume = models.IntegerField(initial=0)
    transactedVolume = models.IntegerField(initial=0)
    cancelledVolume = models.IntegerField(initial=0)
    cashOffered = models.CurrencyField(initial=0)
    assetsOffered = models.IntegerField(initial=0)
    wealthChange = models.FloatField()


def asset_endowment(player: Player):
    return 20


def asset_short_limit(player: Player):
    group = player.group
    if allow_short(group=group):
        return asset_endowment(player=player)
    else:
        return 0


def cash_endowment(player: Player):
    return 2000


def cash_short_limit(player: Player):
    group = player.group
    if allow_short(group=group):
        return cash_endowment(player=player)
    else:
        return 0



def live_method(player: Player, data):
    if not data or 'operationType' not in data:
        return
    key = data['operationType']
    highcharts_series = []
    group = player.group
    players = group.get_players()
    if key == 'market_start':
        return {
            p.id_in_group: dict(
                cashHolding=p.cashHolding,
                assetsHolding=p.assetsHolding,
                highcharts_series=highcharts_series,
            )
            for p in players
        }
    if key == 'limit_order':
        limit_order(player, data)
    elif key == 'cancel_limit':
        cancel_limit(player, data)
    elif key == 'transaction':
        transaction(player, data)
        highcharts_series = [[tx.transactionTime, tx.price] for tx in Transaction.filter(group=group)]
    offers = Limit.filter(group=group)
    transactions = Transaction.filter(group=group)
    bids = sorted([[offer.price, offer.remainingVolume, offer.offerID] for offer in offers if offer.active and offer.isBid], reverse=True, key=itemgetter(0))
    # to do limit amount of offers in table
    asks = sorted([[offer.price, offer.remainingVolume, offer.offerID] for offer in offers if offer.active and not offer.isBid], key=itemgetter(0))
    print(bids)
    return {
        p.id_in_group: dict(
            bids=bids,
            asks=asks,
            trades=sorted([t.transactionTime for t in transactions if (t.makerID == p or t.takerID == p)]),
            cashHolding=p.cashHolding,
            assetsHolding=p.assetsHolding,
            highcharts_series=highcharts_series,
        )
        for p in players
    }


class Limit(ExtraModel):
    offerID = models.IntegerField()
    makerID = models.IntegerField()
    # asset_name = models.StringField()
    group = models.Link(Group)
    limitVolume = models.IntegerField()
    price = models.CurrencyField()
    transactedVolume = models.IntegerField()
    remainingVolume = models.IntegerField()
    amount = models.CurrencyField()
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    offerTime = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))


def limit_order(player: Player, data):
    # handle an enter message sent from the frontend to create a limit order
    maker_id = player.id_in_group
    # asset_name = limitdata['asset_name']
    price = float(data['price'])
    is_bid = data['isBid']
    limit_volume = int(data['limitVolume'])
    if is_bid and player.cashHolding + player.capLong - player.cashOffered - limit_volume * price < 0:
        return {maker_id: 'Order rejected: insufficient available cash.'}
    # elif is_bid == 'ask' and player.assetHolding[asset_name] + player.capShort[asset_name] - player.assetsOffered[asset_name] - limit_volume < 0:
    elif not is_bid and player.assetsHolding + player.capShort - player.assetsOffered - limit_volume < 0:
        return {maker_id: 'Order rejected: insufficient available assets.'}
    else:
        group = player.group
        player.subsession.offerID += 1
        offer_id = player.subsession.offerID
        # to prevent dublicates in offerID
        while len(Limit.filter(group=group, offerID=offer_id)) > 0:
            player.subsession.offerID = offer_id + 1
            offer_id = player.subsession.offerID
        offer_time = int(time.time() - player.group.marketStartTime)
        Limit.create(
            offerID=offer_id,
            makerID=maker_id,
            group=group,
            # asset_name=asset_name,
            limitVolume=limit_volume,
            price=price,
            transactedVolume=0,
            remainingVolume=limit_volume,
            amount=limit_volume * price,
            isBid=is_bid,
            offerTime=offer_time,
            active=True,
        )
        player.subsession.orderID += 1
        order_id = player.subsession.orderID
        Order.create(
            orderID=order_id,
            offerID=offer_id,
            makerID=maker_id,
            group=group,
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
        )
        player.limitVolume += limit_volume
        if is_bid:
            player.assetsOffered += limit_volume
        else:
            player.cashOffered += limit_volume * price


def cancel_limit(player: Player, data):
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
    maker_id = data['makerID']
    if maker_id != player.id_in_group:
        return {player.id_in_group: 'Order rejected: others orders cannot be cancelled.'}
    else:
        offer_id = data['offerID']
        is_bid = data['isBid']
        # asset_name = data['asset_name']
        limit_volume = data['limitVolume']
        remaining_volume = data['remainingVolume']
        price = data['price']
        transacted_volume = data['transactedVolume']
        offer_time = data['offerTime']
        group = player.group
        # update Limit db entry
        offers = [o for o in Limit.filter(group=group) if o.offerID == offer_id]
        if not offers or len(offers) != 1:
            print('Error: too few or too many limits found while cancelling.')
            return
        offers[0].active = False
        Subsession.orderID += 1
        order_id = Subsession.orderID
        Order.create(
            orderID=order_id,
            offerID=offer_id,
            makerID=maker_id,
            group=group,
            # asset_name=asset_name,
            limitVolume=limit_volume,
            price=price,
            transactedVolume=transacted_volume,
            remainingVolume=0,
            amount=limit_volume * price,
            isBid=is_bid,
            orderType='cancelLimitOrder',
            offerTime=offer_time,
            orderTime=int(time.time() - player.group.marketStartTime),
            active=False,
        )
        player.cancelledVolume += remaining_volume
        if is_bid == 'bid':
            player.assetsOffered -= remaining_volume
        else:
            player.cashOffered -= remaining_volume * price


class Order(ExtraModel):
    orderID = models.IntegerField()
    offerID = models.IntegerField()
    transactionID = models.IntegerField()
    makerID = models.IntegerField()
    takerID = models.IntegerField()
    sellerID = models.IntegerField()
    buyerID = models.IntegerField()
    group = models.Link(Group)
    limitVolume = models.IntegerField()
    transactionVolume = models.IntegerField()
    transactedVolume = models.IntegerField()
    remainingVolume = models.IntegerField()
    price = models.CurrencyField()
    amount = models.CurrencyField()
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    orderType = models.StringField()
    orderTime = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")
    offerTime = models.IntegerField()
    transactionTime = models.IntegerField()
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))


class Transaction(ExtraModel):
    transactionID = models.IntegerField()
    offerID = models.IntegerField()
    orderID = models.IntegerField()
    makerID = models.IntegerField()
    takerID = models.IntegerField()
    sellerID = models.IntegerField()
    buyerID = models.IntegerField()
    group = models.Link(Group)
    transactionVolume = models.IntegerField()
    limitVolume = models.IntegerField()
    price = models.CurrencyField()
    amount = models.CurrencyField()
    isBid = models.BooleanField(choices=((True, 'Bid'), (False, 'Ask')))
    offerTime = models.IntegerField()
    transactionTime = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")
    active = models.BooleanField(choices=((True, 'active'), (False, 'inactive')))


def transaction(player: Player, data):
    if 'offerID' not in data:
        return
    # handle an enter message sent from the frontend to cancel a limit order
    offer_id = data['offerID']
    taker_id = player.id_in_group
    is_bid = data['isBid']
    price = data['price']
    # asset_name = limit.asset_name
    limit_entry = Limit.filter(group=group, offerID=offer_id)
    if len(limit_entry) > 1:
        print('Limit entry is not well-defined: multiple entries with the same ID')
    transaction_volume = data['transaction_volume']
    remaining_volume = limit_entry.remainingVolume
    price_offer = limit_entry.price
    if price != price_offer:
        print('mismatch of prices in limit order and market order')
    active = limit_entry.active
    if transaction_volume > limit_volume - remaining_volume:
        transaction_volume = remaining_volume
        active = 0
    else:
        transaction_volume = transaction_volume
    if not is_bid and player.cashHolding + player.capLong - player.cashOffered - limit_volume * price < 0:
        return {taker_id: 'Order rejected: insufficient available cash.'}
    # elif is_bid == 'bid' and player.assetHolding[asset_name] + player.capShort[asset_name] - player.assetsOffered[
    elif is_bid and player.assetsHolding + player.capShort - player.assetsOffered - limit_volume < 0:
        return {taker_id: 'Order rejected: insufficient available assets.'}
    elif maker_id == taker_id:
        return {taker_id: 'Order rejected: own limit orders cannot be transacted.'}
    else:
        group = player.group
        offer_id = limit.offerID
        offer_time = limit.offerTime
        players = group.get_players()
        maker = [p for p in players if p.id_in_group == maker_id]
        if is_bid:
            [buyer, seller] = [maker, player]
            # maker.assetsOffered[asset_name] -= transaction_volume # undo offer holdings
            maker.assetsOffered -= transaction_volume  # undo offer holdings
            seller_id = player.id_in_group
            buyer_id = maker.id_in_group
        else:
            [buyer, seller] = [player, maker]
            maker.cashOffered -= transaction_volume * price
            seller_id = maker.id_in_group
            buyer_id = seller.id_in_group
        Subsession.transactionID += 1
        transaction_id = Subsession.transactionID
        Subsession.orderID += 1
        order_id = Subsession.orderID
        transaction_time = int(time.time() - group.marketStartTime)
        limit.transactedVolume += transaction_volume
        transacted_volume = limit.transactedVolume
        limit.remainingVolume -= transaction_volume
        buyer.transactedVolume += transaction_volume
        buyer.assetHolding += transaction_volume
        buyer.cashHolding -= transaction_volume * price
        seller.transactedVolume += transaction_volume
        seller.cashHolding += transaction_volume * price
        seller.assetHolding -= transaction_volume
        Transaction.create(
            transactionID=transaction_id,
            offerID=offer_id,
            orderID=order_id,
            makerID=maker_id,
            takerID=taker_id,
            sellerID=seller_id,
            buyerID=buyer_id,
            # asset_name=asset_name,
            price=price,
            transactionVolume=transaction_volume,
            remainingVolume=remaining_volume - transaction_volume,
            amount=transaction_volume * price,
            isBid=is_bid,
            transactionTime=transaction_time,
            offerTime=offer_time,
            active=active,
        )
        Order.create(
            orderID=order_id,
            offerID=offer_id,
            transactionID=transaction_id,
            group=group,
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
        )


# PAGES
class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.marketStartTime = int(time.time())


class Market(Page):
    limit_order = limit_order
    cancel_limit = cancel_limit
    transaction = transaction
    live_method = live_method

    @staticmethod
    def js_vars(player: Player):
        return dict(id_in_group=player.id_in_group, informed=player.informed)

    @staticmethod
    def get_timeout_seconds(player: Player):
        group = player.group
        return group.marketStartTime + C.MarketTime - time.time()


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    pass


page_sequence = [WaitToStart, Market, ResultsWaitPage, Results]
