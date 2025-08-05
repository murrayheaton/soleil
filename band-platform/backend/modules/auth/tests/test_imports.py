"""
Test auth module imports to ensure all components are properly migrated.
"""
import pytest
import importlib
import sys


def test_auth_models_import():
    """Test that all auth models can be imported."""
    # Import models module directly
    models = importlib.import_module('modules.auth.models')
    
    # Check that all expected classes exist
    assert hasattr(models, 'User')
    assert hasattr(models, 'Band')
    assert hasattr(models, 'Instrument')
    assert hasattr(models, 'UserRole')
    assert hasattr(models, 'InstrumentFamily')
    assert hasattr(models, 'UserSchema')
    assert hasattr(models, 'BandSchema')
    assert hasattr(models, 'InstrumentSchema')
    assert hasattr(models, 'UserCreate')
    assert hasattr(models, 'UserUpdate')
    assert hasattr(models, 'BandCreate')
    assert hasattr(models, 'BandUpdate')
    assert hasattr(models, 'InstrumentCreate')
    assert hasattr(models, 'InstrumentUpdate')
    assert hasattr(models, 'UserLogin')
    assert hasattr(models, 'GoogleAuthCallback')
    assert hasattr(models, 'TokenResponse')
    assert hasattr(models, 'UserProfile')
    
    # Verify enum values
    assert models.UserRole.MEMBER
    assert models.UserRole.LEADER  
    assert models.UserRole.ADMIN
    
    assert models.InstrumentFamily.BRASS
    assert models.InstrumentFamily.WOODWIND


def test_auth_services_import():
    """Test that all auth services can be imported."""
    # Import services module directly
    services = importlib.import_module('modules.auth.services')
    
    # Check that all expected classes exist
    assert hasattr(services, 'GoogleAuthService')
    assert hasattr(services, 'JWTService')
    assert hasattr(services, 'AuthService')


def test_auth_api_import():
    """Test that auth API routers can be imported."""
    # Import API module directly
    api = importlib.import_module('modules.auth.api')
    
    # Check that routers exist
    assert hasattr(api, 'auth_router')
    assert hasattr(api, 'google_auth_router')
    
    assert api.auth_router is not None
    assert api.google_auth_router is not None


def test_auth_exceptions_import():
    """Test that auth exceptions can be imported."""
    # Import exceptions module directly
    exceptions = importlib.import_module('modules.auth.exceptions')
    
    # Check that all expected exceptions exist
    assert hasattr(exceptions, 'AuthenticationError')
    assert hasattr(exceptions, 'TokenError')
    assert hasattr(exceptions, 'AuthorizationError')
    
    # Verify exceptions are proper classes
    assert issubclass(exceptions.AuthenticationError, Exception)
    assert issubclass(exceptions.TokenError, Exception)
    assert issubclass(exceptions.AuthorizationError, Exception)


def test_compatibility_imports():
    """Test that old import paths still work with deprecation warnings."""
    import warnings
    
    # Clear the module cache for this specific module
    if 'app.services.auth' in sys.modules:
        del sys.modules['app.services.auth']
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import from old location
        auth_compat = importlib.import_module('app.services.auth')
        
        # Should have deprecation warning
        assert len(w) >= 1
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
        assert any("deprecated" in str(warning.message).lower() for warning in w)
        
        # Check that we can access the services
        assert hasattr(auth_compat, 'GoogleAuthService')
        assert hasattr(auth_compat, 'JWTService')
        assert hasattr(auth_compat, 'AuthService')