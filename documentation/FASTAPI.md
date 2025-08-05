# FastAPI Documentation for SOLEil

## Overview
FastAPI is the modern Python web framework used for SOLEil's backend API. It provides high performance, automatic API documentation, and type safety.

## Project Structure

### Main Application
- **Entry Point**: `/band-platform/backend/start_server.py`
- **Module Registration**: Automatic module discovery and registration
- **API Version**: v1 (prefix: `/api`)

### Module Organization
```
backend/
├── modules/
│   ├── auth/          # Authentication module
│   ├── content/       # Content management
│   ├── drive/         # Google Drive integration
│   ├── sync/          # WebSocket sync
│   └── dashboard/     # Dashboard aggregation
├── core/              # Shared utilities
└── start_server.py    # Application entry
```

## Core Concepts

### Application Factory
```python
# start_server.py
app = FastAPI(
    title="SOLEil API",
    description="Band platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://solepower.live"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Module Registration
```python
# Each module exports a router
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login")
async def login(credentials: LoginSchema):
    # Implementation
    pass
```

## Request/Response Models

### Pydantic Models
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    """User profile data model"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    display_name: str = Field(..., description="Display name")
    instruments: List[str] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        # Enable ORM mode for SQLAlchemy integration
        from_attributes = True
```

### Request Validation
```python
@router.post("/user/profile")
async def update_profile(
    profile: UserProfile,
    current_user: User = Depends(get_current_user)
):
    """Update user profile with validation"""
    # FastAPI automatically validates the request body
    return await profile_service.update(current_user.id, profile)
```

## Dependency Injection

### Authentication Dependencies
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Validate JWT token and return current user"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401)
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401)
```

### Database Session
```python
async def get_db() -> AsyncSession:
    """Provide database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## API Documentation

### Automatic Documentation
- **Swagger UI**: `https://solepower.live/api/docs`
- **ReDoc**: `https://solepower.live/api/redoc`

### Custom Documentation
```python
@router.get(
    "/files",
    response_model=List[FileResponse],
    summary="List files",
    description="Get a list of files from Google Drive",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def list_files(
    folder_id: str = Query(..., description="Drive folder ID"),
    file_type: Optional[str] = Query(None, description="Filter by type")
):
    """List files with filtering"""
    pass
```

## Error Handling

### Global Exception Handler
```python
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### Custom Exceptions
```python
class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class PermissionError(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=403, detail=detail)
```

## Middleware

### Request Logging
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/expensive-operation")
@limiter.limit("5/minute")
async def expensive_operation(request: Request):
    # Implementation
    pass
```

## Background Tasks

### Using BackgroundTasks
```python
from fastapi import BackgroundTasks

@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Trigger background sync"""
    background_tasks.add_task(sync_user_content, user.id)
    return {"message": "Sync started"}

async def sync_user_content(user_id: str):
    """Background sync implementation"""
    # Long-running task
    pass
```

## File Handling

### File Upload
```python
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Handle file upload"""
    # Validate file
    if file.content_type not in ["application/pdf", "image/jpeg"]:
        raise HTTPException(400, "Invalid file type")
    
    # Process file
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

### File Streaming
```python
from fastapi.responses import StreamingResponse

@router.get("/stream/{file_id}")
async def stream_file(file_id: str):
    """Stream large files"""
    async def generate():
        async for chunk in get_file_chunks(file_id):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="application/pdf"
    )
```

## Testing

### Test Client
```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client():
    from start_server import app
    return TestClient(app)

def test_login(client):
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Async Testing
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/users/me")
        assert response.status_code == 401  # Unauthorized
```

## Performance Optimization

### Response Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/repertoire")
@cache(expire=300)  # Cache for 5 minutes
async def get_repertoire(user: User = Depends(get_current_user)):
    return await fetch_user_repertoire(user.id)
```

### Database Query Optimization
```python
# Use select_related for joins
from sqlalchemy.orm import selectinload

@router.get("/bands/{band_id}")
async def get_band_with_members(
    band_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Band).options(
        selectinload(Band.members)
    ).where(Band.id == band_id)
    
    result = await db.execute(query)
    return result.scalar_one()
```

## Security Best Practices

### Input Validation
```python
from pydantic import validator, constr

class CreateUser(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### SQL Injection Prevention
```python
# Always use parameterized queries
@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db)
):
    # Safe parameterized query
    query = select(Song).where(Song.title.ilike(f"%{q}%"))
    result = await db.execute(query)
    return result.scalars().all()
```

## Deployment Configuration

### Production Settings
```python
# config.py
class Settings(BaseSettings):
    # API Settings
    api_prefix: str = "/api"
    debug: bool = False
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str
    
    # CORS
    cors_origins: List[str] = ["https://solepower.live"]
    
    class Config:
        env_file = ".env"
```

### Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy + FastAPI Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)