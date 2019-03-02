"""adds AlpacaAccount table

Revision ID: 37173e276aa3
Revises: 3d4f4f9bf703
Create Date: 2019-04-26 17:09:30.308049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37173e276aa3'
down_revision = '3d4f4f9bf703'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alpaca_account',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('buying_power', sa.Float(), nullable=True),
    sa.Column('cash', sa.Float(), nullable=True),
    sa.Column('cash_withdrawable', sa.Float(), nullable=True),
    sa.Column('portfolio_value', sa.Float(), nullable=True),
    sa.Column('pattern_day_trader', sa.Boolean(), nullable=True),
    sa.Column('trading_blocked', sa.Boolean(), nullable=True),
    sa.Column('transfers_blocked', sa.Boolean(), nullable=True),
    sa.Column('account_blocked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alpaca_account_id'), 'alpaca_account', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_alpaca_account_id'), table_name='alpaca_account')
    op.drop_table('alpaca_account')
    # ### end Alembic commands ###