#!/usr/bin/env python3
"""
Fix the reports endpoint by removing duplicates and ensuring proper data access.
"""

# Read the file content
with open('/Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/src/infra_mind/api/endpoints/reports.py', 'r') as f:
    content = f.read()

# Find the duplicate section
duplicate_start = content.find('\n@router.get("/all", status_code=status.HTTP_200_OK)', 200)  # Skip first occurrence
if duplicate_start != -1:
    # Find the end of the duplicate function
    next_function_start = content.find('\n@router.get("/{assessment_id}")', duplicate_start)
    if next_function_start != -1:
        # Remove the duplicate section
        fixed_content = content[:duplicate_start] + content[next_function_start:]
        
        # Now fix the first occurrence to use MongoDB directly
        old_section = '''        # Find all reports for this user
        user_reports = await Report.find({"user_id": str(current_user.id)}).to_list()'''
        
        new_section = '''        # Find all reports for this user using direct MongoDB query
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.get_database("infra_mind")
        
        # Query reports collection directly
        cursor = db.reports.find({"user_id": str(current_user.id)})
        user_reports = await cursor.to_list(length=None)
        client.close()'''
        
        fixed_content = fixed_content.replace(old_section, new_section)
        
        # Fix the data access to use dictionary access instead of object attributes
        old_data_access = '''                report_data = {
                    "id": str(report.id),
                    "assessment_id": report.assessment_id,
                    "user_id": report.user_id,
                    "title": report.title,
                    "description": report.description or "",
                    "report_type": report.report_type,
                    "format": report.format,
                    "status": report.status,
                    "progress_percentage": report.progress_percentage,
                    "sections": report.sections or [],
                    "total_pages": report.total_pages or 0,
                    "word_count": report.word_count or 0,
                    "file_path": report.file_path or "",
                    "file_size_bytes": report.file_size_bytes or 0,
                    "generated_by": report.generated_by or [],
                    "generation_time_seconds": report.generation_time_seconds or 0,
                    "completeness_score": report.completeness_score or 0,
                    "confidence_score": report.confidence_score or 0,
                    "priority": report.priority or "medium",
                    "tags": report.tags or [],
                    "retry_count": getattr(report, 'retry_count', 0),
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                    "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                }'''
        
        new_data_access = '''                report_data = {
                    "id": str(report.get("_id", "")),
                    "assessment_id": report.get("assessment_id", ""),
                    "user_id": report.get("user_id", ""),
                    "title": report.get("title", ""),
                    "description": report.get("description", ""),
                    "report_type": report.get("report_type", ""),
                    "format": report.get("format", ""),
                    "status": report.get("status", ""),
                    "progress_percentage": report.get("progress_percentage", 0),
                    "sections": report.get("sections", []),
                    "total_pages": report.get("total_pages", 0),
                    "word_count": report.get("word_count", 0),
                    "file_path": report.get("file_path", ""),
                    "file_size_bytes": report.get("file_size_bytes", 0),
                    "generated_by": report.get("generated_by", []),
                    "generation_time_seconds": report.get("generation_time_seconds", 0),
                    "completeness_score": report.get("completeness_score", 0),
                    "confidence_score": report.get("confidence_score", 0),
                    "priority": report.get("priority", "medium"),
                    "tags": report.get("tags", []),
                    "retry_count": report.get("retry_count", 0),
                    "created_at": report.get("created_at").isoformat() if report.get("created_at") else None,
                    "updated_at": report.get("updated_at").isoformat() if report.get("updated_at") else None,
                    "completed_at": report.get("completed_at").isoformat() if report.get("completed_at") else None,
                }'''
        
        fixed_content = fixed_content.replace(old_data_access, new_data_access)
        
        # Write the fixed content back
        with open('/Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/src/infra_mind/api/endpoints/reports.py', 'w') as f:
            f.write(fixed_content)
        
        print("✅ Fixed reports endpoint successfully!")
        print("- Removed duplicate /all endpoint")
        print("- Updated to use direct MongoDB queries")
        print("- Fixed data access to use dictionary methods")
    else:
        print("❌ Could not find end of duplicate function")
else:
    print("❌ Could not find duplicate section")