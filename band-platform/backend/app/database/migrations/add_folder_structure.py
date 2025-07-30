"""
Database migration to add folder structure tables.

This migration creates the tables needed for Google Drive role-based
folder organization and synchronization tracking.

Revision: add_folder_structure
Created: 2025-07-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """
    Create tables for folder structure management.
    
    This adds support for:
    - User-specific folder organization
    - Song folder tracking  
    - Sync operation logging
    """
    
    # Create user_folders table
    op.create_table(
        'user_folders',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('google_folder_id', sa.String(255), nullable=False),
        sa.Column('source_folder_id', sa.String(255), nullable=False),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('file_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        # Indexes for performance
        sa.Index('idx_user_folders_user_id', 'user_id'),
        sa.Index('idx_user_folders_google_folder_id', 'google_folder_id'),
        sa.Index('idx_user_folders_source_folder_id', 'source_folder_id'),
        sa.Index('idx_user_folders_sync_status', 'sync_status'),
    )
    
    # Create user_song_folders table
    op.create_table(
        'user_song_folders',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_folder_id', sa.Integer(), sa.ForeignKey('user_folders.id'), nullable=False),
        sa.Column('song_title', sa.String(255), nullable=False),
        sa.Column('google_folder_id', sa.String(255), nullable=False),
        sa.Column('shortcut_count', sa.Integer(), nullable=False, default=0),
        sa.Column('chart_count', sa.Integer(), nullable=False, default=0),
        sa.Column('audio_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('needs_update', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        # Indexes for performance
        sa.Index('idx_user_song_folders_user_folder_id', 'user_folder_id'),
        sa.Index('idx_user_song_folders_song_title', 'song_title'),
        sa.Index('idx_user_song_folders_google_folder_id', 'google_folder_id'),
        sa.Index('idx_user_song_folders_needs_update', 'needs_update'),
    )
    
    # Create folder_sync_logs table
    op.create_table(
        'folder_sync_logs',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('operation', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('files_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('shortcuts_created', sa.Integer(), nullable=False, default=0),
        sa.Column('shortcuts_deleted', sa.Integer(), nullable=False, default=0),
        sa.Column('folders_created', sa.Integer(), nullable=False, default=0),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        # Indexes for performance
        sa.Index('idx_folder_sync_logs_user_id', 'user_id'),
        sa.Index('idx_folder_sync_logs_operation', 'operation'),
        sa.Index('idx_folder_sync_logs_status', 'status'),
        sa.Index('idx_folder_sync_logs_started_at', 'started_at'),
    )
    
    # Add foreign key constraints with explicit names
    op.create_foreign_key(
        'fk_user_folders_user_id',
        'user_folders', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_user_song_folders_user_folder_id',
        'user_song_folders', 'user_folders',
        ['user_folder_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_folder_sync_logs_user_id',
        'folder_sync_logs', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """
    Remove folder structure tables.
    
    This reverses the migration by dropping all tables created
    for folder management functionality.
    """
    
    # Drop foreign key constraints first
    op.drop_constraint('fk_folder_sync_logs_user_id', 'folder_sync_logs', type_='foreignkey')
    op.drop_constraint('fk_user_song_folders_user_folder_id', 'user_song_folders', type_='foreignkey')
    op.drop_constraint('fk_user_folders_user_id', 'user_folders', type_='foreignkey')
    
    # Drop tables in reverse dependency order
    op.drop_table('folder_sync_logs')
    op.drop_table('user_song_folders')
    op.drop_table('user_folders')


# Migration metadata
revision = 'add_folder_structure'
down_revision = None  # This would be the previous migration ID
branch_labels = None
depends_on = None

# Description for Alembic history
"""Add folder structure tables for Google Drive organization

This migration creates the database tables needed to support Google Drive
role-based folder organization including:

- user_folders: Tracks each user's root folder and sync status
- user_song_folders: Tracks individual song folders within user structures  
- folder_sync_logs: Audit trail for all sync operations

The tables include proper indexes for performance and foreign key constraints
for data integrity. All timestamps use UTC and include proper defaults.
"""