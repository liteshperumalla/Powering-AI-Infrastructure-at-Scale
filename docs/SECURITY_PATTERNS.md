# Security Implementation Patterns

**Purpose:** Reusable security patterns for fixing remaining vulnerabilities
**Date:** November 4, 2025
**For:** Development team implementing security fixes

---

## 🔒 Pattern 1: IDOR Prevention (Authorization Checks)

### Problem: Insecure Direct Object Reference
Users can access others' resources by guessing IDs.

### Vulnerable Code:
```python
@router.get("/recommendations/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user)
):
    # ❌ VULNERABLE: Gets resource WITHOUT checking ownership
    recommendation = await Recommendation.get(recommendation_id)

    if not recommendation:
        raise HTTPException(status_code=404, detail="Not found")

    return recommendation  # ❌ Returns ANY user's data!
```

### Secure Pattern:
```python
@router.get("/recommendations/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user)
):
    # ✅ SECURE: Query includes ownership check
    recommendation = await Recommendation.find_one({
        "_id": recommendation_id,
        "user_id": str(current_user.id)  # ✅ Ownership verification
    })

    if not recommendation:
        # Return 404 for both "not found" and "not yours"
        # Don't leak existence of other users' data
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return recommendation
```

### Apply To All Resource Endpoints:
- `/api/v1/assessments/{id}` ✅
- `/api/v1/recommendations/{id}` ⚠️ NEEDS FIX
- `/api/v1/reports/{id}` ⚠️ NEEDS FIX
- `/api/v1/conversations/{id}` ⚠️ NEEDS FIX
- Any endpoint that accesses user-specific resources

---

## 🛡️ Pattern 2: Error Message Sanitization

### Problem: Information Disclosure
Internal errors expose database schema, file paths, and architecture.

### Vulnerable Code:
```python
try:
    result = await process_recommendation(assessment_id)
    return result
except Exception as e:
    # ❌ VULNERABLE: Exposes internal error details
    raise HTTPException(
        status_code=500,
        detail=f"Failed to process: {str(e)}"  # ❌ Leaks internals!
    )
```

**What This Exposes:**
- Database schema: `"collection 'recommendations' not found"`
- File paths: `"/app/src/infra_mind/services/processor.py"`
- Library versions: `"pymongo.errors.OperationFailure"`
- Internal architecture: `"Redis connection failed at 192.168.1.100"`

### Secure Pattern:
```python
try:
    result = await process_recommendation(assessment_id)
    return result
except ValueError as ve:
    # Validation errors can be shown (user error)
    logger.warning(f"Validation error for user {current_user.id}: {ve}")
    raise HTTPException(
        status_code=400,
        detail=str(ve)  # ✅ User-caused error, safe to show
    )
except HTTPException:
    # Re-raise HTTP exceptions as-is
    raise
except Exception as e:
    # ✅ SECURE: Log internally, return generic message
    logger.error(
        f"Internal error in process_recommendation: {e}",
        exc_info=True,  # Full traceback in logs
        extra={
            "user_id": str(current_user.id),
            "assessment_id": assessment_id
        }
    )

    raise HTTPException(
        status_code=500,
        detail="An internal error occurred. Please try again later."  # ✅ Generic
    )
```

### Exception Handling Strategy:

| Exception Type | User Message | Log Level | Include Details? |
|---------------|--------------|-----------|------------------|
| `ValueError` | Show message | WARNING | Yes (user error) |
| `HTTPException` | Re-raise as-is | INFO | Yes (expected) |
| `pymongo.errors.*` | Generic | ERROR | No (internal) |
| `redis.exceptions.*` | Generic | ERROR | No (internal) |
| `Exception` | Generic | ERROR | No (catch-all) |

---

## 🔐 Pattern 3: MFA Secret Encryption

### Problem: Plaintext MFA Secrets
MFA secrets stored unencrypted in database.

### Vulnerable Code:
```python
class User:
    async def enable_mfa(self):
        secret = pyotp.random_base32()
        self.mfa_secret = secret  # ❌ Plaintext storage!
        await self.save()
        return secret

    def verify_mfa(self, token: str) -> bool:
        totp = pyotp.TOTP(self.mfa_secret)  # ❌ Reads plaintext
        return totp.verify(token)
```

### Secure Pattern:
```python
from ..core.encryption import encrypt_mfa_secret, decrypt_mfa_secret

class User:
    async def enable_mfa(self):
        secret = pyotp.random_base32()

        # ✅ Encrypt before storing
        self.mfa_secret = encrypt_mfa_secret(secret)
        await self.save()

        # Return plaintext for QR code generation (not stored)
        return secret

    def verify_mfa(self, token: str) -> bool:
        # ✅ Decrypt when verifying
        try:
            decrypted_secret = decrypt_mfa_secret(self.mfa_secret)
            totp = pyotp.TOTP(decrypted_secret)
            return totp.verify(token)
        except ValueError as e:
            logger.error(f"MFA decryption failed for user {self.id}: {e}")
            return False
```

### Migration Script:
```python
# scripts/migrate_mfa_secrets.py
from infra_mind.models.user import User
from infra_mind.core.encryption import encrypt_mfa_secret
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def migrate_mfa_secrets():
    """Encrypt existing plaintext MFA secrets."""
    client = AsyncIOMotorClient(os.getenv("INFRA_MIND_MONGODB_URL"))
    db = client.get_database("infra_mind")

    users_with_mfa = await db.users.find({"mfa_enabled": True}).to_list(None)

    migrated = 0
    for user_doc in users_with_mfa:
        secret = user_doc.get("mfa_secret")

        if secret:
            try:
                # Try to decrypt - if it works, already encrypted
                decrypt_mfa_secret(secret)
                print(f"User {user_doc['_id']} already encrypted")
            except ValueError:
                # Not encrypted, encrypt it now
                encrypted = encrypt_mfa_secret(secret)
                await db.users.update_one(
                    {"_id": user_doc["_id"]},
                    {"$set": {"mfa_secret": encrypted}}
                )
                migrated += 1
                print(f"✅ Migrated user {user_doc['_id']}")

    print(f"\n✅ Migration complete: {migrated} users migrated")

if __name__ == "__main__":
    asyncio.run(migrate_mfa_secrets())
```

---

## 🚦 Pattern 4: Rate Limiting Application

### Problem: No Rate Limiting
Endpoints vulnerable to brute force and DoS attacks.

### Apply Rate Limiting:

```python
from fastapi import Request
from ...core.rate_limiter import RateLimiter

# Initialize rate limiter
rate_limiter = RateLimiter()

# Pattern A: Decorator approach (recommended)
@router.post("/sensitive-operation")
@rate_limiter.limit(calls=10, period=60)  # 10 calls per minute
async def sensitive_operation(request: Request, data: DataModel):
    ...

# Pattern B: Manual check (for custom logic)
@router.post("/custom-operation")
async def custom_operation(request: Request, data: DataModel):
    # Custom rate limit check
    allowed, info = await rate_limiter.check_rate_limit(
        request=request,
        endpoint="custom_operation",
        calls=5,
        period=300,  # 5 calls per 5 minutes
        user_id=str(current_user.id) if current_user else None
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(info["retry_after"])}
        )

    ...
```

### Recommended Limits by Endpoint Type:

| Endpoint Type | Calls | Period | Rationale |
|--------------|-------|--------|-----------|
| **Login** | 5 | 60s | Prevent brute force |
| **Register** | 3 | 3600s | Prevent spam accounts |
| **Password Reset** | 3 | 3600s | Prevent enumeration |
| **MFA Verify** | 5 | 300s | Prevent token guessing |
| **API Read** | 100 | 60s | Normal usage |
| **API Write** | 50 | 60s | Prevent abuse |
| **File Upload** | 10 | 60s | Resource intensive |

---

## 🔑 Pattern 5: Password Strength Enforcement

### Problem: Weak Passwords
Only length requirement, no complexity check.

### Vulnerable Code:
```python
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)  # ❌ Only length!
```

### Secure Pattern:
```python
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @validator('password')
    def validate_password_strength(cls, password):
        """
        Enforce password complexity requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")

        # Check for common weak passwords
        common_passwords = ['password', '12345678', 'qwerty123']
        if password.lower() in common_passwords:
            raise ValueError("This password is too common. Please choose a stronger password")

        return password
```

---

## 📋 Implementation Checklist

### P0 - Critical (Complete This Week):

- [ ] **IDOR Fixes** (8 hours)
  - [ ] Audit all resource access endpoints
  - [ ] Add ownership checks to GET /{id} endpoints
  - [ ] Add ownership checks to PUT /{id} endpoints
  - [ ] Add ownership checks to DELETE /{id} endpoints
  - [ ] Test with different user accounts

- [ ] **Error Sanitization** (6 hours)
  - [ ] Audit all exception handlers
  - [ ] Replace detailed errors with generic messages
  - [ ] Ensure all errors logged with context
  - [ ] Test error responses don't leak info

- [ ] **MFA Encryption** (4 hours)
  - [ ] Generate MFA_ENCRYPTION_KEY
  - [ ] Update User model to use encryption
  - [ ] Run migration script for existing users
  - [ ] Test MFA flow end-to-end

- [ ] **Password Hashing Upgrade** (2 hours)
  - [ ] Update bcrypt rounds to 12
  - [ ] Add password strength validator
  - [ ] Test registration and login

### Testing Each Pattern:

```bash
# Test IDOR fix
curl -H "Authorization: Bearer USER1_TOKEN" \
  http://localhost:8000/api/v1/recommendations/USER2_RECOMMENDATION_ID
# Should return 404, not 200

# Test error sanitization
curl -X POST http://localhost:8000/api/v1/invalid-endpoint
# Should return generic message, not stack trace

# Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -d '{"email":"test@example.com","password":"wrong"}'
done
# 6th request should return 429

# Test MFA encryption
python3 -c "
from infra_mind.core.encryption import encrypt_mfa_secret, decrypt_mfa_secret
encrypted = encrypt_mfa_secret('SECRETBASE32')
decrypted = decrypt_mfa_secret(encrypted)
assert decrypted == 'SECRETBASE32'
print('✅ MFA encryption working')
"
```

---

## 🚀 Deployment Steps

### 1. Generate Encryption Key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Set Environment Variable:
```bash
export MFA_ENCRYPTION_KEY="your-generated-key-here"
```

### 3. Run Migration (if MFA already in use):
```bash
python scripts/migrate_mfa_secrets.py
```

### 4. Deploy Code:
```bash
docker-compose restart api
```

### 5. Verify:
```bash
curl http://localhost:8000/health
# Should return 200 with healthy status
```

---

## 📊 Security Improvement Tracking

| Pattern | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| IDOR Prevention | P0 | 8h | HIGH | 🔴 TODO |
| Error Sanitization | P0 | 6h | HIGH | 🔴 TODO |
| MFA Encryption | P0 | 4h | CRITICAL | 🔴 TODO |
| Password Strength | P0 | 2h | MEDIUM | 🔴 TODO |
| Rate Limiting | P0 | 1h | HIGH | 🟢 DONE |

---

*Patterns Guide Created: November 4, 2025*
*Use these patterns consistently across all API endpoints*
