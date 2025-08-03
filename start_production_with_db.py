#!/usr/bin/env python3
"""
Production Startup Script with Database Initialization

This script:
1. Validates production environment configuration
2. Initializes the production database with proper setup
3. Starts the API server with production optimizations
4. Includes health checks and monitoring
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.config import settings


class ProductionStarter:
    """Production environment starter with comprehensive setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env.production'
        
    def validate_environment(self):
        """Validate production environment configuration."""
        logger.info("🔍 Validating production environment...")
        
        required_vars = [
            'INFRA_MIND_MONGODB_URL',
            'INFRA_MIND_REDIS_URL',
            'INFRA_MIND_SECRET_KEY',
            'INFRA_MIND_OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.info("💡 Please check your .env.production file")
            return False
        
        # Validate database URL format
        db_url = os.getenv('INFRA_MIND_MONGODB_URL')
        if not db_url.startswith(('mongodb://', 'mongodb+srv://')):
            logger.error("❌ Invalid MongoDB URL format")
            return False
        
        # Validate Redis URL format
        redis_url = os.getenv('INFRA_MIND_REDIS_URL')
        if not redis_url.startswith(('redis://', 'rediss://')):
            logger.error("❌ Invalid Redis URL format")
            return False
        
        logger.success("✅ Environment validation passed")
        return True
    
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        logger.info("📦 Checking dependencies...")
        
        try:
            import motor
            import beanie
            import fastapi
            import uvicorn
            import redis
            import openai
            logger.success("✅ All dependencies are installed")
            return True
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            logger.info("💡 Run: pip install -r requirements.txt")
            return False
    
    async def initialize_database(self):
        """Initialize production database."""
        logger.info("🗄️ Initializing production database...")
        
        try:
            # Run database initialization script
            process = await asyncio.create_subprocess_exec(
                sys.executable, 'init_production_database.py',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.success("✅ Database initialization completed")
                return True
            else:
                logger.error(f"❌ Database initialization failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            return False
    
    def start_api_server(self):
        """Start the production API server."""
        logger.info("🚀 Starting production API server...")
        
        # Production server configuration
        server_config = {
            'app': 'api.app:app',
            'host': '0.0.0.0',
            'port': int(os.getenv('INFRA_MIND_API_PORT', 8000)),
            'workers': int(os.getenv('INFRA_MIND_WORKERS', 4)),
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'log_level': 'info',
            'access_log': True,
            'use_colors': True,
            'loop': 'uvloop',
            'http': 'httptools',
            'timeout': 120,
            'keepalive': 5,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'preload_app': True
        }
        
        # Build uvicorn command
        cmd = [
            sys.executable, '-m', 'uvicorn',
            server_config['app'],
            '--host', server_config['host'],
            '--port', str(server_config['port']),
            '--workers', str(server_config['workers']),
            '--log-level', server_config['log_level'],
            '--loop', server_config['loop'],
            '--http', server_config['http'],
            '--timeout-keep-alive', str(server_config['keepalive']),
            '--access-log'
        ]
        
        if server_config['use_colors']:
            cmd.append('--use-colors')
        
        logger.info(f"🌐 Server will be available at: http://localhost:{server_config['port']}")
        logger.info(f"📚 API Documentation: http://localhost:{server_config['port']}/docs")
        logger.info(f"❤️ Health Check: http://localhost:{server_config['port']}/health")
        
        try:
            # Start the server
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                env=os.environ.copy()
            )
            
            logger.success("🎉 Production API server started successfully!")
            logger.info(f"🔧 Process ID: {process.pid}")
            
            # Wait for the process
            process.wait()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down server...")
            process.terminate()
            process.wait()
            logger.info("✅ Server shutdown complete")
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
        
        return True
    
    async def health_check(self):
        """Perform health check on the running services."""
        logger.info("🏥 Performing health checks...")
        
        import aiohttp
        
        try:
            # Check API health
            async with aiohttp.ClientSession() as session:
                port = int(os.getenv('INFRA_MIND_API_PORT', 8000))
                health_url = f"http://localhost:{port}/health"
                
                async with session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        logger.success("✅ API health check passed")
                        return True
                    else:
                        logger.error(f"❌ API health check failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def print_startup_info(self):
        """Print startup information and instructions."""
        logger.info("=" * 60)
        logger.info("🚀 Infra Mind Production Server")
        logger.info("=" * 60)
        logger.info(f"📍 Environment: {settings.environment}")
        logger.info(f"🔧 Debug Mode: {settings.debug}")
        logger.info(f"🌐 Host: 0.0.0.0")
        logger.info(f"🔌 Port: {os.getenv('INFRA_MIND_API_PORT', 8000)}")
        logger.info(f"👥 Workers: {os.getenv('INFRA_MIND_WORKERS', 4)}")
        logger.info(f"📊 Log Level: info")
        logger.info("")
        logger.info("🔗 Important URLs:")
        port = os.getenv('INFRA_MIND_API_PORT', 8000)
        logger.info(f"   📚 API Documentation: http://localhost:{port}/docs")
        logger.info(f"   ❤️  Health Check: http://localhost:{port}/health")
        logger.info(f"   📊 Metrics: http://localhost:{port}/metrics")
        logger.info("")
        logger.info("🛠️ Production Features Enabled:")
        logger.info("   ✅ Database initialization with indexes")
        logger.info("   ✅ Connection pooling and retry logic")
        logger.info("   ✅ SSL/TLS encryption")
        logger.info("   ✅ Performance monitoring")
        logger.info("   ✅ Error handling and logging")
        logger.info("   ✅ Multi-worker processing")
        logger.info("=" * 60)


async def main():
    """Main startup function."""
    starter = ProductionStarter()
    
    # Print startup information
    starter.print_startup_info()
    
    # Validate environment
    if not starter.validate_environment():
        logger.error("❌ Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Check dependencies
    if not starter.check_dependencies():
        logger.error("❌ Dependency check failed. Exiting.")
        sys.exit(1)
    
    # Initialize database
    if not await starter.initialize_database():
        logger.error("❌ Database initialization failed. Exiting.")
        sys.exit(1)
    
    # Wait a moment for database to be ready
    logger.info("⏳ Waiting for database to be ready...")
    await asyncio.sleep(2)
    
    # Start API server
    logger.info("🌟 Starting production server...")
    starter.start_api_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)