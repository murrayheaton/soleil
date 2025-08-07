"""
Unit tests for the role management API endpoints.

Tests the REST API functionality for managing user roles, instruments,
and triggering folder reorganization.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.api.role_management import (
    InstrumentUpdate,
    RoleUpdate,
    AccessibleFilesResponse,
    router
)
from app.models.user import User, UserRole, Band
from app.models.folder_structure import UserFolder, SyncStatus


class TestInstrumentUpdate:
    """Test cases for the InstrumentUpdate Pydantic model."""
    
    def test_valid_instrument_update(self):
        """Test creating valid instrument update."""
        update = InstrumentUpdate(
            instruments=["trumpet", "flugelhorn"],
            primary_instrument="trumpet",
            reorganize_folders=True
        )
        
        assert update.instruments == ["trumpet", "flugelhorn"]
        assert update.primary_instrument == "trumpet"
        assert update.reorganize_folders is True
    
    def test_instrument_validation_unknown_instrument(self):
        """Test that unknown instruments are rejected."""
        with pytest.raises(ValueError, match="Unknown instrument"):
            InstrumentUpdate(
                instruments=["unknown_instrument"],
                reorganize_folders=False
            )
    
    def test_instrument_validation_empty_list(self):
        """Test that empty instrument list is rejected."""
        with pytest.raises(ValueError, match="At least one instrument must be specified"):
            InstrumentUpdate(
                instruments=[],
                reorganize_folders=False
            )
    
    def test_primary_instrument_validation_not_in_list(self):
        """Test that primary instrument must be in instruments list."""
        with pytest.raises(ValueError, match="Primary instrument must be in the instruments list"):
            InstrumentUpdate(
                instruments=["trumpet"],
                primary_instrument="saxophone",  # Not in instruments list
                reorganize_folders=False
            )
    
    def test_instrument_name_normalization(self):
        """Test that instrument names are normalized properly."""
        # Should work with various formats
        update = InstrumentUpdate(
            instruments=["Alto Saxophone", "bass-clarinet"],
            primary_instrument="Alto Saxophone",
            reorganize_folders=False
        )
        
        # Should normalize to match INSTRUMENT_KEY_MAPPING
        assert "Alto Saxophone" in update.instruments


class TestRoleUpdate:
    """Test cases for the RoleUpdate Pydantic model."""
    
    def test_valid_role_update(self):
        """Test creating valid role update."""
        update = RoleUpdate(
            role=UserRole.LEADER,
            reorganize_folders=True
        )
        
        assert update.role == UserRole.LEADER
        assert update.reorganize_folders is True
    
    def test_default_reorganize_folders(self):
        """Test default value for reorganize_folders."""
        update = RoleUpdate(role=UserRole.MEMBER)
        
        assert update.reorganize_folders is False


class TestRoleManagementEndpoints:
    """Test cases for role management API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test app with just the role management router
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        
        # Mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.name = "Test User"
        self.mock_user.email = "test@example.com"
        self.mock_user.instruments = ["trumpet"]
        self.mock_user.primary_instrument = "trumpet"
        self.mock_user.is_admin = False
        
        # Mock band
        self.mock_band = Mock(spec=Band)
        self.mock_band.google_drive_folder_id = "source_folder_123"
        self.mock_user.band = self.mock_band
        
        # Mock user folder
        self.mock_user_folder = Mock(spec=UserFolder)
        self.mock_user_folder.sync_status = SyncStatus.COMPLETED
        self.mock_user.user_folder = self.mock_user_folder
    
    @patch('app.api.role_management.get_current_user')
    @patch('app.api.role_management.get_drive_credentials')
    def test_update_user_instruments_success(self, mock_get_creds, mock_get_user):
        """Test successful instrument update."""
        mock_get_user.return_value = self.mock_user
        mock_get_creds.return_value = Mock()  # Mock credentials
        
        # Mock database operations
        with patch('app.api.role_management.schedule_sync_for_users') as mock_schedule:
            mock_schedule.return_value = "job_123"
            
            with patch('app.api.role_management.AsyncSession') as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value = mock_db
                
                # Mock database query
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = self.mock_user
                mock_db.execute.return_value = mock_result
                
                response = self.client.put(
                    "/users/1/instruments",
                    json={
                        "instruments": ["trumpet", "flugelhorn"],
                        "primary_instrument": "trumpet",
                        "reorganize_folders": True
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["user_id"] == 1
                assert data["new_instruments"] == ["trumpet", "flugelhorn"]
                assert data["reorganization_status"] == "started"
                assert data["job_id"] == "job_123"
    
    @patch('app.api.role_management.get_current_user')
    def test_update_user_instruments_permission_denied(self, mock_get_user):
        """Test that users can only update their own instruments."""
        # Current user is not the target user and not admin
        mock_current_user = Mock(spec=User)
        mock_current_user.id = 2
        mock_current_user.is_admin = False
        mock_get_user.return_value = mock_current_user
        
        response = self.client.put(
            "/users/1/instruments", 
            json={
                "instruments": ["trumpet"],
                "reorganize_folders": False
            }
        )
        
        assert response.status_code == 403
        assert "only update your own instruments" in response.json()["detail"]
    
    @patch('app.api.role_management.get_current_user')
    def test_update_user_role_admin_only(self, mock_get_user):
        """Test that only admins can change user roles."""
        # Non-admin user
        mock_get_user.return_value = self.mock_user
        
        response = self.client.put(
            "/users/1/role",
            json={
                "role": "band_leader",
                "reorganize_folders": False
            }
        )
        
        assert response.status_code == 403
        assert "Only administrators" in response.json()["detail"]
    
    @patch('app.api.role_management.get_current_user')
    def test_update_user_role_success(self, mock_get_user):
        """Test successful role update by admin."""
        # Admin user
        admin_user = Mock(spec=User)
        admin_user.id = 2
        admin_user.is_admin = True
        mock_get_user.return_value = admin_user
        
        with patch('app.api.role_management.AsyncSession') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock database query
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = self.mock_user
            mock_db.execute.return_value = mock_result
            
            response = self.client.put(
                "/users/1/role",
                json={
                    "role": "band_leader",
                    "reorganize_folders": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return updated user info
            assert "id" in data
            assert "role" in data
    
    @patch('app.api.role_management.get_current_user')
    def test_get_accessible_files_permission_check(self, mock_get_user):
        """Test that users can only view their own accessible files."""
        # Non-admin user trying to view another user's files
        mock_current_user = Mock(spec=User)
        mock_current_user.id = 2
        mock_current_user.is_admin = False
        mock_get_user.return_value = mock_current_user
        
        response = self.client.get("/users/1/accessible-files")
        
        assert response.status_code == 403
        assert "only view your own accessible files" in response.json()["detail"]
    
    @patch('app.api.role_management.get_current_user')
    def test_get_accessible_files_success(self, mock_get_user):
        """Test successful retrieval of accessible files."""
        mock_get_user.return_value = self.mock_user
        
        with patch('app.api.role_management.AsyncSession') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock database query
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = self.mock_user
            mock_db.execute.return_value = mock_result
            
            response = self.client.get("/users/1/accessible-files")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["user_id"] == 1
            assert data["instruments"] == ["trumpet"]
            assert "Bb" in data["accessible_keys"]  # Trumpet uses Bb key
            assert "files_by_key" in data
            assert "files_by_type" in data
    
    @patch('app.api.role_management.get_current_user')
    def test_trigger_reorganization_permission_check(self, mock_get_user):
        """Test permission check for folder reorganization."""
        # Non-admin user trying to reorganize another user's folders
        mock_current_user = Mock(spec=User)
        mock_current_user.id = 2
        mock_current_user.is_admin = False
        mock_get_user.return_value = mock_current_user
        
        response = self.client.post("/users/1/reorganize")
        
        assert response.status_code == 403
        assert "only reorganize your own folders" in response.json()["detail"]
    
    @patch('app.api.role_management.get_current_user')
    @patch('app.api.role_management.get_drive_credentials')
    def test_trigger_reorganization_success(self, mock_get_creds, mock_get_user):
        """Test successful folder reorganization trigger."""
        mock_get_user.return_value = self.mock_user
        mock_get_creds.return_value = Mock()  # Mock credentials
        
        with patch('app.api.role_management.schedule_sync_for_users') as mock_schedule:
            mock_schedule.return_value = "job_456"
            
            with patch('app.api.role_management.AsyncSession') as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value = mock_db
                
                # Mock database query
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = self.mock_user
                mock_db.execute.return_value = mock_result
                
                response = self.client.post("/users/1/reorganize")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["status"] == "reorganization_started"
                assert data["user_id"] == 1
                assert data["job_id"] == "job_456"
    
    @patch('app.api.role_management.get_current_user')
    def test_trigger_reorganization_no_folder_structure(self, mock_get_user):
        """Test error when user has no folder structure to reorganize."""
        # User with no folder structure
        self.mock_user.user_folder = None
        mock_get_user.return_value = self.mock_user
        
        with patch('app.api.role_management.AsyncSession') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock database query
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = self.mock_user
            mock_db.execute.return_value = mock_result
            
            response = self.client.post("/users/1/reorganize")
            
            assert response.status_code == 400
            assert "no folder structure to reorganize" in response.json()["detail"]
    
    @patch('app.api.role_management.get_current_user')
    def test_trigger_reorganization_already_in_progress(self, mock_get_user):
        """Test handling when reorganization is already in progress."""
        # Set folder status to in progress
        self.mock_user_folder.sync_status = SyncStatus.IN_PROGRESS
        mock_get_user.return_value = self.mock_user
        
        with patch('app.api.role_management.AsyncSession') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock database query
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = self.mock_user
            mock_db.execute.return_value = mock_result
            
            response = self.client.post("/users/1/reorganize")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "already_running"
            assert "already in progress" in data["message"]
    
    def test_list_available_instruments(self):
        """Test listing available instruments."""
        response = self.client.get("/instruments")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "instruments_by_key" in data
        assert "all_keys" in data
        assert "total_instruments" in data
        
        # Should have instruments grouped by keys
        assert "C" in data["instruments_by_key"]
        assert "Bb" in data["instruments_by_key"]
        assert "Eb" in data["instruments_by_key"]
        
        # Should include key descriptions
        assert "key_descriptions" in data
        assert "Concert pitch instruments" in data["key_descriptions"]["C"]
    
    def test_list_available_roles(self):
        """Test listing available user roles."""
        response = self.client.get("/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "roles" in data
        assert "role_hierarchy" in data
        
        # Should have all user roles
        roles = data["roles"]
        assert UserRole.MEMBER in roles
        assert UserRole.LEADER in roles
        assert UserRole.ADMIN in roles
        
        # Each role should have description and permissions
        for role_info in roles.values():
            assert "name" in role_info
            assert "description" in role_info
            assert "permissions" in role_info
    
    def test_invalid_instrument_in_request(self):
        """Test handling of invalid instruments in API request."""
        response = self.client.put(
            "/users/1/instruments",
            json={
                "instruments": ["invalid_instrument"],
                "reorganize_folders": False
            }
        )
        
        assert response.status_code == 422  # Validation error
        assert "Unknown instrument" in response.json()["detail"][0]["msg"]
    
    def test_invalid_role_in_request(self):
        """Test handling of invalid role in API request."""
        response = self.client.put(
            "/users/1/role",
            json={
                "role": "invalid_role",
                "reorganize_folders": False
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestAccessibleFilesResponse:
    """Test cases for the AccessibleFilesResponse model."""
    
    def test_create_accessible_files_response(self):
        """Test creating AccessibleFilesResponse."""
        response = AccessibleFilesResponse(
            user_id=1,
            instruments=["trumpet"],
            accessible_keys=["Bb", "C"],
            total_files=100,
            accessible_files=50,
            files_by_key={"Bb": 25, "C": 20},
            files_by_type={"chart": 45, "audio": 5}
        )
        
        assert response.user_id == 1
        assert response.instruments == ["trumpet"]
        assert response.accessible_keys == ["Bb", "C"]
        assert response.total_files == 100
        assert response.accessible_files == 50
        assert response.files_by_key["Bb"] == 25
        assert response.files_by_type["chart"] == 45