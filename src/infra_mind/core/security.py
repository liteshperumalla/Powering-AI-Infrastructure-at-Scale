"""
Security utilities and configuration for Infra Mind.

Provides security headers, input validation, and security monitoring.
"""

import re
import html
import secrets
import hashlib
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
import logging

from .audit import log_security_event, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom security error."""
    pass


class InputValidator:
    """
    Input validation and sanitization utilities.
    
    Learning Note: Input validation is the first line of defense
    against injection attacks and data corruption.
    """
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$')
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bOR\s+\d+\s*=\s*\d+)",
        r"(\'\s*(OR|AND)\s*\')",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_PATTERN.match(email.lower()))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        return bool(cls.PHONE_PATTERN.match(phone))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format and security."""
        if not url:
            return False
        
        # Check format
        if not cls.URL_PATTERN.match(url):
            return False
        
        # Parse URL for additional checks
        try:
            parsed = urlparse(url)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Block localhost and private IPs in production
            hostname = parsed.hostname
            if hostname:
                # Block obvious localhost variants
                if hostname.lower() in ['localhost', '127.0.0.1', '0.0.0.0']:
                    return False
                
                # Block private IP ranges (basic check)
                if hostname.startswith(('192.168.', '10.', '172.')):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """
        Check for SQL injection patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if suspicious patterns found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_xss(cls, text: str) -> bool:
        """
        Check for XSS patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if suspicious patterns found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def validate_and_sanitize_dict(cls, data: Dict[str, Any], schema: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Validate and sanitize dictionary data.
        
        Args:
            data: Input data dictionary
            schema: Validation schema with field rules
            
        Returns:
            Validated and sanitized data
            
        Raises:
            SecurityError: If validation fails
        """
        result = {}
        
        for field, value in data.items():
            if field not in schema:
                continue  # Skip unknown fields
            
            field_rules = schema[field]
            field_type = field_rules.get('type', 'string')
            required = field_rules.get('required', False)
            max_length = field_rules.get('max_length', 1000)
            
            # Check required fields
            if required and (value is None or value == ""):
                raise SecurityError(f"Required field '{field}' is missing")
            
            if value is None:
                result[field] = None
                continue
            
            # Type-specific validation
            if field_type == 'string':
                if not isinstance(value, str):
                    value = str(value)
                
                # Check for injection attacks
                if cls.check_sql_injection(value):
                    raise SecurityError(f"Suspicious SQL patterns detected in field '{field}'")
                
                if cls.check_xss(value):
                    raise SecurityError(f"Suspicious XSS patterns detected in field '{field}'")
                
                # Sanitize
                result[field] = cls.sanitize_string(value, max_length)
                
            elif field_type == 'email':
                if not cls.validate_email(value):
                    raise SecurityError(f"Invalid email format in field '{field}'")
                result[field] = value.lower().strip()
                
            elif field_type == 'url':
                if not cls.validate_url(value):
                    raise SecurityError(f"Invalid URL format in field '{field}'")
                result[field] = value.strip()
                
            elif field_type == 'integer':
                try:
                    result[field] = int(value)
                except (ValueError, TypeError):
                    raise SecurityError(f"Invalid integer value in field '{field}'")
                
            elif field_type == 'float':
                try:
                    result[field] = float(value)
                except (ValueError, TypeError):
                    raise SecurityError(f"Invalid float value in field '{field}'")
                
            elif field_type == 'boolean':
                if isinstance(value, bool):
                    result[field] = value
                elif isinstance(value, str):
                    result[field] = value.lower() in ['true', '1', 'yes', 'on']
                else:
                    result[field] = bool(value)
                
            else:
                result[field] = value
        
        return result


class SecurityHeaders:
    """
    Security headers management.
    
    Learning Note: Security headers help protect against common
    web vulnerabilities and should be applied to all responses.
    """
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            
            # HSTS (only for HTTPS)
            # "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }
    
    @staticmethod
    def get_cors_headers(origin: Optional[str] = None) -> Dict[str, str]:
        """Get CORS headers."""
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://yourdomain.com"
        ]
        
        headers = {
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400",
        }
        
        if origin and origin in allowed_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers


class RateLimiter:
    """
    Rate limiting utilities.
    
    Learning Note: Rate limiting helps prevent abuse and ensures
    fair resource usage. In production, use Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
    
    def is_rate_limited(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        current_time: Optional[float] = None
    ) -> bool:
        """
        Check if identifier is rate limited.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            current_time: Current timestamp (for testing)
            
        Returns:
            True if rate limited, False otherwise
        """
        import time
        
        if current_time is None:
            current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - window_seconds
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old timestamps
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff_time
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit:
            return True
        
        # Add current request
        self.requests[identifier].append(current_time)
        return False
    
    def get_rate_limit_info(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """Get rate limit information for identifier."""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        if identifier not in self.requests:
            return {
                "limit": limit,
                "remaining": limit,
                "reset_time": current_time + window_seconds,
                "window_seconds": window_seconds
            }
        
        # Clean old entries
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff_time
        ]
        
        current_count = len(self.requests[identifier])
        
        return {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset_time": current_time + window_seconds,
            "window_seconds": window_seconds
        }


class SecurityMonitor:
    """
    Security monitoring and threat detection.
    
    Learning Note: Automated security monitoring can help detect
    and respond to threats in real-time.
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.suspicious_ips = set()
        self.blocked_ips = set()
    
    def check_request_security(self, request: Request) -> Dict[str, Any]:
        """
        Perform security checks on incoming request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dictionary with security check results
        """
        results = {
            "safe": True,
            "warnings": [],
            "blocked": False,
            "ip_address": None
        }
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        results["ip_address"] = client_ip
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            results["safe"] = False
            results["blocked"] = True
            results["warnings"].append("IP address is blocked")
            return results
        
        # Check rate limiting
        if self.rate_limiter.is_rate_limited(client_ip, limit=100, window_seconds=60):
            results["safe"] = False
            results["warnings"].append("Rate limit exceeded")
            
            # Add to suspicious IPs
            self.suspicious_ips.add(client_ip)
        
        # Check for suspicious patterns in headers
        user_agent = request.headers.get("user-agent")
        if self.is_suspicious_user_agent(user_agent):
            results["warnings"].append("Suspicious user agent")
            self.suspicious_ips.add(client_ip)
        
        # Check for suspicious paths
        path = str(request.url.path)
        if self.is_suspicious_path(path):
            results["warnings"].append("Suspicious request path")
            self.suspicious_ips.add(client_ip)
        
        # Log security events
        if results["warnings"]:
            log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                ip_address=client_ip,
                details={
                    "warnings": results["warnings"],
                    "user_agent": user_agent,
                    "path": path
                },
                severity=AuditSeverity.HIGH if results["blocked"] else AuditSeverity.MEDIUM
            )
        
        return results
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (be careful with these in production)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (leftmost)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        if not user_agent:
            return True
        
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper",
            "curl", "wget", "python-requests",
            "sqlmap", "nikto", "nmap"
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    def is_suspicious_path(self, path: str) -> bool:
        """Check if request path is suspicious."""
        suspicious_patterns = [
            "admin", "wp-admin", "phpmyadmin",
            ".env", ".git", "config",
            "backup", "dump", "sql",
            "../", "..\\", "%2e%2e",
            "<script", "javascript:",
            "union", "select", "drop",
            "' or '", "' and '", "1=1", "1' or '1'='1"
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in suspicious_patterns)
    
    def block_ip(self, ip_address: str, reason: str) -> None:
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            ip_address=ip_address,
            details={"action": "ip_blocked", "reason": reason},
            severity=AuditSeverity.HIGH
        )
        
        logger.warning(f"Blocked IP address {ip_address}: {reason}")
    
    def unblock_ip(self, ip_address: str) -> None:
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        self.suspicious_ips.discard(ip_address)
        
        logger.info(f"Unblocked IP address {ip_address}")


# Global instances
input_validator = InputValidator()
security_monitor = SecurityMonitor()


# Utility functions
def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected: str) -> bool:
    """Verify CSRF token."""
    return secrets.compare_digest(token, expected)


def hash_ip_address(ip_address: str, salt: Optional[str] = None) -> str:
    """Hash IP address for privacy-preserving logging."""
    if salt is None:
        salt = "default_salt"  # In production, use a proper salt
    
    combined = f"{ip_address}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename or "unnamed_file"