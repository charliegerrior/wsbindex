from app import app, db
from app.models import Comment, Mention, Transaction, Holding

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Comment': Comment, 'Mention': Mention, 'Transaction': Transaction, 'Holding': Holding}