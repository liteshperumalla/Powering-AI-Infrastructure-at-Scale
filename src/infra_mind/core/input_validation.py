"""
Production-grade input validation and sanitization for Infra Mind.

Provides comprehensive input validation, sanitization, and security
measures for all user inputs and API endpoints.
"""

import re
import html
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime
from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, validator, Field
import bleach
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error."""
    pass


class SanitizationConfig:
    """Configuration for input sanitization."""
    
    # Allowed HTML tags and attributes for rich text
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
    ]
    
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    # Maximum lengths for different field types
    MAX_LENGTHS = {
        'email': 254,
        'name': 100,
        'company': 200,
        'job_title': 100,
        'description': 2000,
        'notes': 5000,
        'url': 2048,
        'phone': 20,
        'address': 500
    }
    
    # Regex patterns for validation
    PATTERNS = {
        'name': r'^[a-zA-Z\s\-\'\.]{2,100}$',
        'username': r'^[a-zA-Z0-9_\-\.]{3,50}$',
        'phone': r'^\+?[\d\s\-\(\)]{10,20}$',
        'postal_code': r'^[a-zA-Z0-9\s\-]{3,10}$',
        'slug': r'^[a-z0-9\-]{3,50}$',
        'hex_color': r'^#[0-9a-fA-F]{6}$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    }


class InputSanitizer:
    """
    Comprehensive input sanitization utilities.
    """
    
    @staticmethod
    def sanitize_string(
        text: str, 
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """
        Sanitize string input with comprehensive cleaning.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            strip_whitespace: Whether to strip leading/trailing whitespace
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Strip whitespace if requested
        if strip_whitespace:
            text = text.strip()
        
        # Remove null bytes and control characters (except newlines and tabs)
        text = ''.join(
            char for char in text 
            if ord(char) >= 32 or char in '\t\n\r'
        )
        
        # SQL injection prevention - remove dangerous SQL patterns
        sql_patterns = [
            (r'union\s+select', 'UNION_SELECT_REMOVED'),
            (r'drop\s+table', 'DROP_TABLE_REMOVED'),
            (r'insert\s+into', 'INSERT_INTO_REMOVED'),
            (r'delete\s+from', 'DELETE_FROM_REMOVED'),
            (r'update\s+\w+\s+set', 'UPDATE_SET_REMOVED'),
            (r'alter\s+table', 'ALTER_TABLE_REMOVED'),
            (r'create\s+table', 'CREATE_TABLE_REMOVED'),
            (r'exec\s*\(', 'EXEC_REMOVED'),
            (r'execute\s*\(', 'EXECUTE_REMOVED'),
            (r'sp_\w+', 'STORED_PROC_REMOVED'),
            (r'xp_\w+', 'EXTENDED_PROC_REMOVED'),
            (r'\'\s*;\s*--', 'SQL_COMMENT_REMOVED'),
            (r'\'\s*or\s+\d+\s*=\s*\d+', 'SQL_BOOLEAN_REMOVED'),
        ]
        
        for pattern, replacement in sql_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Handle HTML content
        if allow_html:
            # Use bleach to clean HTML
            text = bleach.clean(
                text,
                tags=SanitizationConfig.ALLOWED_TAGS,
                attributes=SanitizationConfig.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape HTML entities
            text = html.escape(text)
        
        # Truncate if too long
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize and validate email address.
        
        Args:
            email: Email address to sanitize
            
        Returns:
            Sanitized email address
            
        Raises:
            ValidationError: If email is invalid
        """
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        
        email = email.strip().lower()
        
        try:
            # Use email-validator for comprehensive validation
            # Allow test domains for development/testing
            valid = validate_email(email, check_deliverability=False)
            return valid.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}")
    
    @staticmethod
    def sanitize_url(url: str, allowed_schemes: Set[str] = None) -> str:
        """
        Sanitize and validate URL.
        
        Args:
            url: URL to sanitize
            allowed_schemes: Set of allowed URL schemes
            
        Returns:
            Sanitized URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")
        
        if allowed_schemes is None:
            allowed_schemes = {'http', 'https'}
        
        url = url.strip()
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                raise ValidationError("URL must include a scheme (http/https)")
            
            if parsed.scheme.lower() not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
            
            if not parsed.netloc:
                raise ValidationError("URL must include a domain")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'javascript:', 'data:', 'vbscript:', 'file:', 'ftp:'
            ]
            
            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    raise ValidationError(f"URL contains suspicious pattern: {pattern}")
            
            return url
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Invalid URL format: {str(e)}")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_file'
        
        # Limit length (keeping extension)
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_length] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def sanitize_json(data: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
        """
        Recursively sanitize JSON data.
        
        Args:
            data: JSON data to sanitize
            max_depth: Maximum nesting depth
            current_depth: Current nesting level
            
        Returns:
            Sanitized JSON data
            
        Raises:
            ValidationError: If data exceeds maximum depth
        """
        if current_depth > max_depth:
            raise ValidationError(f"JSON depth exceeds maximum of {max_depth}")
        
        if isinstance(data, dict):
            return {
                InputSanitizer.sanitize_string(str(key)): 
                InputSanitizer.sanitize_json(value, max_depth, current_depth + 1)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                InputSanitizer.sanitize_json(item, max_depth, current_depth + 1)
                for item in data
            ]
        elif isinstance(data, str):
            return InputSanitizer.sanitize_string(data)
        else:
            return data


class InputValidator:
    """
    Comprehensive input validation utilities.
    """
    
    @staticmethod
    def validate_string_pattern(text: str, pattern_name: str) -> bool:
        """
        Validate string against predefined patterns.
        
        Args:
            text: Text to validate
            pattern_name: Name of pattern to use
            
        Returns:
            True if text matches pattern
        """
        if pattern_name not in SanitizationConfig.PATTERNS:
            raise ValidationError(f"Unknown pattern: {pattern_name}")
        
        pattern = SanitizationConfig.PATTERNS[pattern_name]
        return bool(re.match(pattern, text))
    
    @staticmethod
    def validate_length(text: str, field_type: str) -> bool:
        """
        Validate string length against field type limits.
        
        Args:
            text: Text to validate
            field_type: Type of field
            
        Returns:
            True if length is acceptable
        """
        if field_type not in SanitizationConfig.MAX_LENGTHS:
            return True  # No limit defined
        
        max_length = SanitizationConfig.MAX_LENGTHS[field_type]
        return len(text) <= max_length
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        Validate IP address format.
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid IP address
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_date_range(date_str: str, min_date: Optional[datetime] = None, max_date: Optional[datetime] = None) -> bool:
        """
        Validate date string and range.
        
        Args:
            date_str: Date string in ISO format
            min_date: Minimum allowed date
            max_date: Maximum allowed date
            
        Returns:
            True if date is valid and in range
        """
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            if min_date and date < min_date:
                return False
            
            if max_date and date > max_date:
                return False
            
            return True
            
        except ValueError:
            return False
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], required_fields: List[str], optional_fields: List[str] = None) -> tuple[bool, List[str]]:
        """
        Validate JSON data against a simple schema.
        
        Args:
            data: JSON data to validate
            required_fields: List of required field names
            optional_fields: List of optional field names
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(data, dict):
            return False, ["Data must be a JSON object"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None:
                errors.append(f"Required field cannot be null: {field}")
        
        # Check for unexpected fields
        allowed_fields = set(required_fields)
        if optional_fields:
            allowed_fields.update(optional_fields)
        
        for field in data.keys():
            if field not in allowed_fields:
                errors.append(f"Unexpected field: {field}")
        
        return len(errors) == 0, errors


class SecureInputProcessor:
    """
    High-level secure input processing for API endpoints.
    """
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.validator = InputValidator()
    
    def process_user_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user input data with comprehensive validation and sanitization.
        
        Args:
            data: Raw input data
            
        Returns:
            Processed and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        processed = {}
        
        for key, value in data.items():
            if value is None:
                processed[key] = None
                continue
            
            # Process based on field name/type
            if key in ['email', 'user_email', 'contact_email']:
                processed[key] = self.sanitizer.sanitize_email(value)
            
            elif key in ['url', 'website', 'homepage']:
                processed[key] = self.sanitizer.sanitize_url(value)
            
            elif key in ['name', 'full_name', 'first_name', 'last_name']:
                processed[key] = self.sanitizer.sanitize_string(
                    value, 
                    max_length=SanitizationConfig.MAX_LENGTHS['name']
                )
                if not self.validator.validate_string_pattern(processed[key], 'name'):
                    raise ValidationError(f"Invalid name format: {key}")
            
            elif key in ['company', 'company_name', 'organization']:
                processed[key] = self.sanitizer.sanitize_string(
                    value,
                    max_length=SanitizationConfig.MAX_LENGTHS['company']
                )
            
            elif key in ['job_title', 'title', 'position']:
                processed[key] = self.sanitizer.sanitize_string(
                    value,
                    max_length=SanitizationConfig.MAX_LENGTHS['job_title']
                )
            
            elif key in ['description', 'summary', 'overview']:
                processed[key] = self.sanitizer.sanitize_string(
                    value,
                    max_length=SanitizationConfig.MAX_LENGTHS['description'],
                    allow_html=True
                )
            
            elif key in ['notes', 'comments', 'remarks']:
                processed[key] = self.sanitizer.sanitize_string(
                    value,
                    max_length=SanitizationConfig.MAX_LENGTHS['notes'],
                    allow_html=True
                )
            
            elif key in ['phone', 'phone_number', 'mobile']:
                processed[key] = self.sanitizer.sanitize_string(
                    value,
                    max_length=SanitizationConfig.MAX_LENGTHS['phone']
                )
                if not self.validator.validate_string_pattern(processed[key], 'phone'):
                    raise ValidationError(f"Invalid phone number format: {key}")
            
            elif isinstance(value, str):
                # Default string processing
                processed[key] = self.sanitizer.sanitize_string(value)
            
            elif isinstance(value, (dict, list)):
                # Recursively process nested data
                processed[key] = self.sanitizer.sanitize_json(value)
            
            else:
                # Keep other types as-is
                processed[key] = value
        
        return processed
    
    def validate_assessment_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate assessment-specific data.
        
        Args:
            data: Assessment data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        required_fields = ['name', 'business_requirements']
        optional_fields = [
            'description', 'technical_requirements', 'compliance_requirements',
            'budget_range', 'timeline', 'priority'
        ]
        
        return self.validator.validate_json_schema(data, required_fields, optional_fields)
    
    def validate_user_registration(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate user registration data.
        
        Args:
            data: Registration data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        required_fields = ['email', 'password', 'full_name']
        optional_fields = ['company_name', 'job_title', 'phone']
        
        is_valid, errors = self.validator.validate_json_schema(data, required_fields, optional_fields)
        
        # Additional validation
        if 'email' in data:
            try:
                self.sanitizer.sanitize_email(data['email'])
            except ValidationError as e:
                errors.append(str(e))
                is_valid = False
        
        if 'password' in data:
            password = data['password']
            if len(password) < 8:
                errors.append("Password must be at least 8 characters long")
                is_valid = False
            if len(password) > 128:
                errors.append("Password must be no more than 128 characters long")
                is_valid = False
        
        return is_valid, errors


# Global processor instance
secure_processor = SecureInputProcessor()


# Pydantic validators for common use cases
def validate_email_field(v):
    """Pydantic validator for email fields."""
    if v is None:
        return v
    return InputSanitizer.sanitize_email(v)


def validate_name_field(v):
    """Pydantic validator for name fields."""
    if v is None:
        return v
    sanitized = InputSanitizer.sanitize_string(v, max_length=100)
    if not InputValidator.validate_string_pattern(sanitized, 'name'):
        raise ValueError("Invalid name format")
    return sanitized


def validate_url_field(v):
    """Pydantic validator for URL fields."""
    if v is None:
        return v
    return InputSanitizer.sanitize_url(v)


# Decorator for endpoint input validation
def validate_input(processor_method: str = 'process_user_input'):
    """
    Decorator for automatic input validation in API endpoints.
    
    Args:
        processor_method: Method name on SecureInputProcessor to use
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request data in kwargs
            for key, value in kwargs.items():
                if hasattr(value, '__dict__') and hasattr(value, 'dict'):
                    # Pydantic model
                    data = value.dict()
                    processor = SecureInputProcessor()
                    method = getattr(processor, processor_method)
                    
                    try:
                        processed_data = method(data)
                        # Update the model with processed data
                        for field, processed_value in processed_data.items():
                            if hasattr(value, field):
                                setattr(value, field, processed_value)
                    except ValidationError as e:
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Input validation failed: {str(e)}"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator