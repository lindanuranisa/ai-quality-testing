# report_generator.py - Updated for contextual verification with PPTX support
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.flowables import KeepTogether
import json
import os
from datetime import datetime
from typing import Dict, Any

class SemanticReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Custom styles for better layout
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.darkblue,
            keepWithNext=True
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
    
    def _safe_text(self, text: str, max_length: int = 100) -> str:
        """Safely truncate text for table cells with proper word wrapping"""
        if not text or text == 'N/A':
            return 'N/A'
        
        text = str(text).strip()
        if len(text) > max_length:
            return text[:max_length-3] + '...'
        return text
    
    def _wrap_text_for_cell(self, text: str, max_length: int = 80) -> str:
        """Create wrapped text for better table cell display"""
        if not text or text == 'N/A':
            return 'N/A'
        
        text = str(text).strip()
        
        # If text is short enough, return as-is
        if len(text) <= max_length:
            return text
        
        # For longer text, try to break at word boundaries
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 3 lines max
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:max_length-3] + '...'
        
        return '\n'.join(lines)
    
    def _format_source_location(self, source_file: str, page_number: int) -> str:
        """ENHANCED: Format source file and page/slide number for display"""
        if not source_file or source_file in ['N/A', None, 'None']:
            return 'N/A'
        
        if not page_number or page_number in ['N/A', None, 'None']:
            return source_file.replace('_', ' ').title()
        
        # Clean up source file name for display
        display_name = str(source_file).replace('_', ' ').title()
        
        # Determine if this is a slide (from PPTX) or page (from PDF)
        # Check if source file name contains indicators of presentation format
        source_lower = str(source_file).lower()
        is_presentation = any(indicator in source_lower for indicator in ['pitch', 'deck', 'presentation', 'slide', 'pptx'])
        
        if is_presentation:
            return f"{display_name}: Slide {page_number}"
        else:
            return f"{display_name}: Page {page_number}"
    
    def _safe_get_value(self, data: Dict, key: str, default: Any = 'N/A') -> Any:
        """Safely get value from dictionary with fallback"""
        try:
            value = data.get(key, default)
            if value is None:
                return default
            return value
        except Exception:
            return default
    
    def create_semantic_quality_report(self, 
                                     company_name: str,
                                     frontend_results: Dict,
                                     memo_results: Dict,
                                     output_path: str):
        """Create contextual verification report"""
        
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Title
        title_text = f"AI Quality Assessment Report - {company_name}"
        title = Paragraph(title_text, self.title_style)
        story.append(title)
        
        # Metadata
        metadata_text = f"""
        <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Assessment Type:</b> Contextual Verification & Fact-Checking<br/>
        <b>Company:</b> {company_name}<br/>
        <b>Scoring:</b> Pass ≥ 50, Fail &lt; 50<br/>
        <b>Verification Method:</b> Semantic understanding with source context
        """
        story.append(Paragraph(metadata_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary with safe calculations
        frontend_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in frontend_results.values()]
        frontend_scores = [s for s in frontend_scores if isinstance(s, (int, float))]
        frontend_avg = sum(frontend_scores) / len(frontend_scores) if frontend_scores else 0
        
        memo_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in memo_results.values()]
        memo_scores = [s for s in memo_scores if isinstance(s, (int, float))]
        memo_avg = sum(memo_scores) / len(memo_scores) if memo_scores else 0
        
        overall_avg = (frontend_avg + memo_avg) / 2 if (frontend_avg + memo_avg) > 0 else 0
        
        # Count contextual matches
        contextual_matches = sum(1 for r in frontend_results.values() if r.get('contextual_match'))
        verified_correct = sum(1 for r in memo_results.values() if r.get('wrong_info') == 'None')
        
        summary_text = f"""
        <b>Executive Summary</b><br/>
        Overall Quality Score: <b>{overall_avg:.1f}/100</b><br/>
        Frontend Data Score: <b>{frontend_avg:.1f}/100</b><br/>
        Investment Memo Score: <b>{memo_avg:.1f}/100</b><br/>
        Status: <b>{'PASS' if overall_avg >= 50 else 'FAIL'}</b><br/>
        <br/>
        <b>Contextual Analysis:</b><br/>
        Contextual Matches: <b>{contextual_matches}/{len(frontend_results)}</b> frontend fields<br/>
        Verified Sections: <b>{verified_correct}/{len(memo_results)}</b> memo sections
        """
        story.append(Paragraph(summary_text, self.normal_style))
        story.append(Spacer(1, 30))
        
        # Frontend Data Verification Section
        if frontend_results:
            story.append(Paragraph("Frontend Data Contextual Verification", self.heading_style))
            
            frontend_data = [
                ['Field', 'AI Value', 'Source Value', 'Source & Location', 'Score', 'Status', 'Match Type']
            ]
            
            for field, result in frontend_results.items():
                try:
                    ai_value = self._wrap_text_for_cell(self._safe_get_value(result, 'ai_value', 'N/A'), 35)
                    source_value = self._wrap_text_for_cell(self._safe_get_value(result, 'source_value', 'N/A'), 35)
                    
                    # ENHANCED: Format source location with proper page/slide designation
                    source_location = self._format_source_location(
                        self._safe_get_value(result, 'source_file'), 
                        self._safe_get_value(result, 'page_number')
                    )
                    
                    score = str(self._safe_get_value(result, 'accuracy_score', 0))
                    status = self._safe_get_value(result, 'status', 'FAIL')
                    
                    # Get verification type
                    verification_type = self._safe_get_value(result, 'verification_type', 'Unknown')
                    match_type = verification_type[:15] + '...' if len(verification_type) > 15 else verification_type
                    
                    frontend_data.append([
                        field,
                        ai_value,
                        source_value,
                        source_location,
                        score,
                        status,
                        match_type
                    ])
                except Exception as e:
                    print(f"      ⚠️ Error processing frontend result for {field}: {e}")
                    frontend_data.append([
                        field,
                        'Error',
                        'Error processing result',
                        'N/A',
                        '0',
                        'FAIL',
                        'Error'
                    ])
            
            # Create table with adjusted column widths
            col_widths = [1.0*inch, 1.3*inch, 1.3*inch, 1.0*inch, 0.5*inch, 0.5*inch, 0.8*inch]
            frontend_table = Table(frontend_data, colWidths=col_widths)
            
            # Apply table style
            frontend_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            # Color code based on status and match type
            for i, (field, result) in enumerate(frontend_results.items(), 1):
                try:
                    score = self._safe_get_value(result, 'accuracy_score', 0)
                    is_contextual = result.get('contextual_match', False)
                    
                    if isinstance(score, (int, float)) and score >= 50:
                        if is_contextual:
                            # Light blue for contextual matches
                            frontend_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, i), (-1, i), colors.lightblue)
                            ]))
                        else:
                            # Light green for direct matches
                            frontend_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
                            ]))
                    else:
                        frontend_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                        ]))
                except Exception:
                    # Default to red for errors
                    frontend_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                    ]))
            
            # Wrap table to prevent breaking
            story.append(KeepTogether(frontend_table))
            story.append(PageBreak())
        
        # Investment Memo Verification Section
        if memo_results:
            story.append(Paragraph("Investment Memo Contextual Fact-Checking", self.heading_style))
            
            memo_data = [
                ['Section', 'Wrong Info Found', 'Correct Info (Source)', 'Source & Location', 'Score', 'Status', 'Verification']
            ]
            
            for section, result in memo_results.items():
                try:
                    section_name = section.replace('_', ' ').title()
                    wrong_info = self._wrap_text_for_cell(self._safe_get_value(result, 'wrong_info', 'N/A'), 40)
                    correct_info = self._wrap_text_for_cell(self._safe_get_value(result, 'correct_info', 'N/A'), 40)
                    
                    # ENHANCED: Format source location with proper page/slide designation
                    source_location = self._format_source_location(
                        self._safe_get_value(result, 'source_file'), 
                        self._safe_get_value(result, 'page_number')
                    )
                    
                    score = str(self._safe_get_value(result, 'accuracy_score', 0))
                    status = self._safe_get_value(result, 'status', 'FAIL')
                    
                    # Get verification type
                    verification_type = self._safe_get_value(result, 'verification_type', 'Unknown')
                    verification = verification_type[:12] + '...' if len(verification_type) > 12 else verification_type
                    
                    memo_data.append([
                        section_name,
                        wrong_info,
                        correct_info,
                        source_location,
                        score,
                        status,
                        verification
                    ])
                except Exception as e:
                    print(f"      ⚠️ Error processing memo result for {section}: {e}")
                    memo_data.append([
                        section.replace('_', ' ').title(),
                        'Error processing result',
                        'N/A',
                        'N/A',
                        '0',
                        'FAIL',
                        'Error'
                    ])
            
            # Create table with adjusted column widths
            col_widths = [0.9*inch, 1.8*inch, 1.8*inch, 0.9*inch, 0.4*inch, 0.4*inch, 0.7*inch]
            memo_table = Table(memo_data, colWidths=col_widths)
            
            # Apply table style
            memo_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            # Color code based on status and verification type
            for i, (section, result) in enumerate(memo_results.items(), 1):
                try:
                    score = self._safe_get_value(result, 'accuracy_score', 0)
                    wrong_info = self._safe_get_value(result, 'wrong_info', '')
                    
                    if isinstance(score, (int, float)) and score >= 50:
                        if wrong_info == 'None':
                            # Light blue for verified correct sections
                            memo_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, i), (-1, i), colors.lightblue)
                            ]))
                        else:
                            # Light green for other passing sections
                            memo_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
                            ]))
                    else:
                        memo_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                        ]))
                except Exception:
                    # Default to red for errors
                    memo_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                    ]))
            
            # Wrap table to prevent breaking
            story.append(KeepTogether(memo_table))
        
        # Detailed Analysis Section
        story.append(Spacer(1, 30))
        story.append(Paragraph("Contextual Verification Analysis", self.heading_style))
        
        # Calculate enhanced statistics
        try:
            # Frontend statistics
            frontend_passed = sum(1 for r in frontend_results.values() 
                                if self._safe_get_value(r, 'status') == 'PASS')
            frontend_total = len(frontend_results)
            contextual_matches = sum(1 for r in frontend_results.values() if r.get('contextual_match'))
            direct_matches = frontend_passed - contextual_matches
            
            # Memo statistics
            memo_passed = sum(1 for r in memo_results.values() 
                            if self._safe_get_value(r, 'status') == 'PASS')
            memo_total = len(memo_results)
            verified_correct = sum(1 for r in memo_results.values() 
                                 if self._safe_get_value(r, 'wrong_info', '').lower() in ['none', 'verified correct'])
            issues_found = memo_total - verified_correct
            
            # Count unique source files referenced
            all_results = {**frontend_results, **memo_results}
            source_files_referenced = len(set(
                self._safe_get_value(r, 'source_file', 'N/A') 
                for r in all_results.values() 
                if self._safe_get_value(r, 'source_file') not in [None, 'N/A', 'None']
            ))
            
            # Count PDF pages vs PPTX slides referenced
            pdf_refs = 0
            pptx_refs = 0
            for r in all_results.values():
                source_file = self._safe_get_value(r, 'source_file', '')
                if source_file and source_file not in [None, 'N/A', 'None']:
                    source_lower = str(source_file).lower()
                    if any(indicator in source_lower for indicator in ['pitch', 'deck', 'presentation', 'slide']):
                        pptx_refs += 1
                    else:
                        pdf_refs += 1
            
            analysis_text = f"""
            <b>Contextual Verification Results:</b><br/>
            • Frontend fields passed: {frontend_passed}/{frontend_total}<br/>
            • Direct matches: {direct_matches}, Contextual matches: {contextual_matches}<br/>
            • Memo sections passed: {memo_passed}/{memo_total}<br/>
            • Sections verified correct: {verified_correct}, Issues found: {issues_found}<br/>
            • Source files referenced: {source_files_referenced} different documents<br/>
            • PDF pages referenced: {pdf_refs}, PPTX slides referenced: {pptx_refs}<br/>
            • Overall pass rate: {((frontend_passed + memo_passed) / (frontend_total + memo_total) * 100):.1f}%<br/>
            <br/>
            <b>Contextual Verification Method:</b><br/>
            • Frontend: AI values verified using semantic understanding of source context<br/>
            • Memo: Investment memo claims fact-checked against source documents contextually<br/>
            • Scoring: PASS ≥ 50 points, with contextual matches receiving appropriate credit<br/>
            • Source Tracking: Properly handles both PDF pages and PPTX slides<br/>
            • Color coding: Light blue = contextual/verified correct, Light green = direct match, Red = failed<br/>
            <br/>
            <b>Key Benefits:</b><br/>
            • Contextual matching handles variations in terminology and format<br/>
            • Source file tracking enables verification of specific claims in both PDFs and presentations<br/>
            • Semantic understanding reduces false negatives from exact matching<br/>
            • Fact-checking identifies actual inaccuracies vs. formatting differences<br/>
            • Multi-format support: Handles both document pages and presentation slides
            """
            
        except Exception as e:
            print(f"      ⚠️ Error calculating analysis statistics: {e}")
            analysis_text = f"""
            <b>Analysis Error:</b><br/>
            There was an error calculating detailed statistics. Please review the individual results above.<br/>
            <br/>
            <b>Basic Information:</b><br/>
            • Frontend results: {len(frontend_results)} fields processed<br/>
            • Memo results: {len(memo_results)} sections processed<br/>
            • Error details: {str(e)[:200]}...<br/>
            """
        
        story.append(Paragraph(analysis_text, self.normal_style))
        
        # Build PDF
        try:
            doc.build(story)
            print(f"✅ Contextual verification report generated successfully: {output_path}")
            print(f"📄 Report can be opened outside VS Code at: {os.path.abspath(output_path)}")
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def create_summary_report(self, all_company_results: Dict, output_path: str):
        """Create summary report for all companies with contextual verification metrics"""
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Title
        title = Paragraph("AI Quality Assessment - Contextual Verification Summary", self.title_style)
        story.append(title)
        
        # Summary table with contextual metrics
        summary_data = [
            ['Company', 'Frontend', 'Memo', 'Overall', 'Status', 'Contextual', 'Verified', 'Sources']
        ]
        
        for company_name, results in all_company_results.items():
            try:
                # Safe calculation of scores
                frontend_results = results.get('frontend_results', {})
                memo_results = results.get('memo_results', {})
                
                frontend_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in frontend_results.values()]
                frontend_scores = [s for s in frontend_scores if isinstance(s, (int, float))]
                frontend_avg = sum(frontend_scores) / len(frontend_scores) if frontend_scores else 0
                
                memo_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in memo_results.values()]
                memo_scores = [s for s in memo_scores if isinstance(s, (int, float))]
                memo_avg = sum(memo_scores) / len(memo_scores) if memo_scores else 0
                
                overall = (frontend_avg + memo_avg) / 2 if (frontend_avg + memo_avg) > 0 else 0
                
                # Status based on score
                status = 'PASS' if overall >= 50 else 'FAIL'
                
                # Contextual metrics
                contextual_count = sum(1 for r in frontend_results.values() if r.get('contextual_match'))
                total_frontend = len(frontend_results) if frontend_results else 1
                contextual_str = f"{contextual_count}/{total_frontend}"
                
                # Verified correct count
                verified_count = sum(1 for r in memo_results.values() if r.get('wrong_info') == 'None')
                total_memo = len(memo_results) if memo_results else 1
                verified_str = f"{verified_count}/{total_memo}"
                
                # Count unique source files referenced
                all_results = {**frontend_results, **memo_results}
                source_files_used = len(set(
                    self._safe_get_value(r, 'source_file', 'N/A') 
                    for r in all_results.values() 
                    if self._safe_get_value(r, 'source_file') not in [None, 'N/A', 'None']
                ))
                source_files_str = str(source_files_used) if source_files_used > 0 else 'N/A'
                
                summary_data.append([
                    company_name,
                    f"{frontend_avg:.1f}",
                    f"{memo_avg:.1f}",
                    f"{overall:.1f}",
                    status,
                    contextual_str,
                    verified_str,
                    source_files_str
                ])
                
            except Exception as e:
                print(f"      ⚠️ Error processing summary for {company_name}: {e}")
                summary_data.append([
                    company_name,
                    'Error',
                    'Error',
                    '0.0',
                    'FAIL',
                    '0/0',
                    '0/0',
                    'N/A'
                ])
        
        # Create summary table
        col_widths = [1.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.6*inch]
        summary_table = Table(summary_data, colWidths=col_widths)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        # Color code based on status
        for i, (company_name, results) in enumerate(all_company_results.items(), 1):
            try:
                frontend_results = results.get('frontend_results', {})
                memo_results = results.get('memo_results', {})
                
                frontend_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in frontend_results.values()]
                frontend_scores = [s for s in frontend_scores if isinstance(s, (int, float))]
                frontend_avg = sum(frontend_scores) / len(frontend_scores) if frontend_scores else 0
                
                memo_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in memo_results.values()]
                memo_scores = [s for s in memo_scores if isinstance(s, (int, float))]
                memo_avg = sum(memo_scores) / len(memo_scores) if memo_scores else 0
                
                overall = (frontend_avg + memo_avg) / 2 if (frontend_avg + memo_avg) > 0 else 0
                
                if overall >= 50:
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
                    ]))
                else:
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                    ]))
            except Exception:
                # Default to red for errors
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                ]))
        
        story.append(summary_table)
        
        # Enhanced statistics
        story.append(Spacer(1, 30))
        try:
            total_companies = len(all_company_results)
            passed_companies = 0
            total_contextual_matches = 0
            total_verified_sections = 0
            total_source_files_used = 0
            total_pdf_refs = 0
            total_pptx_refs = 0
            
            for results in all_company_results.values():
                try:
                    frontend_results = results.get('frontend_results', {})
                    memo_results = results.get('memo_results', {})
                    
                    # Calculate overall score
                    frontend_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in frontend_results.values()]
                    frontend_scores = [s for s in frontend_scores if isinstance(s, (int, float))]
                    frontend_avg = sum(frontend_scores) / len(frontend_scores) if frontend_scores else 0
                    
                    memo_scores = [self._safe_get_value(r, 'accuracy_score', 0) for r in memo_results.values()]
                    memo_scores = [s for s in memo_scores if isinstance(s, (int, float))]
                    memo_avg = sum(memo_scores) / len(memo_scores) if memo_scores else 0
                    
                    overall = (frontend_avg + memo_avg) / 2 if (frontend_avg + memo_avg) > 0 else 0
                    
                    if overall >= 50:
                        passed_companies += 1
                    
                    # Count contextual matches and verified sections
                    total_contextual_matches += sum(1 for r in frontend_results.values() if r.get('contextual_match'))
                    total_verified_sections += sum(1 for r in memo_results.values() if r.get('wrong_info') == 'None')
                    
                    # Count source files and types
                    all_results = {**frontend_results, **memo_results}
                    source_files_used = len(set(
                        self._safe_get_value(r, 'source_file', 'N/A') 
                        for r in all_results.values() 
                        if self._safe_get_value(r, 'source_file') not in [None, 'N/A', 'None']
                    ))
                    total_source_files_used += source_files_used
                    
                    # Count PDF vs PPTX references
                    for r in all_results.values():
                        source_file = self._safe_get_value(r, 'source_file', '')
                        if source_file and source_file not in [None, 'N/A', 'None']:
                            source_lower = str(source_file).lower()
                            if any(indicator in source_lower for indicator in ['pitch', 'deck', 'presentation', 'slide']):
                                total_pptx_refs += 1
                            else:
                                total_pdf_refs += 1
                    
                except Exception as e:
                    print(f"      ⚠️ Error calculating stats for company: {e}")
                    continue
            
            pass_rate = (passed_companies / total_companies * 100) if total_companies > 0 else 0
            
            stats_text = f"""
            <b>Contextual Verification Statistics:</b><br/>
            Total Companies Assessed: {total_companies}<br/>
            Companies Passed: {passed_companies}<br/>
            Pass Rate: {pass_rate:.1f}%<br/>
            Total Contextual Matches: {total_contextual_matches}<br/>
            Total Verified Sections: {total_verified_sections}<br/>
            Total Source Files Referenced: {total_source_files_used}<br/>
            PDF Pages Referenced: {total_pdf_refs}<br/>
            PPTX Slides Referenced: {total_pptx_refs}<br/>
            <br/>
            <b>Assessment Method:</b><br/>
            • Contextual Verification: Uses semantic understanding vs exact matching<br/>
            • Source Context Analysis: Verifies claims against relevant document sections<br/>
            • Multi-Format Support: Handles both PDF documents and PPTX presentations<br/>
            • Fact-Checking: Identifies actual inaccuracies in investment memos<br/>
            • Source Tracking: Links all findings back to specific pages or slides<br/>
            <br/>
            <b>Quality Indicators:</b><br/>
            • High contextual match rate indicates robust semantic understanding<br/>
            • Verified sections show memo accuracy against source documents<br/>
            • Source file references enable manual verification and debugging<br/>
            • Multi-format tracking supports diverse document types<br/>
            • Contextual approach reduces false negatives from formatting differences
            """
            
        except Exception as e:
            print(f"      ⚠️ Error calculating overall statistics: {e}")
            stats_text = f"""
            <b>Statistics Error:</b><br/>
            There was an error calculating overall statistics.<br/>
            Error: {str(e)[:200]}...<br/>
            Please review individual company results above.
            """
        
        story.append(Paragraph(stats_text, self.normal_style))
        
        try:
            doc.build(story)
            print(f"✅ Contextual verification summary report generated: {output_path}")
            print(f"📄 Summary report path: {os.path.abspath(output_path)}")
        except Exception as e:
            print(f"❌ Error generating summary report: {e}")