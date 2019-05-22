from flask import render_template, current_app
from app import db
from app.models import Holding, Transaction, Mention, Comment, AlpacaAccount
from datetime import datetime
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    holdings = Holding.query.filter_by(status="open")
    account = AlpacaAccount.query.all()[0]
    portfolio_market_value = 0
    todays_gainpc = 0
    for holding in holdings:
        portfolio_market_value += holding.market_value
    for holding in holdings:
        todays_gainpc += (holding.unrealized_intraday_plpc * holding.market_value/portfolio_market_value)
    recent_mentions = db.session.query(Mention).order_by(Mention.created_at.desc()).limit(5)
    recent_transactions = db.session.query(Transaction).order_by(Transaction.created_at.desc()).limit(5)
    
    return render_template('index.html', title='Home', holdings = holdings, mentions = recent_mentions, transactions = recent_transactions, value = portfolio_market_value, gains = todays_gainpc, account = account)

@bp.route('/about')
def about():
    return render_template('about.html', title='About')

@bp.route('/legal')
def legal():
    return render_template('legal.html', title='Legal')

@bp.route('/holdings/<symbol>')
def holding(symbol):
    holding = Holding.query.filter_by(symbol=symbol).first_or_404()
    #holding = {'symbol': symbol, 'shares': 100, 'market_value' : '$1234.56'}
    #transactions = [{'symbol': 'MSFT', 'quantity': 789, 'side' : 'buy', 'change': '-$5,432.10', type: 'market', 'created_at': datetime.utcnow(), 'time_in_force' : 'opg', 'status': 'closed', 'mention_id' : 1},
                    #{'symbol': 'MSFT', 'quantity': 1348, 'side' : 'sell', 'change': '$566,789.99', type: 'market', 'created_at': datetime.utcnow(), 'time_in_force' : 'opg', 'status': 'closed', 'mention_id' : 23}
                    #]
    transactions = holding.transactions.all()[::-1]
    mentions = holding.mentions.all()[::-1]
    return render_template('holding.html', holding = holding, transactions = transactions, mentions = mentions)

@bp.route('/transactions/<id>')
def transaction(id):
    #holding = Holding.query.filter_by(symbol=symbol).first_or_404()
    #transaction = {'symbol': 'MSFT', 'quantity': 789, 'side' : 'buy', 'change': '-$5,432.10', type: 'market', 'created_at': datetime.utcnow(), 'time_in_force' : 'opg', 'status': 'closed', 'mention_id' : 1}
    #transactions = []
    #mentions = []
    transaction = Transaction.query.filter_by(id=id).first_or_404()
    return render_template('transaction.html', transaction = transaction)

@bp.route('/mentions/<id>')
def mention(id):
    #holding = Holding.query.filter_by(symbol=symbol).first_or_404()
    #mention = {'symbol': 'MSFT', 'sentiment': -0.563, 'avg_sentiment' : -0.921, 'created_at' : datetime.utcnow() }
    #mention = Mention.query.get(id)
    mention = Mention.query.filter_by(id=id).first_or_404()
    comment = Comment.query.filter_by(id=mention.comment_id).first_or_404()
    #transactions = []
    #mentions = []
    return render_template('mention.html', mention = mention, comment = comment)