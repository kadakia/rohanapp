"""users table

Revision ID: b9473399aece
Revises: ded0a8ceeb69
Create Date: 2025-01-03 21:18:58.684155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9473399aece'
down_revision = 'ded0a8ceeb69'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('body',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=140),
               existing_nullable=True)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=256),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)

    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('body',
               existing_type=sa.String(length=140),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)

    # ### end Alembic commands ###
