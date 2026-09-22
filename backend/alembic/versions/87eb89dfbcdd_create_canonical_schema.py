"""create canonical schema

Revision ID: 87eb89dfbcdd
Revises: 
Create Date: 2026-09-22 15:59:03.668347

"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '87eb89dfbcdd'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure PostGIS extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 1. datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('source_uri', sa.String(length=512), nullable=True),
        sa.Column('dataset_type', sa.String(length=50), nullable=False),
        sa.Column('temporal_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('temporal_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('spatial_extent', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_datasets_spatial_extent', 'datasets', ['spatial_extent'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_datasets_dataset_type'), 'datasets', ['dataset_type'], unique=False)
    op.create_index(op.f('ix_datasets_name'), 'datasets', ['name'], unique=True)
    op.create_index(op.f('ix_datasets_temporal_end'), 'datasets', ['temporal_end'], unique=False)
    op.create_index(op.f('ix_datasets_temporal_start'), 'datasets', ['temporal_start'], unique=False)

    # 2. platforms table
    op.create_table(
        'platforms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('platform_type', sa.String(length=50), nullable=False),
        sa.Column('operator', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_platforms_name'), 'platforms', ['name'], unique=True)
    op.create_index(op.f('ix_platforms_platform_type'), 'platforms', ['platform_type'], unique=False)

    # 3. array_assets table
    op.create_table(
        'array_assets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('storage_format', sa.String(length=50), nullable=False),
        sa.Column('uri', sa.String(length=512), nullable=False),
        sa.Column('variable_info', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('dimensions', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('checksum', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_array_assets_dataset_id'), 'array_assets', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_array_assets_storage_format'), 'array_assets', ['storage_format'], unique=False)

    # 4. provenance_records table
    op.create_table(
        'provenance_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('actor', sa.String(length=150), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provenance_records_action'), 'provenance_records', ['action'], unique=False)
    op.create_index(op.f('ix_provenance_records_dataset_id'), 'provenance_records', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_provenance_records_timestamp'), 'provenance_records', ['timestamp'], unique=False)

    # 5. variables table
    op.create_table(
        'variables',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('standard_name', sa.String(length=150), nullable=True),
        sa.Column('long_name', sa.String(length=255), nullable=True),
        sa.Column('units', sa.String(length=50), nullable=True),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id', 'name', name='uq_variables_dataset_name')
    )
    op.create_index(op.f('ix_variables_dataset_id'), 'variables', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_variables_name'), 'variables', ['name'], unique=False)
    op.create_index(op.f('ix_variables_standard_name'), 'variables', ['standard_name'], unique=False)

    # 6. observations table
    op.create_table(
        'observations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('variable_id', sa.UUID(), nullable=False),
        sa.Column('platform_id', sa.UUID(), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('depth_m', sa.Float(), nullable=True),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
        sa.Column('quality_flag', sa.SmallInteger(), server_default='1', nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['variable_id'], ['variables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_observations_dataset_time', 'observations', ['dataset_id', 'observed_at'], unique=False)
    op.create_index('idx_observations_depth', 'observations', ['depth_m'], unique=False)
    op.create_index('idx_observations_geometry', 'observations', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('idx_observations_platform_time', 'observations', ['platform_id', 'observed_at'], unique=False)
    op.create_index('idx_observations_variable_time', 'observations', ['variable_id', 'observed_at'], unique=False)
    op.create_index(op.f('ix_observations_dataset_id'), 'observations', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_observations_observed_at'), 'observations', ['observed_at'], unique=False)
    op.create_index(op.f('ix_observations_platform_id'), 'observations', ['platform_id'], unique=False)
    op.create_index(op.f('ix_observations_variable_id'), 'observations', ['variable_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_observations_variable_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_platform_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_observed_at'), table_name='observations')
    op.drop_index(op.f('ix_observations_dataset_id'), table_name='observations')
    op.drop_index('idx_observations_variable_time', table_name='observations')
    op.drop_index('idx_observations_platform_time', table_name='observations')
    op.drop_index('idx_observations_geometry', table_name='observations', postgresql_using='gist')
    op.drop_index('idx_observations_depth', table_name='observations')
    op.drop_index('idx_observations_dataset_time', table_name='observations')
    op.drop_table('observations')

    op.drop_index(op.f('ix_variables_standard_name'), table_name='variables')
    op.drop_index(op.f('ix_variables_name'), table_name='variables')
    op.drop_index(op.f('ix_variables_dataset_id'), table_name='variables')
    op.drop_table('variables')

    op.drop_index(op.f('ix_provenance_records_timestamp'), table_name='provenance_records')
    op.drop_index(op.f('ix_provenance_records_dataset_id'), table_name='provenance_records')
    op.drop_index(op.f('ix_provenance_records_action'), table_name='provenance_records')
    op.drop_table('provenance_records')

    op.drop_index(op.f('ix_array_assets_storage_format'), table_name='array_assets')
    op.drop_index(op.f('ix_array_assets_dataset_id'), table_name='array_assets')
    op.drop_table('array_assets')

    op.drop_index(op.f('ix_platforms_platform_type'), table_name='platforms')
    op.drop_index(op.f('ix_platforms_name'), table_name='platforms')
    op.drop_table('platforms')

    op.drop_index(op.f('ix_datasets_temporal_start'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_temporal_end'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_name'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_dataset_type'), table_name='datasets')
    op.drop_index('idx_datasets_spatial_extent', table_name='datasets', postgresql_using='gist')
    op.drop_table('datasets')
