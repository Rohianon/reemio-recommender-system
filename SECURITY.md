# Security Considerations

## ⚠️ Current Demo Implementation

The current implementation uses `user_id` as a query parameter for **demo purposes only**. This is **NOT secure** for production use.

### Issues with Current Approach

1. **URL Exposure**: User IDs are visible in browser history, server logs, and network traffic
2. **No Authentication**: Anyone can request recommendations for any user
3. **Privacy Concerns**: User behavior patterns can be tracked without authorization
4. **Session Hijacking**: User IDs can be easily copied and reused

## ✅ Production-Ready Authentication

For production, implement one of these approaches:

### Option 1: JWT Token Authentication (Recommended)

```python
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

async def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/homepage", response_model=RecommendationResponse)
async def get_homepage_recommendations(
    current_user: str = Depends(get_current_user),
    limit: int = Query(12, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    engine = HybridRecommendationEngine(session)
    result = await engine.get_homepage_recommendations(user_id=current_user, limit=limit)
    return RecommendationResponse(**result)
```

### Option 2: Session-Based Authentication

```python
from fastapi import Depends, HTTPException, Request

async def get_session_user(request: Request) -> str:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id

@router.get("/homepage", response_model=RecommendationResponse)
async def get_homepage_recommendations(
    current_user: str = Depends(get_session_user),
    limit: int = Query(12, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    engine = HybridRecommendationEngine(session)
    result = await engine.get_homepage_recommendations(user_id=current_user, limit=limit)
    return RecommendationResponse(**result)
```

### Option 3: API Key + User Context

```python
from fastapi import Depends, HTTPException, Header

async def verify_api_key_and_get_user(
    x_api_key: str = Header(...),
    x_user_id: str = Header(...),
) -> str:
    if not is_valid_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not user_has_permission(x_api_key, x_user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    return x_user_id
```

## Frontend Changes for Production

Update the frontend to send authentication tokens:

```javascript
// Store token after login
localStorage.setItem('authToken', token);

// Include in API requests
async function loadHomepageRecommendations() {
    const token = localStorage.getItem('authToken');

    const response = await fetch(`${API_BASE_URL}/recommendations/homepage?limit=12`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();
    // ... render recommendations
}
```

## Additional Security Measures

1. **Rate Limiting**: Implement rate limiting per user/IP
2. **HTTPS Only**: Always use HTTPS in production
3. **CORS Configuration**: Restrict CORS to specific domains (remove `*`)
4. **Input Validation**: Validate all user inputs
5. **Audit Logging**: Log all access attempts
6. **Data Encryption**: Encrypt sensitive user data at rest

## Quick Fix for Current Demo

If you want to keep the demo simple but slightly more secure, you can:

1. Use HTTP-only cookies instead of query parameters
2. Add a simple API key requirement
3. Implement rate limiting

But remember: **The current implementation is for demonstration only and should never be used in production without proper authentication!**
