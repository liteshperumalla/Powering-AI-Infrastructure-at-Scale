"""
Data encryption utilities for Infra Mind.

Provides AES-256 encryption for sensitive data at rest and utilities
for secure data handling.
"""

import os
import base64
import secrets
from datetime import datetime
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom encryption error."""
    pass


class DataEncryption:
    """
    AES-256 encryption for sensitive data.
    
    Learning Note: This class provides secure encryption/decryption
    for sensitive data like API keys, personal information, etc.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption with a key.
        
        Args:
            key: Encryption key (32 bytes for AES-256). If None, generates from environment.
        """
        if key:
            self.key = key
        else:
            # Get key from environment or generate
            key_b64 = os.getenv("ENCRYPTION_KEY")
            if key_b64:
                try:
                    self.key = base64.b64decode(key_b64)
                except Exception as e:
                    raise EncryptionError(f"Invalid encryption key in environment: {e}")
            else:
                # Generate a new key (in production, this should be stored securely)
                self.key = self._generate_key()
                logger.warning("Generated new encryption key. Store this securely!")
        
        if len(self.key) != 32:
            raise EncryptionError("Encryption key must be 32 bytes for AES-256")
    
    @staticmethod
    def _generate_key() -> bytes:
        """Generate a new AES-256 key."""
        return secrets.token_bytes(32)
    
    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Generate encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generates if None)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        return key, salt
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Base64-encoded encrypted data with IV prepended
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Generate random IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(iv),
                backend=default_backend()
            )
            
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine IV + auth_tag + ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            
            # Return base64 encoded
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data encrypted with encrypt().
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            # Decode from base64
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract components
            iv = data[:12]  # First 12 bytes
            tag = data[12:28]  # Next 16 bytes
            ciphertext = data[28:]  # Rest is ciphertext
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        result = data.copy()
        
        for field in fields_to_encrypt:
            if field in result and result[field] is not None:
                # Convert to string if not already
                value = str(result[field])
                result[field] = self.encrypt(value)
                # Mark field as encrypted
                result[f"{field}_encrypted"] = True
        
        return result
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        result = data.copy()
        
        for field in fields_to_decrypt:
            if field in result and result[field] is not None:
                # Check if field is marked as encrypted
                if result.get(f"{field}_encrypted", False):
                    result[field] = self.decrypt(result[field])
                    # Remove encryption marker
                    result.pop(f"{field}_encrypted", None)
        
        return result


class FernetEncryption:
    """
    Simpler Fernet encryption for less critical data.
    
    Learning Note: Fernet is easier to use but less flexible than AES-GCM.
    Good for simple encryption needs.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize Fernet encryption."""
        if key:
            self.fernet = Fernet(key)
        else:
            # Generate or get key from environment
            key_b64 = os.getenv("FERNET_KEY")
            if key_b64:
                self.fernet = Fernet(key_b64.encode())
            else:
                # Generate new key
                key = Fernet.generate_key()
                self.fernet = Fernet(key)
                logger.warning(f"Generated new Fernet key: {key.decode()}")
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data with Fernet."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self.fernet.encrypt(data)
        return encrypted.decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data with Fernet."""
        decrypted = self.fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted.decode('utf-8')


class SecureDataHandler:
    """
    Handler for secure data operations.
    
    Learning Note: This class provides high-level methods for handling
    sensitive data throughout the application.
    """
    
    def __init__(self):
        self.aes_encryption = DataEncryption()
        self.fernet_encryption = FernetEncryption()
    
    def encrypt_sensitive_fields(self, data: dict) -> dict:
        """
        Encrypt sensitive fields in user or assessment data.
        
        Args:
            data: Dictionary containing potentially sensitive data
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        # Define sensitive fields that should be encrypted
        sensitive_fields = [
            'api_key',
            'secret_key',
            'password_reset_token',
            'personal_notes',
            'company_confidential_info',
            'credit_card_number',
            'ssn',
            'phone_number'
        ]
        
        return self.aes_encryption.encrypt_dict(data, sensitive_fields)
    
    def decrypt_sensitive_fields(self, data: dict) -> dict:
        """
        Decrypt sensitive fields in user or assessment data.
        
        Args:
            data: Dictionary containing encrypted sensitive data
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        sensitive_fields = [
            'api_key',
            'secret_key',
            'password_reset_token',
            'personal_notes',
            'company_confidential_info',
            'credit_card_number',
            'ssn',
            'phone_number'
        ]
        
        return self.aes_encryption.decrypt_dict(data, sensitive_fields)
    
    def secure_compare(self, a: str, b: str) -> bool:
        """
        Timing-safe string comparison.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal, False otherwise
        """
        return secrets.compare_digest(a.encode(), b.encode())
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Hash sensitive data with salt.
        
        Args:
            data: Data to hash
            salt: Salt for hashing (generates if None)
            
        Returns:
            Tuple of (hash_b64, salt_b64)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(salt + data.encode())
        hash_bytes = digest.finalize()
        
        return (
            base64.b64encode(hash_bytes).decode(),
            base64.b64encode(salt).decode()
        )


# Global instances
data_encryption = DataEncryption()
secure_handler = SecureDataHandler()


def encrypt_data(data: Union[str, bytes]) -> str:
    """Convenience function for data encryption."""
    return data_encryption.encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Convenience function for data decryption."""
    return data_encryption.decrypt(encrypted_data)


def generate_encryption_key() -> str:
    """Generate a new encryption key for configuration."""
    key = DataEncryption._generate_key()
    return base64.b64encode(key).decode()


def generate_fernet_key() -> str:
    """Generate a new Fernet key for configuration."""
    return Fernet.generate_key().decode()


# Audit logging for encryption operations
class EncryptionAuditLogger:
    """
    Audit logger for encryption operations.
    
    Learning Note: Audit logging is crucial for security compliance
    and forensic analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("encryption_audit")
    
    def log_encryption(self, operation: str, data_type: str, user_id: Optional[str] = None):
        """Log encryption operation."""
        self.logger.info(
            f"ENCRYPTION_AUDIT: operation={operation}, data_type={data_type}, "
            f"user_id={user_id or 'system'}, timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_decryption(self, operation: str, data_type: str, user_id: Optional[str] = None):
        """Log decryption operation."""
        self.logger.info(
            f"DECRYPTION_AUDIT: operation={operation}, data_type={data_type}, "
            f"user_id={user_id or 'system'}, timestamp={datetime.utcnow().isoformat()}"
        )
    
    def log_key_operation(self, operation: str, key_type: str):
        """Log key management operation."""
        self.logger.warning(
            f"KEY_AUDIT: operation={operation}, key_type={key_type}, "
            f"timestamp={datetime.utcnow().isoformat()}"
        )


# Global audit logger
audit_logger = EncryptionAuditLogger()