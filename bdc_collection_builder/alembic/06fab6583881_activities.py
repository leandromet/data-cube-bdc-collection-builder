"""activities

Revision ID: 06fab6583881
Revises: 
Create Date: 2020-08-26 18:32:58.022855

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '06fab6583881'
down_revision = None
branch_labels = ('bdc_collection_builder',)
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.Column('activity_type', sa.String(length=64), nullable=False),
    sa.Column('args', sa.JSON(), nullable=True),
    sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('scene_type', sa.String(), nullable=True),
    sa.Column('sceneid', sa.String(length=64), nullable=False),
    sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['bdc.collections.id'], name=op.f('activities_collection_id_collections_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('activities_pkey')),
    schema='collection_builder'
    )
    op.create_table('activity_history',
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('start', sa.DateTime(), nullable=True),
    sa.Column('env', sa.JSON(), nullable=True),
    sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['activity_id'], ['collection_builder.activities.id'], name=op.f('activity_history_activity_id_activities_fkey')),
    sa.ForeignKeyConstraint(['task_id'], ['collection_builder.celery_taskmeta.id'], name=op.f('activity_history_task_id_celery_taskmeta_fkey')),
    sa.PrimaryKeyConstraint('activity_id', 'task_id', name=op.f('activity_history_pkey')),
    schema='collection_builder'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('activity_history', schema='collection_builder')
    op.drop_table('activities', schema='collection_builder')
    # ### end Alembic commands ###
