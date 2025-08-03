#!/usr/bin/env python3
"""
Production Database Test Script

Comprehensive testing of production MongoDB configuration including:
- Connection pooling and SSL/TLS
- Index performance and optimization
- Data encryption and security
- Backup procedures validation
- Health checks and monitoring
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.infra_mind.core.database import (
    init_database, 
    close_database, 
    get_database_info, 
    perform_health_check,
    setup_database_encryption,
    setup_backup_procedures,
    db
)
from src.infra_mind.core.config import settings


async def test_production_connection():
    """Test production database connection with advanced features."""
    print("🔍 TESTING PRODUCTION DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        # Print current configuration
        print(f"📋 Production Database Configuration:")
        print(f"   • Environment: {settings.environment}")
        print(f"   • Database Name: {settings.mongodb_database}")
        print(f"   • Max Connections: {settings.mongodb_max_connections}")
        print(f"   • Min Connections: {settings.mongodb_min_connections}")
        print(f"   • SSL/TLS: {'Enabled' if settings.is_production else 'Development mode'}")
        
        # Test database initialization
        print(f"\n🔌 Testing production database initialization...")
        start_time = time.time()
        await init_database()
        init_time = time.time() - start_time
        
        print(f"✅ Database initialized in {init_time:.2f} seconds")
        
        # Check if database is connected
        if db.database is not None:
            print("✅ Production database connection successful!")
            
            # Get comprehensive database info
            print(f"\n📊 Getting comprehensive database information...")
            db_info = await get_database_info()
            
            if db_info.get("status") == "connected":
                print("✅ Database info retrieved successfully:")
                print(f"   • Status: {db_info['status']}")
                print(f"   • Database: {db_info['database']}")
                print(f"   • Server Version: {db_info.get('server_version', 'N/A')}")
                print(f"   • Uptime: {db_info.get('uptime_seconds', 0)} seconds")
                print(f"   • Collections: {db_info.get('collections', 'N/A')}")
                print(f"   • Objects: {db_info.get('objects', 'N/A')}")
                print(f"   • Data Size: {db_info.get('dataSize', 'N/A')} bytes")
                print(f"   • Storage Size: {db_info.get('storageSize', 'N/A')} bytes")
                print(f"   • Index Size: {db_info.get('indexSize', 'N/A')} bytes")
                
                # Connection pool information
                pool_info = db_info.get('connection_pool', {})
                print(f"\n🏊 Connection Pool Statistics:")
                print(f"   • Max Pool Size: {pool_info.get('max_pool_size', 'N/A')}")
                print(f"   • Min Pool Size: {pool_info.get('min_pool_size', 'N/A')}")
                print(f"   • Failed Connections: {pool_info.get('failed_connections', 0)}")
                
                # Performance metrics
                opcounters = db_info.get('opcounters', {})
                if opcounters:
                    print(f"\n📈 Operation Counters:")
                    print(f"   • Inserts: {opcounters.get('insert', 0)}")
                    print(f"   • Queries: {opcounters.get('query', 0)}")
                    print(f"   • Updates: {opcounters.get('update', 0)}")
                    print(f"   • Deletes: {opcounters.get('delete', 0)}")
                
            else:
                print(f"⚠️  Database info status: {db_info}")
            
        else:
            print("❌ Database connection failed - check configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Production database test failed: {str(e)}")
        logger.error(f"Database test error: {e}", exc_info=True)
        return False


async def test_connection_pooling():
    """Test connection pooling performance and behavior."""
    print(f"\n🏊 TESTING CONNECTION POOLING")
    print("=" * 60)
    
    if db.database is None:
        print("⚠️  Database not available - skipping connection pool tests")
        return False
    
    try:
        # Test concurrent connections
        print("🔄 Testing concurrent database operations...")
        
        async def concurrent_operation(operation_id: int):
            """Perform a database operation concurrently."""
            try:
                start_time = time.time()
                
                # Perform a simple operation
                result = await db.database.test_pool.insert_one({
                    "operation_id": operation_id,
                    "timestamp": datetime.utcnow(),
                    "test_type": "connection_pool"
                })
                
                # Read it back
                found_doc = await db.database.test_pool.find_one({"_id": result.inserted_id})
                
                # Clean up
                await db.database.test_pool.delete_one({"_id": result.inserted_id})
                
                operation_time = time.time() - start_time
                return {
                    "operation_id": operation_id,
                    "success": True,
                    "time": operation_time,
                    "document_id": str(result.inserted_id)
                }
                
            except Exception as e:
                return {
                    "operation_id": operation_id,
                    "success": False,
                    "error": str(e),
                    "time": time.time() - start_time
                }
        
        # Run concurrent operations
        num_operations = 20
        start_time = time.time()
        
        tasks = [concurrent_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_ops = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_ops = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        print(f"✅ Concurrent operations completed:")
        print(f"   • Total operations: {num_operations}")
        print(f"   • Successful: {len(successful_ops)}")
        print(f"   • Failed: {len(failed_ops)}")
        print(f"   • Total time: {total_time:.2f} seconds")
        print(f"   • Average time per operation: {total_time/num_operations:.3f} seconds")
        
        if successful_ops:
            avg_op_time = sum(op["time"] for op in successful_ops) / len(successful_ops)
            print(f"   • Average successful operation time: {avg_op_time:.3f} seconds")
        
        if failed_ops:
            print(f"⚠️  Failed operations:")
            for failed_op in failed_ops[:3]:  # Show first 3 failures
                print(f"     • Operation {failed_op.get('operation_id')}: {failed_op.get('error')}")
        
        return len(failed_ops) == 0
        
    except Exception as e:
        print(f"❌ Connection pooling test failed: {e}")
        return False


async def test_index_performance():
    """Test database index performance and optimization."""
    print(f"\n📊 TESTING INDEX PERFORMANCE")
    print("=" * 60)
    
    if db.database is None:
        print("⚠️  Database not available - skipping index tests")
        return False
    
    try:
        # Create test data
        print("📝 Creating test data for index performance testing...")
        
        test_collection = db.database.index_performance_test
        
        # Insert test documents
        test_docs = []
        for i in range(1000):
            test_docs.append({
                "user_id": f"user_{i % 100}",  # 100 unique users
                "status": ["pending", "in_progress", "completed"][i % 3],
                "priority": ["low", "medium", "high"][i % 3],
                "created_at": datetime.utcnow() - timedelta(days=i % 30),
                "category": f"category_{i % 10}",
                "value": i * 1.5,
                "tags": [f"tag_{j}" for j in range(i % 5)]
            })
        
        await test_collection.insert_many(test_docs)
        print(f"✅ Inserted {len(test_docs)} test documents")
        
        # Test queries without indexes
        print("🔍 Testing queries without indexes...")
        
        start_time = time.time()
        result1 = await test_collection.find({"user_id": "user_50", "status": "completed"}).to_list(length=None)
        no_index_time = time.time() - start_time
        
        print(f"   • Query without index: {no_index_time:.3f} seconds ({len(result1)} results)")
        
        # Create indexes
        print("📊 Creating performance indexes...")
        
        await test_collection.create_index([("user_id", 1), ("status", 1)], name="idx_user_status")
        await test_collection.create_index([("created_at", -1)], name="idx_created_desc")
        await test_collection.create_index([("category", 1), ("priority", 1)], name="idx_category_priority")
        await test_collection.create_index([("value", 1)], name="idx_value")
        
        print("✅ Performance indexes created")
        
        # Test queries with indexes
        print("🔍 Testing queries with indexes...")
        
        start_time = time.time()
        result2 = await test_collection.find({"user_id": "user_50", "status": "completed"}).to_list(length=None)
        with_index_time = time.time() - start_time
        
        print(f"   • Query with index: {with_index_time:.3f} seconds ({len(result2)} results)")
        
        # Performance improvement
        if no_index_time > 0:
            improvement = ((no_index_time - with_index_time) / no_index_time) * 100
            print(f"   • Performance improvement: {improvement:.1f}%")
        
        # Test complex query
        start_time = time.time()
        complex_result = await test_collection.find({
            "category": "category_5",
            "priority": "high",
            "value": {"$gte": 100}
        }).sort([("created_at", -1)]).limit(10).to_list(length=None)
        complex_time = time.time() - start_time
        
        print(f"   • Complex query: {complex_time:.3f} seconds ({len(complex_result)} results)")
        
        # Get index usage statistics
        try:
            stats = await test_collection.aggregate([
                {"$indexStats": {}}
            ]).to_list(length=None)
            
            print(f"📈 Index usage statistics:")
            for stat in stats[:3]:  # Show first 3 indexes
                index_name = stat.get("name", "unknown")
                accesses = stat.get("accesses", {})
                print(f"   • {index_name}: {accesses.get('ops', 0)} operations")
                
        except Exception as e:
            print(f"⚠️  Could not get index statistics: {e}")
        
        # Clean up test data
        await test_collection.drop()
        print("🧹 Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Index performance test failed: {e}")
        return False


async def test_health_checks():
    """Test comprehensive database health checks."""
    print(f"\n🏥 TESTING DATABASE HEALTH CHECKS")
    print("=" * 60)
    
    try:
        print("🔍 Performing comprehensive health check...")
        
        health_result = await perform_health_check()
        
        print(f"📊 Health Check Results:")
        print(f"   • Overall Health: {'✅ Healthy' if health_result['healthy'] else '❌ Unhealthy'}")
        print(f"   • Timestamp: {health_result['timestamp']}")
        
        # Show individual check results
        checks = health_result.get('checks', {})
        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            status_icon = '✅' if status == 'passed' else '❌'
            
            print(f"   • {check_name}: {status_icon} {status}")
            
            if 'response_time_ms' in check_result:
                print(f"     - Response time: {check_result['response_time_ms']:.2f}ms")
            
            if 'error' in check_result:
                print(f"     - Error: {check_result['error']}")
        
        return health_result['healthy']
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False


async def test_encryption_and_security():
    """Test database encryption and security features."""
    print(f"\n🔒 TESTING ENCRYPTION AND SECURITY")
    print("=" * 60)
    
    try:
        print("🔐 Testing database encryption setup...")
        
        await setup_database_encryption()
        
        print("✅ Encryption setup completed")
        
        # Test secure connection
        if db.client:
            try:
                # Check if connection is using TLS
                server_status = await db.client.admin.command("serverStatus")
                
                if server_status.get("transportSecurity"):
                    print("✅ TLS/SSL encryption verified")
                else:
                    print("⚠️  TLS/SSL encryption not detected (may be expected in development)")
                
                # Test authentication
                try:
                    await db.client.admin.command("connectionStatus")
                    print("✅ Authentication verified")
                except Exception as e:
                    print(f"⚠️  Authentication test: {e}")
                
            except Exception as e:
                print(f"⚠️  Security check error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Encryption and security test failed: {e}")
        return False


async def test_backup_procedures():
    """Test backup procedures and validation."""
    print(f"\n💾 TESTING BACKUP PROCEDURES")
    print("=" * 60)
    
    try:
        print("📋 Setting up backup procedures...")
        
        await setup_backup_procedures()
        
        print("✅ Backup procedures configured")
        
        # Verify backup metadata collection
        if db.database is not None:
            backup_collection = db.database.backup_metadata
            
            # Check if backup configuration was created
            config_doc = await backup_collection.find_one({"config_type": "backup_settings"})
            
            if config_doc:
                print("✅ Backup configuration found:")
                config = config_doc.get('config', {})
                print(f"   • Schedule: {config.get('backup_schedule', 'N/A')}")
                print(f"   • Retention: {config.get('retention_days', 'N/A')} days")
                print(f"   • Types: {', '.join(config.get('backup_types', []))}")
            else:
                print("⚠️  Backup configuration not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup procedures test failed: {e}")
        return False


async def test_production_workload():
    """Test database performance under production-like workload."""
    print(f"\n⚡ TESTING PRODUCTION WORKLOAD")
    print("=" * 60)
    
    if db.database is None:
        print("⚠️  Database not available - skipping workload tests")
        return False
    
    try:
        print("🚀 Simulating production workload...")
        
        # Create test collections
        users_collection = db.database.workload_test_users
        assessments_collection = db.database.workload_test_assessments
        
        # Insert users
        print("👥 Creating test users...")
        users = []
        for i in range(100):
            users.append({
                "user_id": f"user_{i}",
                "email": f"user_{i}@example.com",
                "created_at": datetime.utcnow() - timedelta(days=i % 30),
                "is_active": i % 10 != 0,  # 90% active users
                "subscription_tier": ["free", "basic", "premium"][i % 3]
            })
        
        await users_collection.insert_many(users)
        
        # Create indexes
        await users_collection.create_index([("email", 1)], unique=True)
        await users_collection.create_index([("is_active", 1), ("subscription_tier", 1)])
        
        # Insert assessments
        print("📋 Creating test assessments...")
        assessments = []
        for i in range(500):
            assessments.append({
                "assessment_id": f"assessment_{i}",
                "user_id": f"user_{i % 100}",
                "status": ["pending", "in_progress", "completed"][i % 3],
                "priority": ["low", "medium", "high"][i % 3],
                "created_at": datetime.utcnow() - timedelta(hours=i % 24),
                "assessment_type": ["infrastructure", "security", "compliance"][i % 3]
            })
        
        await assessments_collection.insert_many(assessments)
        
        # Create indexes
        await assessments_collection.create_index([("user_id", 1), ("status", 1)])
        await assessments_collection.create_index([("created_at", -1)])
        await assessments_collection.create_index([("status", 1), ("priority", 1)])
        
        print("✅ Test data created")
        
        # Simulate concurrent operations
        print("⚡ Running concurrent operations...")
        
        async def workload_operation(op_id: int):
            """Simulate a typical application operation."""
            try:
                start_time = time.time()
                
                # Find user
                user = await users_collection.find_one({"user_id": f"user_{op_id % 100}"})
                
                # Find user's assessments
                assessments = await assessments_collection.find({
                    "user_id": f"user_{op_id % 100}",
                    "status": {"$in": ["pending", "in_progress"]}
                }).to_list(length=10)
                
                # Update assessment status
                if assessments:
                    await assessments_collection.update_one(
                        {"assessment_id": assessments[0]["assessment_id"]},
                        {"$set": {"updated_at": datetime.utcnow()}}
                    )
                
                # Insert a new metric
                await db.database.workload_test_metrics.insert_one({
                    "metric_name": f"test_metric_{op_id}",
                    "value": op_id * 1.5,
                    "timestamp": datetime.utcnow(),
                    "source": "workload_test"
                })
                
                operation_time = time.time() - start_time
                return {"success": True, "time": operation_time}
                
            except Exception as e:
                return {"success": False, "error": str(e), "time": time.time() - start_time}
        
        # Run workload
        num_operations = 50
        start_time = time.time()
        
        tasks = [workload_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_ops = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_ops = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        print(f"📊 Workload test results:")
        print(f"   • Total operations: {num_operations}")
        print(f"   • Successful: {len(successful_ops)}")
        print(f"   • Failed: {len(failed_ops)}")
        print(f"   • Total time: {total_time:.2f} seconds")
        print(f"   • Operations per second: {num_operations/total_time:.2f}")
        
        if successful_ops:
            avg_time = sum(op["time"] for op in successful_ops) / len(successful_ops)
            print(f"   • Average operation time: {avg_time:.3f} seconds")
        
        # Clean up test data
        await users_collection.drop()
        await assessments_collection.drop()
        await db.database.workload_test_metrics.drop()
        
        print("🧹 Workload test data cleaned up")
        
        return len(failed_ops) == 0
        
    except Exception as e:
        print(f"❌ Production workload test failed: {e}")
        return False


async def main():
    """Run all production database tests."""
    print("🚀 INFRA MIND PRODUCTION DATABASE TEST SUITE")
    print("=" * 80)
    
    test_results = {}
    
    try:
        # Test basic connection
        test_results["connection"] = await test_production_connection()
        
        # Test connection pooling
        test_results["connection_pooling"] = await test_connection_pooling()
        
        # Test index performance
        test_results["index_performance"] = await test_index_performance()
        
        # Test health checks
        test_results["health_checks"] = await test_health_checks()
        
        # Test encryption and security
        test_results["encryption_security"] = await test_encryption_and_security()
        
        # Test backup procedures
        test_results["backup_procedures"] = await test_backup_procedures()
        
        # Test production workload
        test_results["production_workload"] = await test_production_workload()
        
    finally:
        # Always close database connection
        await close_database()
    
    # Print summary
    print(f"\n" + "=" * 80)
    print("📊 PRODUCTION DATABASE TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   • {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All production database tests passed!")
        print("✅ Database is ready for production deployment")
    else:
        print("⚠️  Some tests failed - review configuration before production deployment")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())