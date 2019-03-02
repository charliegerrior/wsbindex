from app import db
from datetime import datetime

class AlpacaAccount(db.Model):
    id = db.Column(db.String(50), primary_key=True, index=True)
    status = db.Column(db.String(50))
    currency = db.Column(db.String(3))
    buying_power = db.Column(db.Float)
    cash = db.Column(db.Float)
    cash_withdrawable = db.Column(db.Float)
    portfolio_value = db.Column(db.Float)
    pattern_day_trader = db.Column(db.Boolean)
    trading_blocked = db.Column(db.Boolean)
    transfers_blocked = db.Column(db.Boolean)
    account_blocked = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    
class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(8), index=True)
    qty = db.Column(db.Integer)
    avg_entry_price = db.Column(db.Float)
    market_value = db.Column(db.Float)
    cost_basis = db.Column(db.Float)
    unrealized_pl = db.Column(db.Float)
    unrealized_plpc = db.Column(db.Float)
    unrealized_intraday_pl = db.Column(db.Float)
    unrealized_intraday_plpc = db.Column(db.Float)
    current_price = db.Column(db.Float)
    lastday_price = db.Column(db.Float)
    change_today = db.Column(db.Float)
    status = db.Column(db.String(10), index=True)
    mentions = db.relationship('Mention', lazy='dynamic')
    transactions = db.relationship('Transaction', lazy='dynamic')

    def __repr__(self):
      return '<Holding {}>'.format(self.symbol)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alpaca_id = db.Column(db.String(50), index=True)
    symbol = db.Column(db.String(8), db.ForeignKey('holding.symbol'))
    qty = db.Column(db.Integer)
    filled_qty = db.Column(db.Integer)
    side = db.Column(db.String(4))
    type = db.Column(db.String(20))
    time_in_force = db.Column(db.String(3))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    filled_at = db.Column(db.DateTime, index=True)
    filled_avg_price = db.Column(db.Float)

    def __repr__(self):
      return '<Transaction {}>'.format(self.id)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reddit_id = db.Column(db.String(7), unique=True)
    reddit_link = db.Column(db.String(100), unique=True)
    author = db.Column(db.String(23))
    body = db.Column(db.Text, index=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    mention =  db.relationship('Mention', backref='comment', lazy='dynamic')
    #mentions = db.relationship('Mention', lazy='dynamic')

    def __repr__(self):
        return '<Comment {}>'.format(self.body)
    
class Mention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.String(7), db.ForeignKey('comment.id'))
    symbol = db.Column(db.String(8), db.ForeignKey('holding.symbol'))
    sentiment = db.Column(db.Float)
    avg_sentiment = db.Column(db.Float)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    def __repr__(self):
        return '<Mention {}>'.format(self.symbol)
