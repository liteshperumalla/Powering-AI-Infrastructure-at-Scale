"""
SSO (Single Sign-On) integration with enterprise identity providers.

Supports integration with popular enterprise identity providers including
Azure AD, Okta, Auth0, Google Workspace, and SAML-based providers.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
import aiohttp
import jwt
import json
import base64
from urllib.parse import urlencode, parse_qs, urlparse
import xml.etree.ElementTree as ET

from ..core.config import get_settings
# Simple cache implementation for integrations
class SimpleCache:
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str):
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        self._cache[key] = value
    
    async def delete(self, key: str):
        self._cache.pop(key, None)

simple_cache = SimpleCache()
from ..core.auth import TokenManager, AuthService
class APIError(Exception):
    """API error exception."""
    pass
from ..models.user import User

logger = logging.getLogger(__name__)


class SSOProvider(str, Enum):
    """Supported SSO providers."""
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    AUTH0 = "auth0"
    GOOGLE_WORKSPACE = "google_workspace"
    SAML_GENERIC = "saml_generic"
    OIDC_GENERIC = "oidc_generic"


class AuthenticationMethod(str, Enum):
    """Authentication methods."""
    OAUTH2 = "oauth2"
    SAML2 = "saml2"
    OIDC = "oidc"


@dataclass
class SSOConfiguration:
    """SSO provider configuration."""
    provider: SSOProvider
    client_id: str
    client_secret: str
    auth_method: AuthenticationMethod
    authorization_url: str
    token_url: str
    userinfo_url: Optional[str] = None
    jwks_url: Optional[str] = None
    issuer: Optional[str] = None
    scopes: List[str] = None
    redirect_uri: Optional[str] = None
    metadata_url: Optional[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["openid", "profile", "email"]


@dataclass
class SSOUser:
    """User information from SSO provider."""
    provider: SSOProvider
    provider_user_id: str
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    groups: List[str] = None
    roles: List[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.roles is None:
            self.roles = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AuthorizationRequest:
    """OAuth2/OIDC authorization request."""
    provider: SSOProvider
    state: str
    nonce: str
    redirect_uri: str
    authorization_url: str
    expires_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "state": self.state,
            "nonce": self.nonce,
            "redirect_uri": self.redirect_uri,
            "authorization_url": self.authorization_url,
            "expires_at": self.expires_at.isoformat()
        }


class SSOProviderIntegrator:
    """
    SSO provider integrator for enterprise identity providers.
    
    Supports OAuth2, OIDC, and SAML-based authentication with
    popular enterprise identity providers.
    """
    
    def __init__(self):
        """Initialize SSO provider integrator."""
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize provider configurations
        self.providers = self._initialize_providers()
        
        # Cache for authorization requests and tokens
        self.auth_cache_ttl = 600  # 10 minutes
        
        logger.info("SSO Provider Integrator initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "InfraMind-SSOIntegrator/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _initialize_providers(self) -> Dict[SSOProvider, SSOConfiguration]:
        """Initialize SSO provider configurations."""
        providers = {}
        
        # Azure AD configuration
        if getattr(self.settings, "AZURE_AD_CLIENT_ID", None):
            tenant_id = getattr(self.settings, "AZURE_AD_TENANT_ID", "common")
            providers[SSOProvider.AZURE_AD] = SSOConfiguration(
                provider=SSOProvider.AZURE_AD,
                client_id=getattr(self.settings, "AZURE_AD_CLIENT_ID", None),
                client_secret=getattr(self.settings, "AZURE_AD_CLIENT_SECRET", None),
                auth_method=AuthenticationMethod.OIDC,
                authorization_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                userinfo_url="https://graph.microsoft.com/v1.0/me",
                jwks_url=f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
                issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                scopes=["openid", "profile", "email", "User.Read"],
                enabled=getattr(self.settings, "ENABLE_AZURE_AD_SSO", False)
            )
        
        # Okta configuration
        if getattr(self.settings, "OKTA_CLIENT_ID", None):
            okta_domain = getattr(self.settings, "OKTA_DOMAIN", None)
            providers[SSOProvider.OKTA] = SSOConfiguration(
                provider=SSOProvider.OKTA,
                client_id=getattr(self.settings, "OKTA_CLIENT_ID", None),
                client_secret=getattr(self.settings, "OKTA_CLIENT_SECRET", None),
                auth_method=AuthenticationMethod.OIDC,
                authorization_url=f"https://{okta_domain}/oauth2/default/v1/authorize",
                token_url=f"https://{okta_domain}/oauth2/default/v1/token",
                userinfo_url=f"https://{okta_domain}/oauth2/default/v1/userinfo",
                jwks_url=f"https://{okta_domain}/oauth2/default/v1/keys",
                issuer=f"https://{okta_domain}/oauth2/default",
                enabled=getattr(self.settings, "ENABLE_OKTA_SSO", False)
            )
        
        # Auth0 configuration
        if getattr(self.settings, "AUTH0_CLIENT_ID", None):
            auth0_domain = getattr(self.settings, "AUTH0_DOMAIN", None)
            providers[SSOProvider.AUTH0] = SSOConfiguration(
                provider=SSOProvider.AUTH0,
                client_id=getattr(self.settings, "AUTH0_CLIENT_ID", None),
                client_secret=getattr(self.settings, "AUTH0_CLIENT_SECRET", None),
                auth_method=AuthenticationMethod.OIDC,
                authorization_url=f"https://{auth0_domain}/authorize",
                token_url=f"https://{auth0_domain}/oauth/token",
                userinfo_url=f"https://{auth0_domain}/userinfo",
                jwks_url=f"https://{auth0_domain}/.well-known/jwks.json",
                issuer=f"https://{auth0_domain}/",
                enabled=getattr(self.settings, "ENABLE_AUTH0_SSO", False)
            )
        
        # Google Workspace configuration
        if getattr(self.settings, "GOOGLE_CLIENT_ID", None):
            providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
                provider=SSOProvider.GOOGLE_WORKSPACE,
                client_id=getattr(self.settings, "GOOGLE_CLIENT_ID", None),
                client_secret=getattr(self.settings, "GOOGLE_CLIENT_SECRET", None),
                auth_method=AuthenticationMethod.OIDC,
                authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
                jwks_url="https://www.googleapis.com/oauth2/v3/certs",
                issuer="https://accounts.google.com",
                scopes=["openid", "profile", "email"],
                enabled=getattr(self.settings, "ENABLE_GOOGLE_SSO", False)
            )
        
        return providers
    
    # Authorization Flow Methods
    
    async def initiate_authorization(self, 
                                   provider: SSOProvider,
                                   redirect_uri: str,
                                   state: Optional[str] = None) -> AuthorizationRequest:
        """Initiate OAuth2/OIDC authorization flow."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} not configured")
        
        config = self.providers[provider]
        if not config.enabled:
            raise ValueError(f"Provider {provider.value} is disabled")
        
        # Generate state and nonce for security
        import secrets
        if not state:
            state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            "client_id": config.client_id,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce
        }
        
        # Provider-specific parameters
        if provider == SSOProvider.AZURE_AD:
            auth_params["response_mode"] = "query"
        elif provider == SSOProvider.OKTA:
            auth_params["prompt"] = "login"
        
        authorization_url = f"{config.authorization_url}?{urlencode(auth_params)}"
        
        # Create authorization request
        auth_request = AuthorizationRequest(
            provider=provider,
            state=state,
            nonce=nonce,
            redirect_uri=redirect_uri,
            authorization_url=authorization_url,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        
        # Cache the request for validation
        await simple_cache.set(
            f"sso_auth_request_{state}",
            auth_request.to_dict(),
            ttl=self.auth_cache_ttl
        )
        
        logger.info(f"Initiated authorization for provider {provider.value}")
        return auth_request
    
    async def handle_authorization_callback(self,
                                          provider: SSOProvider,
                                          authorization_code: str,
                                          state: str,
                                          redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth2/OIDC authorization callback."""
        # Validate state parameter
        cached_request = await simple_cache.get(f"sso_auth_request_{state}")
        if not cached_request:
            raise ValueError("Invalid or expired authorization request")
        
        auth_request = AuthorizationRequest(**cached_request)
        if auth_request.provider != provider:
            raise ValueError("Provider mismatch in authorization callback")
        
        # Exchange authorization code for tokens
        tokens = await self._exchange_authorization_code(
            provider, authorization_code, redirect_uri
        )
        
        # Get user information
        sso_user = await self._get_user_info(provider, tokens["access_token"])
        
        # Create or update local user
        local_user = await self._create_or_update_user(sso_user)
        
        # Generate local tokens
        local_tokens = AuthService.create_tokens_for_user(local_user)
        
        # Clean up authorization request cache
        await simple_cache.delete(f"sso_auth_request_{state}")
        
        result = {
            "success": True,
            "user": {
                "id": str(local_user.id),
                "email": local_user.email,
                "full_name": local_user.full_name,
                "sso_provider": provider.value
            },
            "tokens": local_tokens,
            "sso_user_info": asdict(sso_user)
        }
        
        logger.info(f"Successfully authenticated user {sso_user.email} via {provider.value}")
        return result
    
    async def _exchange_authorization_code(self,
                                         provider: SSOProvider,
                                         authorization_code: str,
                                         redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        config = self.providers[provider]
        
        token_data = {
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with self.session.post(
            config.token_url,
            data=token_data,
            headers=headers
        ) as response:
            if response.status == 200:
                tokens = await response.json()
                return tokens
            else:
                error_text = await response.text()
                logger.error(f"Token exchange failed for {provider.value}: {error_text}")
                raise APIError(f"Token exchange failed: {error_text}")
    
    async def _get_user_info(self, provider: SSOProvider, access_token: str) -> SSOUser:
        """Get user information from SSO provider."""
        config = self.providers[provider]
        
        if not config.userinfo_url:
            raise ValueError(f"No userinfo URL configured for {provider.value}")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with self.session.get(config.userinfo_url, headers=headers) as response:
            if response.status == 200:
                user_data = await response.json()
                return self._parse_user_info(provider, user_data)
            else:
                error_text = await response.text()
                logger.error(f"Failed to get user info from {provider.value}: {error_text}")
                raise APIError(f"Failed to get user info: {error_text}")
    
    def _parse_user_info(self, provider: SSOProvider, user_data: Dict[str, Any]) -> SSOUser:
        """Parse user information from provider-specific format."""
        if provider == SSOProvider.AZURE_AD:
            return SSOUser(
                provider=provider,
                provider_user_id=user_data.get("id", ""),
                email=user_data.get("mail") or user_data.get("userPrincipalName", ""),
                full_name=user_data.get("displayName", ""),
                first_name=user_data.get("givenName"),
                last_name=user_data.get("surname"),
                job_title=user_data.get("jobTitle"),
                department=user_data.get("department"),
                company=user_data.get("companyName"),
                metadata=user_data
            )
        
        elif provider == SSOProvider.OKTA:
            return SSOUser(
                provider=provider,
                provider_user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                full_name=user_data.get("name", ""),
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
                groups=user_data.get("groups", []),
                metadata=user_data
            )
        
        elif provider == SSOProvider.AUTH0:
            return SSOUser(
                provider=provider,
                provider_user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                full_name=user_data.get("name", ""),
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
                avatar_url=user_data.get("picture"),
                metadata=user_data
            )
        
        elif provider == SSOProvider.GOOGLE_WORKSPACE:
            return SSOUser(
                provider=provider,
                provider_user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                full_name=user_data.get("name", ""),
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
                avatar_url=user_data.get("picture"),
                metadata=user_data
            )
        
        else:
            # Generic OIDC parsing
            return SSOUser(
                provider=provider,
                provider_user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                full_name=user_data.get("name", ""),
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
                metadata=user_data
            )
    
    async def _create_or_update_user(self, sso_user: SSOUser) -> User:
        """Create or update local user from SSO user information."""
        # Try to find existing user by email
        existing_user = await User.find_one(User.email == sso_user.email.lower())
        
        if existing_user:
            # Update existing user with SSO information
            existing_user.full_name = sso_user.full_name or existing_user.full_name
            existing_user.sso_provider = sso_user.provider.value
            existing_user.sso_user_id = sso_user.provider_user_id
            existing_user.job_title = sso_user.job_title or existing_user.job_title
            existing_user.company_name = sso_user.company or existing_user.company_name
            existing_user.last_login = datetime.now(timezone.utc)
            existing_user.is_active = True
            
            await existing_user.save()
            return existing_user
        
        else:
            # Create new user
            new_user = User(
                email=sso_user.email.lower(),
                full_name=sso_user.full_name,
                sso_provider=sso_user.provider.value,
                sso_user_id=sso_user.provider_user_id,
                job_title=sso_user.job_title,
                company_name=sso_user.company,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc),
                # SSO users don't need password
                hashed_password=""
            )
            
            await new_user.insert()
            return new_user
    
    # Token Validation Methods
    
    async def validate_jwt_token(self, provider: SSOProvider, token: str) -> Dict[str, Any]:
        """Validate JWT token from SSO provider."""
        config = self.providers.get(provider)
        if not config or not config.jwks_url:
            raise ValueError(f"JWKS URL not configured for {provider.value}")
        
        # Get JWKS (JSON Web Key Set)
        jwks = await self._get_jwks(provider)
        
        # Decode and validate token
        try:
            # Get token header to find key ID
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            # Find matching key
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break
            
            if not key:
                raise ValueError("No matching key found in JWKS")
            
            # Validate token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=config.issuer,
                audience=config.client_id
            )
            
            return {
                "valid": True,
                "payload": payload,
                "provider": provider.value
            }
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token from {provider.value}: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "provider": provider.value
            }
    
    async def _get_jwks(self, provider: SSOProvider) -> Dict[str, Any]:
        """Get JSON Web Key Set from provider."""
        config = self.providers[provider]
        cache_key = f"jwks_{provider.value}"
        
        # Check cache first
        cached_jwks = await simple_cache.get(cache_key)
        if cached_jwks:
            return cached_jwks
        
        # Fetch from provider
        async with self.session.get(config.jwks_url) as response:
            if response.status == 200:
                jwks = await response.json()
                
                # Cache for 1 hour
                await simple_cache.set(cache_key, jwks, ttl=3600)
                
                return jwks
            else:
                error_text = await response.text()
                logger.error(f"Failed to fetch JWKS from {provider.value}: {error_text}")
                raise APIError(f"Failed to fetch JWKS: {error_text}")
    
    # Provider Management Methods
    
    def get_enabled_providers(self) -> List[SSOProvider]:
        """Get list of enabled SSO providers."""
        return [
            provider for provider, config in self.providers.items()
            if config.enabled
        ]
    
    def get_provider_config(self, provider: SSOProvider) -> Optional[SSOConfiguration]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider)
    
    async def test_provider_connection(self, provider: SSOProvider) -> Dict[str, Any]:
        """Test connection to SSO provider."""
        config = self.providers.get(provider)
        if not config:
            return {
                "provider": provider.value,
                "configured": False,
                "enabled": False,
                "error": "Provider not configured"
            }
        
        test_result = {
            "provider": provider.value,
            "configured": True,
            "enabled": config.enabled,
            "endpoints": {
                "authorization_url": config.authorization_url,
                "token_url": config.token_url,
                "userinfo_url": config.userinfo_url,
                "jwks_url": config.jwks_url
            }
        }
        
        if not config.enabled:
            test_result["error"] = "Provider disabled"
            return test_result
        
        # Test JWKS endpoint if available
        if config.jwks_url:
            try:
                async with self.session.get(config.jwks_url) as response:
                    if response.status == 200:
                        test_result["jwks_accessible"] = True
                    else:
                        test_result["jwks_accessible"] = False
                        test_result["jwks_error"] = f"HTTP {response.status}"
            except Exception as e:
                test_result["jwks_accessible"] = False
                test_result["jwks_error"] = str(e)
        
        return test_result
    
    # Logout and Session Management
    
    async def initiate_logout(self, provider: SSOProvider, user_id: str) -> Dict[str, Any]:
        """Initiate logout from SSO provider."""
        config = self.providers.get(provider)
        if not config:
            return {"success": False, "error": "Provider not configured"}
        
        # Provider-specific logout URLs
        logout_urls = {
            SSOProvider.AZURE_AD: f"https://login.microsoftonline.com/common/oauth2/v2.0/logout",
            SSOProvider.OKTA: f"https://{getattr(self.settings, 'OKTA_DOMAIN', 'example.okta.com')}/oauth2/default/v1/logout",
            SSOProvider.AUTH0: f"https://{getattr(self.settings, 'AUTH0_DOMAIN', 'example.auth0.com')}/v2/logout",
            SSOProvider.GOOGLE_WORKSPACE: "https://accounts.google.com/logout"
        }
        
        logout_url = logout_urls.get(provider)
        if logout_url:
            return {
                "success": True,
                "logout_url": logout_url,
                "provider": provider.value
            }
        else:
            return {
                "success": False,
                "error": "Logout URL not configured for provider"
            }


# Global integrator instance
sso_integrator = SSOProviderIntegrator()


# Convenience functions

async def initiate_sso_login(provider: SSOProvider, redirect_uri: str) -> AuthorizationRequest:
    """Initiate SSO login flow."""
    async with sso_integrator as integrator:
        return await integrator.initiate_authorization(provider, redirect_uri)


async def handle_sso_callback(provider: SSOProvider,
                            authorization_code: str,
                            state: str,
                            redirect_uri: str) -> Dict[str, Any]:
    """Handle SSO callback and create user session."""
    async with sso_integrator as integrator:
        return await integrator.handle_authorization_callback(
            provider, authorization_code, state, redirect_uri
        )


async def get_available_sso_providers() -> List[Dict[str, Any]]:
    """Get list of available SSO providers."""
    enabled_providers = sso_integrator.get_enabled_providers()
    
    provider_info = []
    for provider in enabled_providers:
        config = sso_integrator.get_provider_config(provider)
        provider_info.append({
            "provider": provider.value,
            "name": provider.value.replace("_", " ").title(),
            "enabled": config.enabled if config else False
        })
    
    return provider_info


async def test_sso_providers() -> Dict[str, Any]:
    """Test all configured SSO providers."""
    async with sso_integrator as integrator:
        test_results = {}
        
        for provider in integrator.providers.keys():
            test_results[provider.value] = await integrator.test_provider_connection(provider)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers": test_results
        }