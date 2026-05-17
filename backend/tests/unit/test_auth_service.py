"""
Unit tests for AuthService.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.features.auth.service import AuthService
from app.features.auth.schemas import LoginRequest
from app.features.auth.models import User
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_authenticate_user_success():
    # Arrange
    mock_db = AsyncMock()
    service = AuthService(mock_db)
    
    password = "testpassword"
    hashed = hash_password(password)
    
    mock_user = User(
        id="user-id",
        email="test@example.com",
        password_hash=hashed,
        role="ADMIN",
        name="Test Admin"
    )
    
    # Mock the DB result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    login_data = LoginRequest(email="test@example.com", password=password)
    
    # Act
    authenticated_user = await service.authenticate(login_data)
    
    # Assert
    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"
    assert authenticated_user.id == "user-id"
    assert authenticated_user.role == "ADMIN"

@pytest.mark.asyncio
async def test_authenticate_user_failure():
    # Arrange
    mock_db = AsyncMock()
    service = AuthService(mock_db)
    
    # Mock the DB result (user not found)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    login_data = LoginRequest(email="wrong@example.com", password="any")
    
    # Act
    authenticated_user = await service.authenticate(login_data)
    
    # Assert
    assert authenticated_user is None
