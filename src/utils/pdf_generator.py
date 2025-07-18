"""
PDF generation utilities for AutoJobAgent documents.
Converts text documents to professional PDF format.
"""

from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import re

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PDFGenerator:
    """Generate professional PDF documents from text content."""
    
    def __init__(self):
        """Initialize PDF generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for professional documents."""
        # Only add styles if they don't already exist
        style_names = [style.name for style in self.styles.byName.values()]
        
        # Header style for name
        if 'NameHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='NameHeader',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            ))
        
        # Contact info style
        if 'ContactInfo' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ContactInfo',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                alignment=TA_CENTER,
                textColor=colors.black
            ))
        
        # Section header style
        if 'SectionHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            ))
        
        # Body text style
        if 'BodyText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                textColor=colors.black,
                leftIndent=0
            ))
        
        # Bullet point style
        if 'BulletPoint' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BulletPoint',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=3,
                leftIndent=20,
                bulletIndent=10,
                textColor=colors.black
            ))
    
    def text_to_pdf(self, text_content: str, output_path: Path, document_type: str = "resume") -> bool:
        """
        Convert text content to a professional PDF.
        
        Args:
            text_content: The text content to convert
            output_path: Path where the PDF should be saved
            document_type: Type of document ("resume" or "cover_letter")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Parse content and create flowables
            story = []
            
            if document_type == "resume":
                story = self._parse_resume_content(text_content)
            else:  # cover_letter
                story = self._parse_cover_letter_content(text_content)
            
            # Build PDF
            doc.build(story)
            logger.info(f"Successfully generated PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate PDF {output_path}: {e}")
            return False
    
    def _parse_resume_content(self, content: str) -> list:
        """Parse resume text content into PDF flowables."""
        story = []
        lines = content.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            # Check if this is a name (first non-empty line, all caps or title case)
            if not story and (line.isupper() or line.istitle()) and '|' not in line:
                # This is likely the name
                story.append(Paragraph(line, self.styles['NameHeader']))
                continue
            
            # Check if this is contact info (contains email, phone, or links)
            if any(indicator in line.lower() for indicator in ['@', 'http', '437-', '|']):
                # Clean up contact info formatting
                contact_line = self._format_contact_line(line)
                story.append(Paragraph(contact_line, self.styles['ContactInfo']))
                story.append(Spacer(1, 12))
                continue
            
            # Check if this is a section header (starts with **)
            if line.startswith('**') and line.endswith('**'):
                section_title = line.strip('*').strip()
                current_section = section_title.lower()
                story.append(Paragraph(section_title, self.styles['SectionHeader']))
                continue
            
            # Check if this is a subsection (starts with single *)
            if line.startswith('*') and not line.startswith('**'):
                subsection = line.strip('*').strip()
                story.append(Paragraph(f"<b>{subsection}</b>", self.styles['BodyText']))
                continue
            
            # Check if this is a bullet point
            if line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()
                story.append(Paragraph(f"• {bullet_text}", self.styles['BulletPoint']))
                continue
            
            # Regular content
            if line:
                story.append(Paragraph(line, self.styles['BodyText']))
        
        return story
    
    def _parse_cover_letter_content(self, content: str) -> list:
        """Parse cover letter text content into PDF flowables."""
        story = []
        lines = content.strip().split('\n')
        in_header = True
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            # Header section (contact info)
            if in_header and any(indicator in line for indicator in ['@', 'Mississauga', '437-']):
                story.append(Paragraph(line, self.styles['ContactInfo']))
                continue
            
            # Check for date line (handle dates specially)
            date_patterns = [
                r'[A-Za-z]+ \d{1,2}, \d{4}',  # "June 30, 2025"
                r'\d{1,2}/\d{1,2}/\d{4}',     # "06/30/2025"
                r'\d{4}-\d{2}-\d{2}'          # "2025-06-30"
            ]
            is_date_line = any(re.search(pattern, line) for pattern in date_patterns)
            
            if is_date_line and in_header:
                story.append(Paragraph(line, self.styles['ContactInfo']))
                story.append(Spacer(1, 12))
                continue
            
            # Date or greeting
            if line.startswith('Dear ') or 'Dear' in line:
                in_header = False
                story.append(Spacer(1, 24))  # Space before greeting
                story.append(Paragraph(line, self.styles['BodyText']))
                story.append(Spacer(1, 12))
                continue
            
            # Closing (Sincerely, etc.)
            if line in ['Sincerely,', 'Best regards,', 'Yours truly,']:
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, self.styles['BodyText']))
                continue
            
            # Name at the end - fix the index calculation to avoid the error
            non_empty_lines = [l.strip() for l in lines if l.strip()]
            if line and non_empty_lines and line == non_empty_lines[-1]:
                story.append(Paragraph(f"<b>{line}</b>", self.styles['BodyText']))
                continue
            
            # Regular paragraph
            if line and not in_header:
                story.append(Paragraph(line, self.styles['BodyText']))
                story.append(Spacer(1, 6))
        
        return story
    
    def _format_contact_line(self, line: str) -> str:
        """Format contact information line for better PDF display."""
        # Replace pipe separators with bullets for better visual separation
        formatted = line.replace('|', ' • ')
        
        # Make email and links clickable
        formatted = re.sub(
            r'(https?://[^\s]+)',
            r'<link href="\1">\1</link>',
            formatted
        )
        
        formatted = re.sub(
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'<link href="mailto:\1">\1</link>',
            formatted
        )
        
        return formatted


def convert_text_to_pdf(text_file_path: Path, output_pdf_path: Path, document_type: str = "resume") -> bool:
    """
    Convert a text file to PDF format.
    
    Args:
        text_file_path: Path to the input text file
        output_pdf_path: Path for the output PDF file
        document_type: Type of document ("resume" or "cover_letter")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not text_file_path.exists():
            logger.error(f"Input text file not found: {text_file_path}")
            return False
        
        # Read the text content
        with open(text_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate PDF
        generator = PDFGenerator()
        return generator.text_to_pdf(content, output_pdf_path, document_type)
        
    except Exception as e:
        logger.error(f"Failed to convert {text_file_path} to PDF: {e}")
        return False


if __name__ == "__main__":
    # Test the PDF generator
    test_content = """
**NIRAJAN KHADKA**
Mississauga, ON | Nirajan.Tech@gmail.com | 437-344-5361

**EDUCATION**
Bachelor of Science in Computer Science, University of Toronto, 2024
- GPA: 3.7/4.0

**EXPERIENCE**
Data Analysis Intern, TechCorp Solutions (Summer 2023)
- Analyzed customer data using Python and SQL
- Created Power BI dashboards for executive reporting
"""
    
    generator = PDFGenerator()
    test_path = Path("test_resume.pdf")
    generator.text_to_pdf(test_content, test_path, "resume")
    print(f"Test PDF generated: {test_path}")
