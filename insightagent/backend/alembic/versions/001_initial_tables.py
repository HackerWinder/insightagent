"""Initial database tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建任务状态枚举类型
    task_status_enum = postgresql.ENUM(
        'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 
        name='taskstatus'
    )
    task_status_enum.create(op.get_bind())
    
    # 创建日志级别枚举类型
    log_level_enum = postgresql.ENUM(
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 
        name='loglevel'
    )
    log_level_enum.create(op.get_bind())

    # 创建tasks表
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('status', task_status_enum, nullable=False, default='QUEUED'),
        sa.Column('progress', sa.Float, default=0.0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    
    # 创建索引
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])

    # 创建task_logs表
    op.create_table(
        'task_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('level', log_level_enum, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('step', sa.String(255), nullable=True),
    )
    
    # 创建索引
    op.create_index('ix_task_logs_task_id', 'task_logs', ['task_id'])
    op.create_index('ix_task_logs_timestamp', 'task_logs', ['timestamp'])

    # 创建raw_data表
    op.create_table(
        'raw_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    
    # 创建索引
    op.create_index('ix_raw_data_task_id', 'raw_data', ['task_id'])
    op.create_index('ix_raw_data_source', 'raw_data', ['source'])

    # 创建analysis_results表
    op.create_table(
        'analysis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sentiment_score', sa.Float, nullable=True),
        sa.Column('sentiment_distribution', postgresql.JSONB, nullable=True),
        sa.Column('top_topics', postgresql.JSONB, nullable=True),
        sa.Column('feature_requests', postgresql.JSONB, nullable=True),
        sa.Column('key_insights', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    
    # 创建索引
    op.create_index('ix_analysis_results_task_id', 'analysis_results', ['task_id'])


def downgrade() -> None:
    # 删除表
    op.drop_table('analysis_results')
    op.drop_table('raw_data')
    op.drop_table('task_logs')
    op.drop_table('tasks')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS loglevel')