"""
Production-grade security middleware for Infra Mind.

Provides comprehensive security measures including:
- Security headers
- CORS policies
- Input validation and sanitization
- Rate limiting
- Request/response security
"""

import os
import re
import json
import time
import base64
import secrets
import hashlib
import hmac
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import logging

from .audit import log_security_event, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration settings."""
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "20"))
    
    # Request size limits
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
    MAX_JSON_DEPTH = int(os.getenv("MAX_JSON_DEPTH", "10"))
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
    }
    
    # CORS settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["*"]
    
    # Input validation patterns
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',               # XSS
        r'on\w+\s*=',                # Event handlers
        r'union\s+select',           # SQL injection
        r'drop\s+table',             # SQL injection
        r'insert\s+into',            # SQL injection
        r'delete\s+from',            # SQL injection
        r'update\s+\w+\s+set',       # SQL injection
        r'alter\s+table',            # SQL injection
        r'create\s+table',           # SQL injection
        r'exec\s*\(',                # SQL injection
        r'execute\s*\(',             # SQL injection
        r'sp_\w+',                   # SQL stored procedures
        r'xp_\w+',                   # SQL extended procedures
        r'\'\s*;\s*--',              # SQL comment injection
        r'\'\s*or\s+\d+\s*=\s*\d+', # SQL boolean injection
        r'\.\./\.\.',                # Path traversal
        r'file://',                  # File inclusion
        r'data:text/html',           # Data URI XSS
    ]


class RateLimiter:
    """
    Production-grade rate limiter with sliding window and burst protection.
    """
    
    def __init__(self):
        self.requests = defaultdict(list)  # IP -> list of timestamps
        self.blocked_ips = {}  # IP -> block_until_timestamp
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_ip: str, endpoint: str = None) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            client_ip: Client IP address
            endpoint: Optional endpoint for specific limits
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False, {
                    "reason": "ip_blocked",
                    "blocked_until": self.blocked_ips[client_ip]
                }
            else:
                # Unblock IP
                del self.blocked_ips[client_ip]
        
        # Get request history for this IP
        request_times = self.requests[client_ip]
        
        # Remove old requests outside the window
        window_start = now - SecurityConfig.RATE_LIMIT_WINDOW
        request_times[:] = [t for t in request_times if t > window_start]
        
        # Check rate limit
        if len(request_times) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            # Block IP for double the window time
            block_duration = SecurityConfig.RATE_LIMIT_WINDOW * 2
            self.blocked_ips[client_ip] = now + block_duration
            
            return False, {
                "reason": "rate_limit_exceeded",
                "requests_in_window": len(request_times),
                "window_seconds": SecurityConfig.RATE_LIMIT_WINDOW,
                "blocked_until": self.blocked_ips[client_ip]
            }
        
        # Check burst limit (requests in last 10 seconds)
        burst_window = now - 10
        recent_requests = [t for t in request_times if t > burst_window]
        
        if len(recent_requests) >= SecurityConfig.RATE_LIMIT_BURST:
            return False, {
                "reason": "burst_limit_exceeded",
                "recent_requests": len(recent_requests),
                "burst_limit": SecurityConfig.RATE_LIMIT_BURST
            }
        
        # Add current request
        request_times.append(now)
        
        return True, {
            "requests_in_window": len(request_times),
            "window_seconds": SecurityConfig.RATE_LIMIT_WINDOW
        }
    
    def _cleanup_old_entries(self, now: float) -> None:
        """Clean up old rate limit entries."""
        cutoff = now - SecurityConfig.RATE_LIMIT_WINDOW * 2
        
        # Clean up request histories
        for ip in list(self.requests.keys()):
            self.requests[ip][:] = [t for t in self.requests[ip] if t > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]
        
        # Clean up expired blocks
        for ip in list(self.blocked_ips.keys()):
            if now >= self.blocked_ips[ip]:
                del self.blocked_ips[ip]


class InputValidator:
    """
    Input validation and sanitization utilities.
    """
    
    @staticmethod
    def validate_json_depth(data: Any, max_depth: int = SecurityConfig.MAX_JSON_DEPTH, current_depth: int = 0) -> bool:
        """
        Validate JSON depth to prevent deeply nested attacks.
        
        Args:
            data: Data to validate
            max_depth: Maximum allowed depth
            current_depth: Current depth level
            
        Returns:
            True if depth is acceptable
        """
        if current_depth > max_depth:
            return False
        
        if isinstance(data, dict):
            return all(
                InputValidator.validate_json_depth(value, max_depth, current_depth + 1)
                for value in data.values()
            )
        elif isinstance(data, list):
            return all(
                InputValidator.validate_json_depth(item, max_depth, current_depth + 1)
                for item in data
            )
        
        return True
    
    @staticmethod
    def detect_suspicious_patterns(text: str) -> List[str]:
        """
        Detect suspicious patterns in input text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected suspicious patterns
        """
        if not isinstance(text, str):
            return []
        
        detected = []
        text_lower = text.lower()
        
        for pattern in SecurityConfig.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected.append(pattern)
        
        return detected
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)[:max_length]
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Basic HTML entity encoding for dangerous characters
        text = text.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        
        return text
    
    @staticmethod
    def validate_request_data(data: Any, client_ip: str) -> tuple[bool, List[str]]:
        """
        Comprehensive request data validation.
        
        Args:
            data: Request data to validate
            client_ip: Client IP for logging
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check JSON depth
        if not InputValidator.validate_json_depth(data):
            issues.append("JSON depth exceeds maximum allowed")
        
        # Check for suspicious patterns in string values
        def check_strings(obj, path=""):
            if isinstance(obj, str):
                suspicious = InputValidator.detect_suspicious_patterns(obj)
                if suspicious:
                    issues.append(f"Suspicious patterns detected at {path}: {suspicious}")
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_strings(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_strings(item, f"{path}[{i}]")
        
        check_strings(data)
        
        return len(issues) == 0, issues


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for production deployment.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.start_time = time.time()
        
        # Paths that bypass certain security checks
        self.health_check_paths = {"/health", "/ping", "/status"}
        self.public_paths = {"/docs", "/redoc", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # Skip security checks for health endpoints
            if request.url.path in self.health_check_paths:
                response = await call_next(request)
                return self._add_security_headers(response)
            
            # Rate limiting
            allowed, rate_info = self.rate_limiter.is_allowed(client_ip, request.url.path)
            if not allowed:
                log_security_event(
                    AuditEventType.SECURITY_VIOLATION,
                    ip_address=client_ip,
                    details={
                        "violation_type": "rate_limit",
                        "endpoint": str(request.url),
                        "rate_info": rate_info
                    },
                    severity=AuditSeverity.HIGH
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": rate_info.get("blocked_until", time.time() + 60) - time.time()
                    }
                )
            
            # Request size validation
            if hasattr(request, 'headers') and 'content-length' in request.headers:
                content_length = int(request.headers.get('content-length', 0))
                if content_length > SecurityConfig.MAX_REQUEST_SIZE:
                    log_security_event(
                        AuditEventType.SECURITY_VIOLATION,
                        ip_address=client_ip,
                        details={
                            "violation_type": "request_too_large",
                            "content_length": content_length,
                            "max_allowed": SecurityConfig.MAX_REQUEST_SIZE
                        },
                        severity=AuditSeverity.MEDIUM
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"error": "Request too large"}
                    )
            
            # Input validation for JSON requests
            if request.method in ["POST", "PUT", "PATCH"] and self._is_json_request(request):
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body)
                        is_valid, issues = InputValidator.validate_request_data(data, client_ip)
                        
                        if not is_valid:
                            log_security_event(
                                AuditEventType.SECURITY_VIOLATION,
                                ip_address=client_ip,
                                details={
                                    "violation_type": "malicious_input",
                                    "endpoint": str(request.url),
                                    "issues": issues
                                },
                                severity=AuditSeverity.HIGH
                            )
                            
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid input detected"}
                            )
                        
                        # Recreate request with validated body
                        request._body = body
                
                except json.JSONDecodeError:
                    # Let the application handle JSON decode errors
                    pass
                except Exception as e:
                    logger.error(f"Input validation error: {e}")
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log request metrics
            duration = time.time() - start_time
            if duration > 5.0:  # Log slow requests
                logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            
            # Log security error
            log_security_event(
                AuditEventType.ERROR_OCCURRED,
                ip_address=client_ip,
                details={
                    "error_type": "middleware_error",
                    "error": str(e),
                    "endpoint": str(request.url)
                },
                severity=AuditSeverity.HIGH
            )
            
            # Return generic error to avoid information disclosure
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support."""
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "CF-Connecting-IP",  # Cloudflare
            "X-Client-IP"
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                # Take the first IP in case of multiple
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _is_json_request(self, request: Request) -> bool:
        """Check if request contains JSON data."""
        content_type = request.headers.get("content-type", "")
        return "application/json" in content_type.lower()
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Add custom headers
        response.headers["X-Request-ID"] = hashlib.md5(
            f"{time.time()}{secrets.token_hex(8)}".encode()
        ).hexdigest()[:16]
        
        return response


class CSRFProtection:
    """
    CSRF protection utilities.
    """
    
    @staticmethod
    def generate_csrf_token(session_id: str, secret_key: str) -> str:
        """
        Generate CSRF token for a session.
        
        Args:
            session_id: Session identifier
            secret_key: Secret key for HMAC
            
        Returns:
            CSRF token
        """
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token = f"{timestamp}:{signature}"
        return base64.b64encode(token.encode()).decode()
    
    @staticmethod
    def validate_csrf_token(token: str, session_id: str, secret_key: str, max_age: int = 3600) -> bool:
        """
        Validate CSRF token.
        
        Args:
            token: CSRF token to validate
            session_id: Session identifier
            secret_key: Secret key for HMAC
            max_age: Maximum token age in seconds
            
        Returns:
            True if token is valid
        """
        try:
            decoded = base64.b64decode(token.encode()).decode()
            timestamp_str, signature = decoded.split(':', 1)
            timestamp = int(timestamp_str)
            
            # Check token age
            if time.time() - timestamp > max_age:
                return False
            
            # Verify signature
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False


def setup_cors_middleware(app, allowed_origins: List[str] = None):
    """
    Set up CORS middleware with secure defaults.
    
    Args:
        app: FastAPI application
        allowed_origins: List of allowed origins
    """
    if allowed_origins is None:
        allowed_origins = SecurityConfig.ALLOWED_ORIGINS
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=SecurityConfig.ALLOWED_METHODS,
        allow_headers=SecurityConfig.ALLOWED_HEADERS,
        expose_headers=["X-Request-ID"],
        max_age=600  # 10 minutes
    )


def setup_security_middleware(app):
    """
    Set up comprehensive security middleware.
    
    Args:
        app: FastAPI application
    """
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Add CORS middleware
    setup_cors_middleware(app)
    
    logger.info("Security middleware configured")


# Security utilities
def generate_secure_filename(filename: str) -> str:
    """
    Generate a secure filename by removing dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_file_upload(file_content: bytes, allowed_types: Set[str], max_size: int = 10485760) -> tuple[bool, str]:
    """
    Validate uploaded file content.
    
    Args:
        file_content: File content bytes
        allowed_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if len(file_content) > max_size:
        return False, f"File too large. Maximum size: {max_size} bytes"
    
    # Basic file type detection (this is a simplified version)
    # In production, use python-magic or similar for proper MIME type detection
    if file_content.startswith(b'\x89PNG'):
        mime_type = 'image/png'
    elif file_content.startswith(b'\xff\xd8\xff'):
        mime_type = 'image/jpeg'
    elif file_content.startswith(b'%PDF'):
        mime_type = 'application/pdf'
    elif file_content.startswith(b'PK'):
        mime_type = 'application/zip'
    else:
        mime_type = 'application/octet-stream'
    
    if mime_type not in allowed_types:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
    
    return True, ""