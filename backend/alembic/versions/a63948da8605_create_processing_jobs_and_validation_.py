"""create processing_jobs and validation_runs tables

Revision ID: a63948da8605
Revises: 87eb89dfbcdd
Create Date: 2026-09-22 18:08:22.684659

"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a63948da8605'
down_revision: Union[str, Sequence[str], None] = '87eb89dfbcdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. processing_jobs table
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='QUEUED', nullable=False),
        sa.Column('initiated_by', sa.String(length=128), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs_uri', sa.String(length=512), nullable=True),
        sa.Column('job_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_processing_jobs_dataset_status', 'processing_jobs', ['dataset_id', 'status'], unique=False)
    op.create_index('idx_processing_jobs_status', 'processing_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_processing_jobs_dataset_id'), 'processing_jobs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_processing_jobs_job_type'), 'processing_jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_processing_jobs_status'), 'processing_jobs', ['status'], unique=False)

    # 2. validation_runs table
    op.create_table(
        'validation_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('model_dataset_id', sa.UUID(), nullable=False),
        sa.Column('observation_dataset_id', sa.UUID(), nullable=True),
        sa.Column('variable_id', sa.UUID(), nullable=False),
        sa.Column('spatial_scope_geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('time_range_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_range_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('depth_level_min', sa.Float(), nullable=True),
        sa.Column('depth_level_max', sa.Float(), nullable=True),
        sa.Column('metric_mae', sa.Float(), nullable=True),
        sa.Column('metric_rmse', sa.Float(), nullable=True),
        sa.Column('metric_bias', sa.Float(), nullable=True),
        sa.Column('metric_correlation', sa.Float(), nullable=True),
        sa.Column('sample_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('result_payload', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['observation_dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['variable_id'], ['variables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_validation_runs_created_at', 'validation_runs', ['created_at'], unique=False)
    op.create_index('idx_validation_runs_model_var', 'validation_runs', ['model_dataset_id', 'variable_id'], unique=False)
    op.create_index(op.f('ix_validation_runs_model_dataset_id'), 'validation_runs', ['model_dataset_id'], unique=False)
    op.create_index(op.f('ix_validation_runs_observation_dataset_id'), 'validation_runs', ['observation_dataset_id'], unique=False)
    op.create_index(op.f('ix_validation_runs_variable_id'), 'validation_runs', ['variable_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_validation_runs_variable_id'), table_name='validation_runs')
    op.drop_index(op.f('ix_validation_runs_observation_dataset_id'), table_name='validation_runs')
    op.drop_index(op.f('ix_validation_runs_model_dataset_id'), table_name='validation_runs')
    op.drop_index('idx_validation_runs_model_var', table_name='validation_runs')
    op.drop_index('idx_validation_runs_created_at', table_name='validation_runs')
    op.drop_table('validation_runs')

    op.drop_index(op.f('ix_processing_jobs_status'), table_name='processing_jobs')
    op.drop_index(op.f('ix_processing_jobs_job_type'), table_name='processing_jobs')
    op.drop_index(op.f('ix_processing_jobs_dataset_id'), table_name='processing_jobs')
    op.drop_index('idx_processing_jobs_status', table_name='processing_jobs')
    op.drop_index('idx_processing_jobs_dataset_status', table_name='processing_jobs')
    op.drop_table('processing_jobs')
