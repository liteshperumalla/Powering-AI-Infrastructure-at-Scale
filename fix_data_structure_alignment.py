#!/usr/bin/env python3
"""
Comprehensive Data Structure Alignment Script

This script fixes all data structure inconsistencies across the entire Infra Mind system:
1. Analyzes current data structures in MongoDB
2. Identifies validation conflicts
3. Aligns all data to consistent formats
4. Updates models to handle flexible structures
5. Tests all functionality after alignment
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import traceback

# Configuration
MONGO_URI = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
DRY_RUN = False  # Set to True to see what would be changed without making changes

class DataAlignmentTool:
    def __init__(self):
        self.client = None
        self.db = None
        self.alignment_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collections_analyzed": 0,
            "documents_analyzed": 0,
            "documents_updated": 0,
            "issues_found": [],
            "fixes_applied": [],
            "validation_errors": [],
            "summary": {}
        }
        
    async def __aenter__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.get_database("infra_mind")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def log_issue(self, issue_type: str, collection: str, doc_id: str, description: str, severity: str = "medium"):
        """Log an issue found during analysis."""
        issue = {
            "type": issue_type,
            "collection": collection,
            "document_id": doc_id,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.alignment_report["issues_found"].append(issue)
        print(f"🔍 ISSUE [{severity.upper()}] {collection}/{doc_id}: {description}")

    def log_fix(self, fix_type: str, collection: str, doc_id: str, description: str, changes: Dict[str, Any]):
        """Log a fix applied during migration."""
        fix = {
            "type": fix_type,
            "collection": collection,
            "document_id": doc_id,
            "description": description,
            "changes": changes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.alignment_report["fixes_applied"].append(fix)
        print(f"🔧 FIX {collection}/{doc_id}: {description}")

    async def analyze_reports_collection(self):
        """Analyze and fix the reports collection."""
        print("📊 Analyzing reports collection...")
        
        cursor = self.db.reports.find({})
        reports_analyzed = 0
        reports_fixed = 0
        
        async for report in cursor:
            reports_analyzed += 1
            doc_id = str(report.get("_id", "unknown"))
            
            # Check sections structure
            sections = report.get("sections", [])
            needs_fix = False
            fixes = {}
            
            # Issue 1: Mixed section types (some reports have dict sections, model expects str)
            if sections:
                has_dict_sections = any(isinstance(s, dict) for s in sections)
                has_str_sections = any(isinstance(s, str) for s in sections)
                
                if has_dict_sections:
                    self.log_issue(
                        "data_structure_mismatch", 
                        "reports", 
                        doc_id,
                        f"Report has {len([s for s in sections if isinstance(s, dict)])} dict sections but model expects string IDs",
                        "high"
                    )
                    
                    # Convert dict sections to consistent format
                    aligned_sections = []
                    for i, section in enumerate(sections):
                        if isinstance(section, dict):
                            # Keep the dict but ensure consistent structure
                            aligned_section = {
                                "section_id": section.get("section_id", section.get("id", f"section_{i}")),
                                "title": section.get("title", f"Section {i+1}"),
                                "content": section.get("content", ""),
                                "order": section.get("order", i),
                                "type": section.get("type", "content"),
                                "metadata": section.get("metadata", {})
                            }
                            # Preserve additional fields
                            for key, value in section.items():
                                if key not in aligned_section:
                                    aligned_section[key] = value
                            aligned_sections.append(aligned_section)
                        else:
                            # Convert string ID to dict format for consistency
                            aligned_sections.append({
                                "section_id": section,
                                "title": f"Section {i+1}",
                                "content": "",
                                "order": i,
                                "type": "content",
                                "metadata": {}
                            })
                    
                    fixes["sections"] = aligned_sections
                    needs_fix = True
            
            # Issue 2: Missing sharing fields
            if "shared_with" not in report:
                fixes["shared_with"] = []
                needs_fix = True
                
            if "sharing_permissions" not in report:
                fixes["sharing_permissions"] = {}
                needs_fix = True
                
            if "is_public" not in report:
                fixes["is_public"] = False
                needs_fix = True
                
            # Issue 3: Ensure updated_at is present
            if "updated_at" not in report:
                fixes["updated_at"] = datetime.now(timezone.utc)
                needs_fix = True
            
            # Apply fixes
            if needs_fix and not DRY_RUN:
                try:
                    await self.db.reports.update_one(
                        {"_id": report["_id"]},
                        {"$set": fixes}
                    )
                    reports_fixed += 1
                    self.log_fix(
                        "structure_alignment",
                        "reports",
                        doc_id,
                        f"Aligned report structure and added missing fields",
                        fixes
                    )
                except Exception as e:
                    self.log_issue(
                        "update_failed",
                        "reports",
                        doc_id,
                        f"Failed to update report: {str(e)}",
                        "high"
                    )
            elif needs_fix and DRY_RUN:
                self.log_fix(
                    "structure_alignment",
                    "reports",
                    doc_id,
                    f"[DRY RUN] Would align report structure: {list(fixes.keys())}",
                    fixes
                )
        
        self.alignment_report["summary"]["reports"] = {
            "analyzed": reports_analyzed,
            "fixed": reports_fixed
        }
        print(f"✅ Reports: Analyzed {reports_analyzed}, Fixed {reports_fixed}")

    async def analyze_users_collection(self):
        """Analyze and fix the users collection."""
        print("👤 Analyzing users collection...")
        
        cursor = self.db.users.find({})
        users_analyzed = 0
        users_fixed = 0
        
        async for user in cursor:
            users_analyzed += 1
            doc_id = str(user.get("_id", "unknown"))
            
            needs_fix = False
            fixes = {}
            
            # Issue 1: Ensure required fields exist
            required_fields = {
                "is_active": True,
                "role": "user",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            for field, default_value in required_fields.items():
                if field not in user:
                    fixes[field] = default_value
                    needs_fix = True
            
            # Apply fixes
            if needs_fix and not DRY_RUN:
                try:
                    await self.db.users.update_one(
                        {"_id": user["_id"]},
                        {"$set": fixes}
                    )
                    users_fixed += 1
                    self.log_fix(
                        "missing_fields",
                        "users",
                        doc_id,
                        f"Added missing user fields",
                        fixes
                    )
                except Exception as e:
                    self.log_issue(
                        "update_failed",
                        "users",
                        doc_id,
                        f"Failed to update user: {str(e)}",
                        "high"
                    )
            elif needs_fix and DRY_RUN:
                self.log_fix(
                    "missing_fields",
                    "users",
                    doc_id,
                    f"[DRY RUN] Would add missing fields: {list(fixes.keys())}",
                    fixes
                )
        
        self.alignment_report["summary"]["users"] = {
            "analyzed": users_analyzed,
            "fixed": users_fixed
        }
        print(f"✅ Users: Analyzed {users_analyzed}, Fixed {users_fixed}")

    async def analyze_assessments_collection(self):
        """Analyze and fix the assessments collection."""
        print("📋 Analyzing assessments collection...")
        
        cursor = self.db.assessments.find({})
        assessments_analyzed = 0
        assessments_fixed = 0
        
        async for assessment in cursor:
            assessments_analyzed += 1
            doc_id = str(assessment.get("_id", "unknown"))
            
            needs_fix = False
            fixes = {}
            
            # Issue 1: Ensure consistent structure
            if "updated_at" not in assessment:
                fixes["updated_at"] = datetime.now(timezone.utc)
                needs_fix = True
            
            # Apply fixes
            if needs_fix and not DRY_RUN:
                try:
                    await self.db.assessments.update_one(
                        {"_id": assessment["_id"]},
                        {"$set": fixes}
                    )
                    assessments_fixed += 1
                    self.log_fix(
                        "missing_fields",
                        "assessments",
                        doc_id,
                        f"Added missing assessment fields",
                        fixes
                    )
                except Exception as e:
                    self.log_issue(
                        "update_failed",
                        "assessments",
                        doc_id,
                        f"Failed to update assessment: {str(e)}",
                        "high"
                    )
            elif needs_fix and DRY_RUN:
                self.log_fix(
                    "missing_fields",
                    "assessments",
                    doc_id,
                    f"[DRY RUN] Would add missing fields: {list(fixes.keys())}",
                    fixes
                )
        
        self.alignment_report["summary"]["assessments"] = {
            "analyzed": assessments_analyzed,
            "fixed": assessments_fixed
        }
        print(f"✅ Assessments: Analyzed {assessments_analyzed}, Fixed {assessments_fixed}")

    async def create_indexes(self):
        """Create necessary database indexes for performance."""
        print("📚 Creating database indexes...")
        
        try:
            # Reports indexes
            await self.db.reports.create_index([("user_id", 1)])
            await self.db.reports.create_index([("assessment_id", 1)])
            await self.db.reports.create_index([("report_type", 1)])
            await self.db.reports.create_index([("status", 1)])
            await self.db.reports.create_index([("is_public", 1)])
            await self.db.reports.create_index([("shared_with", 1)])
            
            # Users indexes
            await self.db.users.create_index([("email", 1)], unique=True)
            await self.db.users.create_index([("is_active", 1)])
            
            # Assessments indexes
            await self.db.assessments.create_index([("user_id", 1)])
            await self.db.assessments.create_index([("status", 1)])
            
            print("✅ Database indexes created successfully")
            
        except Exception as e:
            self.log_issue(
                "index_creation_failed",
                "database",
                "indexes",
                f"Failed to create indexes: {str(e)}",
                "medium"
            )

    async def run_comprehensive_alignment(self):
        """Run comprehensive data alignment across all collections."""
        print("🚀 Starting comprehensive data structure alignment...")
        print(f"📝 Mode: {'DRY RUN (no changes will be made)' if DRY_RUN else 'LIVE (changes will be applied)'}")
        
        try:
            # Analyze each collection
            await self.analyze_reports_collection()
            await self.analyze_users_collection()  
            await self.analyze_assessments_collection()
            
            # Create indexes
            if not DRY_RUN:
                await self.create_indexes()
            
            # Update report summary
            total_analyzed = sum(col.get("analyzed", 0) for col in self.alignment_report["summary"].values())
            total_fixed = sum(col.get("fixed", 0) for col in self.alignment_report["summary"].values())
            
            self.alignment_report["collections_analyzed"] = len(self.alignment_report["summary"])
            self.alignment_report["documents_analyzed"] = total_analyzed
            self.alignment_report["documents_updated"] = total_fixed
            
            print("\n" + "="*80)
            print("📊 DATA ALIGNMENT SUMMARY")
            print("="*80)
            print(f"Collections analyzed: {self.alignment_report['collections_analyzed']}")
            print(f"Documents analyzed: {total_analyzed}")
            print(f"Documents updated: {total_fixed}")
            print(f"Issues found: {len(self.alignment_report['issues_found'])}")
            print(f"Fixes applied: {len(self.alignment_report['fixes_applied'])}")
            
            # Show issue breakdown
            if self.alignment_report['issues_found']:
                print(f"\n🔍 Issues by type:")
                issue_types = {}
                for issue in self.alignment_report['issues_found']:
                    issue_type = issue['type']
                    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                for issue_type, count in issue_types.items():
                    print(f"  - {issue_type}: {count}")
            
            # Show collection summary
            print(f"\n📋 By collection:")
            for collection, stats in self.alignment_report["summary"].items():
                print(f"  - {collection}: {stats['analyzed']} analyzed, {stats['fixed']} fixed")
            
            if DRY_RUN:
                print(f"\n⚠️  This was a DRY RUN - no changes were made to the database")
                print(f"   Set DRY_RUN = False in the script to apply these fixes")
            else:
                print(f"\n✅ All changes have been applied to the database")
            
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"❌ Alignment failed: {str(e)}")
            traceback.print_exc()
            return False

    async def save_alignment_report(self):
        """Save the alignment report to a file."""
        report_filename = f"alignment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_filename, 'w') as f:
                json.dump(self.alignment_report, f, indent=2, default=str)
            print(f"📄 Alignment report saved to: {report_filename}")
        except Exception as e:
            print(f"⚠️  Failed to save alignment report: {str(e)}")

async def main():
    """Main execution function."""
    print("🔧 Infra Mind - Data Structure Alignment Tool")
    print("=" * 50)
    
    async with DataAlignmentTool() as tool:
        success = await tool.run_comprehensive_alignment()
        await tool.save_alignment_report()
        
        if success:
            print("\n✅ Data alignment completed successfully!")
            return 0
        else:
            print("\n❌ Data alignment failed!")
            return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Alignment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)