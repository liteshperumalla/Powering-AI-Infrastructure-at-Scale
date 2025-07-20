"""
CLI interface for Infra Mind development and administration.

Provides useful commands for development, testing, and administration.
"""

import asyncio
from typing import Optional
import typer
from loguru import logger

from .core.config import settings
from .core.database import init_database, close_database, get_database_info
from .core.logging import setup_logging

app = typer.Typer(
    name="infra-mind",
    help="Infra Mind CLI for development and administration"
)


@app.command()
def info():
    """Display application information."""
    typer.echo(f"🚀 {settings.app_name} v{settings.app_version}")
    typer.echo(f"Environment: {settings.environment}")
    typer.echo(f"Debug mode: {settings.debug}")
    typer.echo(f"MongoDB URL: {settings.mongodb_url}")
    typer.echo(f"Redis URL: {settings.redis_url}")


@app.command()
def run(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
):
    """Run the FastAPI application."""
    import uvicorn
    
    typer.echo(f"🚀 Starting {settings.app_name} on {host}:{port}")
    
    uvicorn.run(
        "infra_mind.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if not settings.debug else "debug",
    )


@app.command()
def db_info():
    """Display database information."""
    async def _db_info():
        setup_logging()
        await init_database()
        
        info = await get_database_info()
        
        typer.echo("📊 Database Information:")
        for key, value in info.items():
            typer.echo(f"  {key}: {value}")
        
        await close_database()
    
    asyncio.run(_db_info())


@app.command()
def test_connection():
    """Test database and Redis connections."""
    async def _test_connection():
        setup_logging()
        
        try:
            # Test database connection
            typer.echo("🔌 Testing MongoDB connection...")
            await init_database()
            typer.echo("✅ MongoDB connection successful")
            
            # Test Redis connection (basic test)
            typer.echo("🔌 Testing Redis connection...")
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.ping()
            typer.echo("✅ Redis connection successful")
            await redis_client.close()
            
            await close_database()
            typer.echo("🎉 All connections successful!")
            
        except Exception as e:
            typer.echo(f"❌ Connection failed: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_test_connection())


@app.command()
def create_user(
    email: str = typer.Option(..., prompt=True, help="User email"),
    name: str = typer.Option(..., prompt=True, help="Full name"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password"),
    company: Optional[str] = typer.Option(None, help="Company name"),
):
    """Create a new user account."""
    async def _create_user():
        setup_logging()
        await init_database()
        
        from .models.user import User
        from passlib.context import CryptContext
        
        # Hash password
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
        
        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=name,
            company=company,
            is_active=True,
            is_verified=True,  # Auto-verify for CLI created users
        )
        
        try:
            await user.insert()
            typer.echo(f"✅ User created successfully: {email}")
        except Exception as e:
            typer.echo(f"❌ Failed to create user: {e}")
            raise typer.Exit(1)
        
        await close_database()
    
    asyncio.run(_create_user())


if __name__ == "__main__":
    app()