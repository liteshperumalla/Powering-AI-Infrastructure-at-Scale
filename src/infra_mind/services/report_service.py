"""
Advanced Report Service for Infra Mind.

Provides advanced reporting features including versioning, collaboration,
templates, and interactive previews.
"""

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from ..models.report import Report, ReportSection, ReportTemplate, ReportType, ReportFormat, ReportStatus
from ..models.assessment import Assessment
from ..core.database import db

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for advanced report management features.
    
    Provides functionality for:
    - Report versioning and comparison
    - Template management and customization
    - Report sharing and collaboration
    - Interactive report previews
    """
    
    def __init__(self):
        """Initialize the report service."""
        self.db = db
    
    async def create_report_from_template(
        self,
        assessment_id: str,
        user_id: str,
        template_id: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Create a new report using a template."""
        try:
            # Get the template
            template = await ReportTemplate.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Check if user can access template
            if not template.can_user_access(user_id):
                raise PermissionError("User does not have access to this template")
            
            # Create report from template
            report = Report(
                assessment_id=assessment_id,
                user_id=user_id,
                title=f"Report from {template.name}",
                report_type=template.report_type,
                template_id=template_id,
                branding_config=template.branding_config.copy(),
                custom_css=template.css_template
            )
            
            # Apply custom configuration if provided
            if custom_config:
                if "title" in custom_config:
                    report.title = custom_config["title"]
                if "branding" in custom_config:
                    report.branding_config.update(custom_config["branding"])
                if "custom_css" in custom_config:
                    report.custom_css = custom_config["custom_css"]
            
            # Save report
            await report.insert()
            
            # Update template usage
            template.increment_usage()
            await template.save()
            
            logger.info(f"Created report {report.id} from template {template_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error creating report from template: {str(e)}")
            raise
    
    async def create_report_version(
        self,
        original_report_id: str,
        user_id: str,
        version: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Create a new version of an existing report."""
        try:
            # Get original report
            original_report = await Report.get(original_report_id)
            if not original_report:
                raise ValueError(f"Report {original_report_id} not found")
            
            # Check permissions
            if not original_report.can_user_access(user_id, "edit"):
                raise PermissionError("User does not have edit access to this report")
            
            # Create new version
            new_report = original_report.create_new_version(version)
            
            # Apply changes if provided
            if changes:
                for key, value in changes.items():
                    if hasattr(new_report, key):
                        setattr(new_report, key, value)
            
            # Save new version
            await new_report.insert()
            
            logger.info(f"Created version {version} of report {original_report_id}")
            return new_report
            
        except Exception as e:
            logger.error(f"Error creating report version: {str(e)}")
            raise
    
    async def compare_report_versions(
        self,
        report_id_1: str,
        report_id_2: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Compare two versions of a report."""
        try:
            # Get both reports
            report1 = await Report.get(report_id_1)
            report2 = await Report.get(report_id_2)
            
            if not report1 or not report2:
                raise ValueError("One or both reports not found")
            
            # Check permissions
            if not (report1.can_user_access(user_id) and report2.can_user_access(user_id)):
                raise PermissionError("User does not have access to one or both reports")
            
            # Get sections for both reports
            sections1 = await ReportSection.find({"report_id": report_id_1}).to_list()
            sections2 = await ReportSection.find({"report_id": report_id_2}).to_list()
            
            # Create section maps for comparison
            sections1_map = {s.section_id: s for s in sections1}
            sections2_map = {s.section_id: s for s in sections2}
            
            # Compare sections
            comparison = {
                "report1": {
                    "id": report_id_1,
                    "title": report1.title,
                    "version": report1.version,
                    "created_at": report1.created_at.isoformat()
                },
                "report2": {
                    "id": report_id_2,
                    "title": report2.title,
                    "version": report2.version,
                    "created_at": report2.created_at.isoformat()
                },
                "differences": {
                    "metadata": self._compare_metadata(report1, report2),
                    "sections": self._compare_sections(sections1_map, sections2_map)
                }
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing report versions: {str(e)}")
            raise
    
    def _compare_metadata(self, report1: Report, report2: Report) -> Dict[str, Any]:
        """Compare metadata between two reports."""
        differences = {}
        
        fields_to_compare = [
            "title", "description", "report_type", "format",
            "branding_config", "custom_css", "logo_url"
        ]
        
        for field in fields_to_compare:
            value1 = getattr(report1, field, None)
            value2 = getattr(report2, field, None)
            
            if value1 != value2:
                differences[field] = {
                    "report1": value1,
                    "report2": value2
                }
        
        return differences
    
    def _compare_sections(
        self,
        sections1_map: Dict[str, ReportSection],
        sections2_map: Dict[str, ReportSection]
    ) -> Dict[str, Any]:
        """Compare sections between two reports."""
        differences = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        all_section_ids = set(sections1_map.keys()) | set(sections2_map.keys())
        
        for section_id in all_section_ids:
            section1 = sections1_map.get(section_id)
            section2 = sections2_map.get(section_id)
            
            if section1 and not section2:
                differences["removed"].append({
                    "section_id": section_id,
                    "title": section1.title
                })
            elif section2 and not section1:
                differences["added"].append({
                    "section_id": section_id,
                    "title": section2.title
                })
            elif section1 and section2:
                section_diff = self._compare_section_content(section1, section2)
                if section_diff:
                    differences["modified"].append({
                        "section_id": section_id,
                        "title": section2.title,
                        "changes": section_diff
                    })
        
        return differences
    
    def _compare_section_content(
        self,
        section1: ReportSection,
        section2: ReportSection
    ) -> Dict[str, Any]:
        """Compare content between two sections."""
        differences = {}
        
        fields_to_compare = ["title", "content", "order", "is_interactive"]
        
        for field in fields_to_compare:
            value1 = getattr(section1, field, None)
            value2 = getattr(section2, field, None)
            
            if value1 != value2:
                differences[field] = {
                    "old": value1,
                    "new": value2
                }
        
        return differences
    
    async def share_report(
        self,
        report_id: str,
        owner_id: str,
        share_with_user_id: str,
        permission: str = "view"
    ) -> None:
        """Share a report with another user."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            from bson import ObjectId
            
            # Connect to database directly for reliability
            mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
            client = AsyncIOMotorClient(mongo_uri)
            db_conn = client.get_database("infra_mind")
            
            # Get the report by ObjectId
            try:
                report_doc = await db_conn.reports.find_one({"_id": ObjectId(report_id)})
            except Exception:
                # If ObjectId conversion fails, might be a string ID
                report_doc = await db_conn.reports.find_one({"report_id": report_id})
            
            if not report_doc:
                raise ValueError(f"Report {report_id} not found")
            
            # Check if user is owner or already has admin permission
            user_id_str = str(report_doc.get("user_id"))
            shared_with = report_doc.get("shared_with", [])
            sharing_permissions = report_doc.get("sharing_permissions", {})
            
            if not (user_id_str == owner_id or sharing_permissions.get(owner_id) == "admin"):
                raise PermissionError("User does not have permission to share this report")
            
            # Update sharing information
            if share_with_user_id not in shared_with:
                shared_with.append(share_with_user_id)
            sharing_permissions[share_with_user_id] = permission
            
            # Update the report in database
            try:
                update_result = await db_conn.reports.update_one(
                    {"_id": ObjectId(report_id)},
                    {
                        "$set": {
                            "shared_with": shared_with,
                            "sharing_permissions": sharing_permissions,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            except Exception:
                # Try with report_id field if ObjectId fails
                update_result = await db_conn.reports.update_one(
                    {"report_id": report_id},
                    {
                        "$set": {
                            "shared_with": shared_with,
                            "sharing_permissions": sharing_permissions,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            
            if update_result.matched_count == 0:
                raise ValueError(f"Failed to update report {report_id}")
            
            await client.close()
            logger.info(f"Shared report {report_id} with user {share_with_user_id} ({permission})")
            
        except Exception as e:
            logger.error(f"Error sharing report: {str(e)}")
            raise
    
    async def create_public_link(
        self,
        report_id: str,
        user_id: str
    ) -> str:
        """Create a public link for a report."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            from bson import ObjectId
            
            # Connect to database directly for reliability
            mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
            client = AsyncIOMotorClient(mongo_uri)
            db_conn = client.get_database("infra_mind")
            
            # Get the report by ObjectId
            try:
                report_doc = await db_conn.reports.find_one({"_id": ObjectId(report_id)})
            except Exception:
                # If ObjectId conversion fails, might be a string ID
                report_doc = await db_conn.reports.find_one({"report_id": report_id})
            
            if not report_doc:
                raise ValueError(f"Report {report_id} not found")
            
            # Check permissions - user must be owner or have admin access
            user_id_str = str(report_doc.get("user_id"))
            sharing_permissions = report_doc.get("sharing_permissions", {})
            
            if not (user_id_str == user_id or sharing_permissions.get(user_id) == "admin"):
                raise PermissionError("User does not have admin access to this report")
            
            # Generate public link token
            public_token = str(uuid.uuid4())
            
            # Update the report in database
            try:
                update_result = await db_conn.reports.update_one(
                    {"_id": ObjectId(report_id)},
                    {
                        "$set": {
                            "is_public": True,
                            "public_link_token": public_token,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            except Exception:
                # Try with report_id field if ObjectId fails
                update_result = await db_conn.reports.update_one(
                    {"report_id": report_id},
                    {
                        "$set": {
                            "is_public": True,
                            "public_link_token": public_token,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            
            if update_result.matched_count == 0:
                raise ValueError(f"Failed to update report {report_id}")
            
            await client.close()
            logger.info(f"Created public link for report {report_id}")
            return public_token
            
        except Exception as e:
            logger.error(f"Error creating public link: {str(e)}")
            raise
    
    async def get_report_with_interactive_data(
        self,
        report_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get report with interactive drill-down data."""
        try:
            # Get the report
            report = await Report.get(report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Check permissions
            if not report.can_user_access(user_id):
                raise PermissionError("User does not have access to this report")
            
            # Get sections with interactive data
            sections = await ReportSection.find({"report_id": report_id}).to_list()
            
            # Build interactive report data
            interactive_data = {
                "report": {
                    "id": report.id,
                    "title": report.title,
                    "version": report.version,
                    "branding_config": report.branding_config,
                    "custom_css": report.custom_css
                },
                "sections": [],
                "navigation": self._build_navigation(sections)
            }
            
            for section in sorted(sections, key=lambda s: s.order):
                section_data = {
                    "id": section.section_id,
                    "title": section.title,
                    "content": section.content,
                    "content_type": section.content_type,
                    "order": section.order,
                    "is_interactive": section.is_interactive
                }
                
                if section.is_interactive:
                    section_data["drill_down_data"] = section.drill_down_data
                    section_data["charts_config"] = section.charts_config
                
                interactive_data["sections"].append(section_data)
            
            return interactive_data
            
        except Exception as e:
            logger.error(f"Error getting interactive report data: {str(e)}")
            raise
    
    def _build_navigation(self, sections: List[ReportSection]) -> List[Dict[str, Any]]:
        """Build navigation structure for the report."""
        navigation = []
        
        for section in sorted(sections, key=lambda s: s.order):
            nav_item = {
                "id": section.section_id,
                "title": section.title,
                "order": section.order,
                "has_interactive_content": section.is_interactive
            }
            navigation.append(nav_item)
        
        return navigation
    
    async def create_template_from_report(
        self,
        report_id: str,
        user_id: str,
        template_name: str,
        template_description: Optional[str] = None,
        is_public: bool = False
    ) -> ReportTemplate:
        """Create a reusable template from an existing report."""
        try:
            # Get the report
            report = await Report.get(report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Check permissions
            if not report.can_user_access(user_id, "admin"):
                raise PermissionError("User does not have admin access to this report")
            
            # Get report sections
            sections = await ReportSection.find({"report_id": report_id}).to_list()
            
            # Build sections configuration
            sections_config = []
            for section in sorted(sections, key=lambda s: s.order):
                section_config = {
                    "title": section.title,
                    "order": section.order,
                    "content_type": section.content_type,
                    "is_interactive": section.is_interactive,
                    "generated_by": section.generated_by
                }
                sections_config.append(section_config)
            
            # Create template
            template = ReportTemplate(
                name=template_name,
                description=template_description,
                report_type=report.report_type,
                sections_config=sections_config,
                branding_config=report.branding_config.copy(),
                css_template=report.custom_css,
                created_by=user_id,
                is_public=is_public
            )
            
            await template.insert()
            
            logger.info(f"Created template {template.id} from report {report_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating template from report: {str(e)}")
            raise
    
    async def get_user_reports_with_versions(
        self,
        user_id: str,
        include_shared: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all reports for a user with version information."""
        try:
            # Build query
            query = {"$or": [{"user_id": user_id}]}
            
            if include_shared:
                query["$or"].append({"shared_with": user_id})
            
            # Get reports
            reports = await Report.find(query).to_list()
            
            # Group by parent report and organize versions
            report_groups = {}
            
            for report in reports:
                # Determine the root report ID
                root_id = report.parent_report_id or str(report.id)
                
                if root_id not in report_groups:
                    report_groups[root_id] = {
                        "root_report": None,
                        "versions": []
                    }
                
                if not report.parent_report_id:
                    report_groups[root_id]["root_report"] = report
                
                report_groups[root_id]["versions"].append(report)
            
            # Format response
            result = []
            for group_data in report_groups.values():
                root_report = group_data["root_report"]
                versions = sorted(group_data["versions"], key=lambda r: r.created_at, reverse=True)
                
                if root_report:
                    result.append({
                        "root_report": {
                            "id": str(root_report.id),
                            "title": root_report.title,
                            "report_type": root_report.report_type.value,
                            "created_at": root_report.created_at.isoformat(),
                            "status": root_report.status.value
                        },
                        "versions": [
                            {
                                "id": str(v.id),
                                "version": v.version,
                                "created_at": v.created_at.isoformat(),
                                "status": v.status.value,
                                "is_current": v == versions[0]
                            }
                            for v in versions
                        ],
                        "total_versions": len(versions),
                        "shared_with_count": len(root_report.shared_with)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user reports with versions: {str(e)}")
            raise