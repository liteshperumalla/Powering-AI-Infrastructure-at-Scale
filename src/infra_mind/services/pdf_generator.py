"""
PDF Generation Service for Reports

This module provides functionality to generate PDF reports from report data.
"""

import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from loguru import logger


class PDFReportGenerator:
    """Generates PDF reports from structured report data."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1976d2')
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#1976d2'),
            borderWidth=1,
            borderColor=colors.HexColor('#1976d2'),
            borderPadding=5
        ))

        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#424242')
        ))

        # Content style
        self.styles.add(ParagraphStyle(
            name='ContentText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        ))

        # Key findings style
        self.styles.add(ParagraphStyle(
            name='KeyFinding',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            bulletIndent=10,
            alignment=TA_LEFT
        ))

    def _format_markdown_text(self, text: str) -> str:
        """Convert markdown formatting to ReportLab XML tags."""
        if not text:
            return ""

        # Convert **bold** to <b>bold</b>
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

        # Handle bullet points with proper formatting
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('• '):
                # Remove bullet and add proper formatting
                formatted_lines.append('  • ' + stripped[2:])
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _calculate_word_count(self, report_data: Dict[str, Any]) -> int:
        """Calculate total word count from all sections."""
        word_count = 0
        sections = report_data.get('sections', [])

        for section in sections:
            if isinstance(section, dict):
                content = section.get('content', '')
                if content:
                    word_count += len(content.split())

        return word_count
    
    def generate_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF from report data.
        
        Args:
            report_data: Dictionary containing report information
            
        Returns:
            bytes: PDF file content as bytes
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the story (content) for the PDF
            story = []
            
            # Title page
            self._add_title_page(story, report_data)
            
            # Table of contents could go here
            
            # Report sections
            self._add_report_sections(story, report_data)
            
            # Footer information
            self._add_footer_info(story, report_data)
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to generate PDF: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _add_title_page(self, story: List[Flowable], report_data: Dict[str, Any]):
        """Add title page to the PDF."""
        # Main title
        title = report_data.get('title', 'Infrastructure Assessment Report')
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 30))
        
        # Report type
        report_type = report_data.get('report_type', 'Technical Report')
        story.append(Paragraph(f"Report Type: {report_type.replace('_', ' ').title()}", 
                              self.styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Report metadata
        created_date = report_data.get('created_at', datetime.now())
        if isinstance(created_date, str):
            created_date = created_date[:10]  # Take date part only
        elif hasattr(created_date, 'strftime'):
            created_date = created_date.strftime('%Y-%m-%d')
        
        # Calculate actual metadata values
        word_count = self._calculate_word_count(report_data)
        # Pages will be calculated after PDF generation, so we'll show estimated count
        sections = report_data.get('sections', [])
        estimated_pages = max(1, len(sections))  # Rough estimate based on sections

        metadata_data = [
            ['Report ID:', str(report_data.get('report_id', 'N/A'))],
            ['Generated:', str(created_date)],
            ['Status:', str(report_data.get('status', 'Completed')).title()],
            ['Pages:', str(estimated_pages) + ' (est.)'],
            ['Word Count:', f"{word_count:,}"]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 40))
        
        # Executive summary if available
        sections = report_data.get('sections', [])
        # Safely find executive summary section (handle both dict and string sections)
        exec_summary = None
        for s in sections:
            if isinstance(s, dict) and 'executive' in s.get('title', '').lower():
                exec_summary = s
                break

        if exec_summary and isinstance(exec_summary, dict) and exec_summary.get('content'):
            story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
            # Apply markdown formatting
            formatted_content = self._format_markdown_text(exec_summary['content'])
            story.append(Paragraph(formatted_content, self.styles['ContentText']))
            story.append(Spacer(1, 20))
        
        story.append(PageBreak())
    
    def _add_report_sections(self, story: List[Flowable], report_data: Dict[str, Any]):
        """Add main report sections to the PDF."""
        sections = report_data.get('sections', [])

        for section in sections:
            # Handle both dict and string sections
            if isinstance(section, dict):
                section_title = section.get('title', 'Untitled Section')
                section_content = section.get('content')
                section_type = section.get('type', 'content')
            elif isinstance(section, str):
                section_title = section
                section_content = None
                section_type = 'content'
            else:
                continue  # Skip invalid sections
            
            # Skip executive summary as it's already in title page
            if 'executive' in section_title.lower():
                continue
            
            # Add section heading
            story.append(KeepTogether([
                Paragraph(section_title, self.styles['SectionHeading']),
                Spacer(1, 12)
            ]))
            
            # Add section content
            if section_content:
                # Apply markdown formatting
                formatted_content = self._format_markdown_text(section_content)

                # Split long content into paragraphs
                paragraphs = formatted_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.strip(), self.styles['ContentText']))
            
            story.append(Spacer(1, 20))
        
        # Add key findings if available
        key_findings = report_data.get('key_findings', [])
        if key_findings:
            story.append(PageBreak())
            story.append(Paragraph("Key Findings", self.styles['SectionHeading']))
            
            for i, finding in enumerate(key_findings, 1):
                if finding and isinstance(finding, str) and finding.strip():
                    story.append(Paragraph(f"• {finding}", self.styles['KeyFinding']))
        
        # Add recommendations if available
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("Recommendations", self.styles['SectionHeading']))
            
            for i, rec in enumerate(recommendations, 1):
                if rec and isinstance(rec, str) and rec.strip():
                    story.append(Paragraph(f"{i}. {rec}", self.styles['ContentText']))
                    story.append(Spacer(1, 8))
    
    def _add_footer_info(self, story: List[Flowable], report_data: Dict[str, Any]):
        """Add footer information to the PDF."""
        story.append(PageBreak())
        story.append(Paragraph("Report Information", self.styles['SectionHeading']))
        
        footer_text = f"""
        This report was generated by the Infra Mind AI Infrastructure Advisory Platform.
        
        Report Generation Details:
        • Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        • Report ID: {report_data.get('report_id')}
        • Assessment ID: {report_data.get('assessment_id')}
        • Platform Version: 2.0
        
        For questions about this report, please contact your infrastructure advisory team.
        """
        
        story.append(Paragraph(footer_text, self.styles['ContentText']))


# Global instance
pdf_generator = PDFReportGenerator()


def generate_report_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate a PDF from report data.
    
    Args:
        report_data: Dictionary containing report information
        
    Returns:
        bytes: PDF file content as bytes
    """
    return pdf_generator.generate_pdf(report_data)