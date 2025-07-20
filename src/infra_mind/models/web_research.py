"""
Web research data model for Infra Mind.

Defines the web scraping and research data document structure.
"""

from datetime import datetime
from typing import Dict, Optional
from beanie import Document, Indexed
from pydantic import Field


class WebResearchData(Document):
    """
    Web research data document model.
    
    Learning Note: This model stores data collected by the Web Research Agent
    from various online sources for market intelligence and validation.
    """
    
    # Source information
    source_url: str = Indexed()
    source_type: str = Indexed()  # pricing, documentation, blog, news, regulatory
    provider: Optional[str] = Indexed()  # aws, azure, gcp, general
    
    # Content identification
    content_hash: str = Indexed(unique=True)  # Hash of content for deduplication
    title: Optional[str] = Field(default=None, description="Page/content title")
    
    # Extracted data
    extracted_data: Dict = Field(
        description="The actual data extracted from the source"
    )
    
    # Validation and quality
    validation_status: str = Field(
        default="pending",
        description="Validation status: pending, validated, invalid, expired"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Confidence in the extracted data (0-1)"
    )
    
    # Timestamps
    last_scraped: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = Field(
        default=None,
        description="When this data expires and should be re-scraped"
    )
    
    # Metadata
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata about the scraping process"
    )
    
    # Processing information
    processing_time_seconds: Optional[float] = Field(
        default=None,
        description="Time taken to process this data"
    )
    
    class Settings:
        """Beanie document settings."""
        name = "web_research_data"
        indexes = [
            [("source_type", 1), ("provider", 1)],  # Query by type and provider
            [("last_scraped", -1)],  # Sort by scrape date
            [("validation_status", 1)],  # Query by validation status
            [("content_hash", 1)],  # Unique content identification
        ]
    
    def __str__(self) -> str:
        """String representation of the web research data."""
        return f"WebResearchData(type={self.source_type}, provider={self.provider})"