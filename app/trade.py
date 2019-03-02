from app import app, db
from app.models import Comment, Mention, Transaction, Holding, AlpacaAccount

from dotenv import load_dotenv
from datetime import datetime, timezone
import dateutil.parser
import os

import numpy
import alpaca_trade_api as tradeapi

from sqlalchemy import func
from collections import Counter

import operator
from pprint import pprint

from datetime import datetime
import time

from rq import Queue
from worker import conn
#NEED TO UPDATE
#from run import run_inverse_wsb

q = Queue(connection=conn)

APP_ROOT = os.path.join(os.path.dirname(__file__), '../..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

api = tradeapi.REST(os.getenv('ALPACA_KEY_ID'), os.getenv('ALPACA_SECRET_KEY'), base_url="https://paper-api.alpaca.markets")
conn = tradeapi.stream2.StreamConn(key_id = os.getenv('ALPACA_KEY_ID'), secret_key = os.getenv('ALPACA_SECRET_KEY'), base_url="https://paper-api.alpaca.markets")

def getPrice(symbol):
    barset = api.get_barset(symbol, 'minute', limit = 1)
    bars = barset[symbol]
    price = bars[0].c
    
    return price
   
def rebalancePortfolio():
    if api.get_clock().is_open:
        changes = []
        total_neg_sentiment = 0
        portfolio = api.list_positions()
        portfolio_symbols = list(p.symbol for p in portfolio)
        app.logger.info("Portfolio:")
        app.logger.info(portfolio_symbols)
        #mentions = Mention.query.all()
#        all_symbols = set(list(m.symbol for m in Mention.query.all()))
#        neg_mentions = []
#        for s in all_symbols:
#            mentions = Mention.query.filter_by(symbol=s).order_by(Mention.created_at.desc()).all()
#            for mention in mentions:
#                if mention.avg_sentiment < 0:
#                #total_neg_sentiment += m.avg_sentiment
#                    neg_mentions.append(mention)
#        all_neg_symbols = list(m.symbol for m in neg_mentions)
        neg_mentions = Mention.query.filter(Mention.avg_sentiment < 0).all()
        neg_symbols = list(m.symbol for m in neg_mentions)
        neg_counter = Counter(neg_symbols).most_common(10)
        top_ten_neg_symbols = list(x[0] for x in neg_counter)
        app.logger.info("Top Ten Bearish Stocks:")
        app.logger.info(top_ten_neg_symbols)
        for s in portfolio_symbols:
            if s not in top_ten_neg_symbols:
                #SELL
                app.logger.info("%s no longer in top 10 bearish stocks; attempting to sell" % (s))
                try:
                    order = api.submit_order(
                        symbol=s,
                        qty=portfolio[portfolio_symbols.index(s)].qty,
                        side="sell",
                        type='market',
                        time_in_force='gtc'
                        #client_order_id="".join(["wsb",str(random.randint(1,1000))])
                    )
                    createTransactionRecord(order)
                    time.sleep(5)
                except Exception as e:
                    app.logger.info("attempting to %s %d shares of %s for $%.2f" % (order["side"], order["qty"], order["symbol"], float(order["qty"] * getPrice(order["symbol"]))))
                    app.logger.info(e)

        #only want to return latest mention for each symbol
        #deduped = Mention.query.with_entities(Mention.symbol, func.count(Mention.symbol)).group_by(Mention.symbol).all()
#        final_mentions = []
#        for s in top_ten_neg_symbols:
#            mention = Mention.query.filter_by(symbol=s).order_by(Mention.created_at.desc()).first()
#            final_mentions.append(mention)
            #if mention.avg_sentiment < 0:
            #total_neg_sentiment += mention.avg_sentiment         
#        for result in deduped:
#            mention = Mention.query.filter_by(symbol=result[0]).order_by(Mention.created_at.desc()).first()
#            final_mentions.append(mention)
#            if mention.avg_sentiment < 0:
#                total_neg_sentiment += mention.avg_sentiment
        total_mentions = 0
        stocks = []
        for symbol in neg_counter:
            total_mentions += symbol[1]
        for symbol in neg_counter:
            stocks.append({'symbol' : symbol[0], 'weighting': symbol[1]/total_mentions})
        for stock in stocks:
            weighting = stock['weighting']
            symbol = stock['symbol']
            app.logger.info("%s:" % (symbol))
            app.logger.info("Weighting: %.2f" % (weighting))
            if symbol in portfolio_symbols: 
                new_qty = int((float(api.get_account().portfolio_value) * weighting)/float(portfolio[portfolio_symbols.index(symbol)].current_price))
                app.logger.info("New qty: %s" % (new_qty))
                current_qty = int(portfolio[portfolio_symbols.index(symbol)].qty)
                app.logger.info("Current qty: %s" % (current_qty))
                change_qty = new_qty - current_qty
                if change_qty > 0:
                    changes.append({"symbol" : symbol, "side" : "buy", "qty" : change_qty})
                elif change_qty < 0:
                    change_qty = abs(change_qty)
                    changes.append({"symbol" : symbol, "side" : "sell", "qty" : change_qty})
            else:
                app.logger.info("%s not currently in portfolio" % (symbol))
                try:
                    new_quantity = int((float(api.get_account().portfolio_value) * weighting)/getPrice(symbol))
                    if new_quantity > 0:
                        changes.append({"symbol" : symbol, "side" : "buy", "qty" : new_quantity})
                except Exception as e:
                    app.logger.info(e)
                    app.logger.info("unable to get price for %s" % (symbol))
                    pass
        #forcing 'sell' orders to be submitted first
        sorted_changes = sorted(changes, key=operator.itemgetter('side'), reverse=True)
        for change in sorted_changes:
            #if change["qty"] > 0:
            try:
                order = api.submit_order(
                    symbol=change["symbol"],
                    qty=change["qty"],
                    side=change["side"],
                    type='market',
                    time_in_force='gtc'
                    #client_order_id="".join(["wsb",str(random.randint(1,1000))])
                )
                if change["side"] == "sell":
                #BIG UGLY HACK in order to make sure that the sell orders have gone through so we have enough buying power for the buy orders
                    time.sleep(5)
                createTransactionRecord(order)
            except Exception as e:
                app.logger.info("attempting to %s %d shares of %s for $%.2f" % (change["side"], change["qty"], change["symbol"], float(change["qty"] * getPrice(change["symbol"]))))
                app.logger.info(e)
                app.logger.info("need: $%.2f" % (float(getPrice(change["symbol"])) * float(change["qty"])))
                app.logger.info("have: $%.2f" % (float(api.get_account().buying_power)))
                #ANOTHER HACK to get rebalancing to work
                revised_qty = int(float(api.get_account().buying_power)/float(getPrice(change["symbol"])) * 0.90 )
                try:
                    time.sleep(5)
                    order = api.submit_order(
                        symbol=change["symbol"],
                        qty=change["qty"],
                        side=change["side"],
                        type='market',
                        time_in_force='gtc'
                        #client_order_id="".join(["wsb",str(random.randint(1,1000))])
                    )
                    createTransactionRecord(order)
                except Exception as e:
                    app.logger.info("attempting to %s %d shares of %s for $%.2f" % (change["side"], change["qty"], change["symbol"], float(change["qty"] * getPrice(change["symbol"]))))
                    app.logger.info(e)
                    app.logger.info("need: $%.2f" % (float(getPrice(change["symbol"])) * float(change["qty"])))
                    app.logger.info("have: $%.2f" % (float(api.get_account().buying_power)))

        time.sleep(5)
        getPortfolio()
        getAlpacaAccount()
            
def getOrderUpdates():
    @conn.on(r'trade_updates')
    async def on_msg(conn, channel, data):
        # Print the update to the console.
        #print(channel)
        app.logger.debug(data)
        if data.event == 'new':
            try:
                createTransactionRecord(data.order)
            except Exception as e:
                app.logger.warn(e)
        elif data.event == 'fill':
            try:
                updateTransaction(data.order)
            except Exception as e:
                app.logger.warn(e)

    # Start listening for updates.
    conn.run(['trade_updates'])
    
#def getAccountUpdates():
#    @conn.on(r'account_updates')
#    async def on_msg(conn, channel, data):
#        # Print the update to the console.
#        pprint(data)
#        #print("Update for account. Cash balance: {}".format(data['cash']))
#        updateAccount(data)
#
#    # Start listening for updates.
#    conn.run(['account_updates'])
    
def updateAlpacaAccount(data):
    accounts = AlpacaAccount.query.all()
    if len(accounts) > 0:
        account = accounts[0]
        account.updated_at = data["updated_at"]
        account.status = data["status"]
        account.currency = data["currency"]
        account.cash = data["cash"]
        account.cash_withdrawable = data["cash_withdrawable"]
    else:
        account = AlpacaAccount(id = data["id"],
                          updated_at = data["updated_at"],
                          status = data["status"],
                          currency = data["currency"],
                          cash = data["cash"],
                          cash_withdrawable = data["cash_withdrawable"]
                          )
    db.session.add(account)
    db.session.commit()
    
def getAlpacaAccount():
    alpacaAccount = api.get_account()
    accounts = AlpacaAccount.query.all()
    if len(accounts) > 0:
        account = accounts[0]
        account.status = alpacaAccount.status
        account.cash = alpacaAccount.cash
        account.cash_withdrawable = alpacaAccount.cash_withdrawable
        account.currency = alpacaAccount.currency
        account.buying_power = alpacaAccount.buying_power
        account.portfolio_value = alpacaAccount.portfolio_value
        account.pattern_day_trader = alpacaAccount.pattern_day_trader
        account.trading_blocked = alpacaAccount.trading_blocked
        account.transfers_blocked = alpacaAccount.transfers_blocked
        account.account_blocked = alpacaAccount.account_blocked
    else:
        account = AlpacaAccount(id = alpacaAccount.id,
                                #updated_at = alpacaAccount.updated_at,
                                created_at = alpacaAccount.created_at,
                                status = alpacaAccount.status,
                                cash = alpacaAccount.cash,
                                cash_withdrawable = alpacaAccount.cash_withdrawable,
                                currency = alpacaAccount.currency,
                                buying_power = alpacaAccount.buying_power,
                                portfolio_value = alpacaAccount.portfolio_value,
                                pattern_day_trader = alpacaAccount.pattern_day_trader,
                                trading_blocked = alpacaAccount.trading_blocked,
                                transfers_blocked = alpacaAccount.transfers_blocked,
                                account_blocked = alpacaAccount.account_blocked
                              )
    db.session.add(account)
    db.session.commit()

def createTransactionRecord(order):
    tx = Transaction(alpaca_id = order.id,
                     symbol = order.symbol,
                     created_at = order.created_at,
                     qty = order.qty,
                     filled_qty = order.filled_qty,
                     side = order.side,
                     type = order.type,
                     time_in_force = order.time_in_force,
                     status = order.status,
                     #'2019-04-12T19:25:08.494Z'
                     filled_at = order.filled_at,
                     filled_avg_price = order.filled_avg_price,                   
                     )
    db.session.add(tx)
    db.session.commit()
    
def updateTransaction(order):
    tx = Transaction.query.filter_by(alpaca_id=order["id"]).first()
    tx.status = order["status"]
    tx.filled_qty = order["filled_qty"]
    tx.filled_at = dateutil.parser.parse(order["filled_at"])
    tx.filled_avg_price = order["filled_avg_price"]
    db.session.add(tx)
    db.session.commit()
    
def getPortfolio():
    portfolio = api.list_positions()
    portfolio_symbols = list(p.symbol for p in portfolio)
    current_holdings = Holding.query.all()
    for holding in current_holdings:
        if holding.symbol not in portfolio_symbols:
            holding.qty = 0
            holding.market_value = 0
            holding.avg_entry_price = 0
            holding.cost_basis = 0
            holding.unrealized_pl = 0
            holding.unrealized_plpc = 0
            holding.unrealized_intraday_pl = 0
            holding.unrealized_intraday_plpc = 0
            holding.current_price = 0
            holding.lastday_price = 0
            holding.change_today = 0
            holding.status = "closed"
    for position in portfolio:
        holding = Holding.query.filter_by(symbol=position.symbol).first()
        if holding is not None:
            holding.qty = position.qty
            holding.market_value = position.market_value
            holding.avg_entry_price = position.avg_entry_price
            holding.cost_basis = position.cost_basis
            holding.unrealized_pl = position.unrealized_pl
            holding.unrealized_plpc = position.unrealized_plpc
            holding.unrealized_intraday_pl = position.unrealized_intraday_pl
            holding.unrealized_intraday_plpc = position.unrealized_intraday_plpc
            holding.current_price = position.current_price
            holding.lastday_price = position.lastday_price
            holding.change_today = position.change_today
            holding.status = "open"
        else:
            holding = Holding(
                symbol = position.symbol,
                qty = position.qty,
                market_value = position.market_value,
                avg_entry_price = position.avg_entry_price,
                cost_basis = position.cost_basis,
                unrealized_pl = position.unrealized_pl,
                unrealized_plpc = position.unrealized_plpc,
                unrealized_intraday_pl = position.unrealized_intraday_pl,
                unrealized_intraday_plpc = position.unrealized_intraday_plpc,
                current_price = position.current_price,
                lastday_price = position.lastday_price,
                change_today = position.change_today,
                status = "open"
                )
        db.session.add(holding)
        db.session.commit()    