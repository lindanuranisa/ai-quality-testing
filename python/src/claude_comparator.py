import anthropic
import json
from typing import Dict, List, Any, Tuple
import os
from dotenv import load_dotenv
import re

load_dotenv()

class SemanticClaudeComparator:
    def __init__(self, api_key: str = None):
        """Initialize Claude comparator with contextual verification capabilities"""
        try:
            self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            # Initialize client
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
        except Exception as e:
            print(f"Error initializing Claude client: {e}")
            raise
    
    # def test_connection(self):
    #     """Test if Claude API connection works"""
    #     try:
    #         message = self.client.messages.create(
    #             model="claude-3-5-sonnet-20241022",
    #             max_tokens=10,
    #             messages=[{"role": "user", "content": "Hello"}]
    #         )
    #         print("    ✅ Claude API connection successful!")
    #         return True
    #     except Exception as e:
    #         print(f"    ❌ Claude API connection failed: {e}")
    #         return False
    
    def _extract_page_info(self, source_text: str) -> Dict[str, Dict[int, str]]:
        """ENHANCED: Extract page/slide-specific content with source file tracking - CACHED"""
        if hasattr(self, '_cached_page_info'):
            return self._cached_page_info
            
        source_files = {}
        if not source_text:
            self._cached_page_info = source_files
            return source_files
        
        # Look for both PAGE (PDF) and SLIDE (PPTX) markers
        patterns = [
            r'SOURCE_FILE:\s*([^\n]+)\s*\nPAGE\s*(\d+)\n={40,}\n',  # PDF pattern
            r'SOURCE_FILE:\s*([^\n]+)\s*\nSLIDE\s*(\d+)\n={40,}\n'  # PPTX pattern
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, source_text, re.MULTILINE)
            
            for match in matches:
                source_file = match.group(1).strip().lower()
                page_num = int(match.group(2))
                
                if source_file not in source_files:
                    source_files[source_file] = {}
                
                # Extract content after this page/slide marker until next marker
                start_pos = match.end()
                remaining_text = source_text[start_pos:]
                
                # Look for next PAGE or SLIDE marker
                next_match = re.search(r'(SOURCE_FILE:\s*[^\n]+\s*\n(?:PAGE|SLIDE)\s*\d+\n={40,})', remaining_text)
                
                if next_match:
                    end_pos = start_pos + next_match.start()
                    page_content = source_text[start_pos:end_pos]
                else:
                    page_content = remaining_text
                
                source_files[source_file][page_num] = page_content.strip()
        
        # Cache the result
        self._cached_page_info = source_files
        return source_files
    
    def _create_contextual_chunk(self, field_name: str, ai_value: str, source_text: str, max_chars: int = 20000) -> str:
        """ENHANCED: Create contextual chunk based on field relevance and semantic similarity"""
        if not source_text:
            return ""
        
        if len(source_text) <= max_chars:
            return source_text
        
        # Create comprehensive search terms based on field and value
        search_terms = []
        
        # Extract terms from AI value
        if ai_value and ai_value != "N/A":
            # Extract meaningful terms from the AI value
            terms = re.findall(r'\b[A-Za-z]{3,}\b|\$[\d,]+(?:\.\d+)?[MBK]?|\b\d{4}\b|\b\d+\b', str(ai_value))
            search_terms.extend(terms)
            
            # Add partial matches for company names, emails, etc.
            if '@' in str(ai_value):  # Email
                search_terms.extend(str(ai_value).split('@'))
            if '.' in str(ai_value) and len(str(ai_value)) < 50:  # Might be domain or decimal
                search_terms.extend(str(ai_value).split('.'))
        
        # Add field-specific context terms
        field_context = {
            'company_name': ['company', 'corporation', 'inc', 'llc', 'ltd', 'business', 'startup', 'firm'],
            'industry': ['industry', 'sector', 'market', 'vertical', 'space', 'domain', 'field'],
            'location': ['located', 'headquarters', 'based', 'address', 'city', 'state', 'country', 'office'],
            'founders': ['founder', 'co-founder', 'ceo', 'founder', 'started', 'established', 'created'],
            'founder_email': ['email', 'contact', '@', 'reach', 'founder', 'ceo'],
            'year_founded': ['founded', 'established', 'started', 'incorporated', 'began', 'launched'],
            'funding_stage': ['stage', 'funding', 'round', 'series', 'seed', 'pre-seed', 'growth'],
            'latest_valuation': ['valuation', 'valued', 'worth', 'value', 'post-money', 'pre-money'],
            'fund_raise_target': ['raise', 'raising', 'target', 'seeking', 'funding', 'round'],
            'amount_raised': ['raised', 'funding', 'investment', 'capital', 'money'],
            'revenue': ['revenue', 'income', 'sales', 'earnings', 'arr', 'mrr'],
            'list_of_investors': ['investor', 'investors', 'backed', 'funding', 'investment'],
            'lead_investor': ['lead', 'leading', 'investor', 'primary'],
            'verticals': ['vertical', 'verticals', 'market', 'markets', 'sector', 'focus']
        }
        
        # Add field-specific terms
        if field_name.lower() in field_context:
            search_terms.extend(field_context[field_name.lower()])
        
        # Generic business terms that are often relevant
        search_terms.extend(['company', 'business', 'startup', 'founded', 'ceo', 'team'])
        
        # Create sections with contextual scoring
        sections = re.split(r'\n\s*\n|\n={3,}|\n-{3,}', source_text)
        scored_sections = []
        
        search_terms_lower = [term.lower() for term in search_terms if term and len(term) > 2]
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 30:  # Skip very short sections
                continue
                
            section_lower = section.lower()
            score = 0
            
            # Term matching with different weights
            for term in search_terms_lower:
                count = section_lower.count(term)
                if count > 0:
                    # Higher weight for exact AI value matches
                    if ai_value and term in str(ai_value).lower():
                        score += count * 5
                    # Medium weight for field-related terms
                    elif field_name.lower() in field_context and term in field_context[field_name.lower()]:
                        score += count * 3
                    # Lower weight for general business terms
                    else:
                        score += count * 1
            
            # Boost sections with structured data patterns
            if re.search(r'\$[\d,]+(?:\.\d+)?[MBK]?', section):  # Money amounts
                score += 10
            if re.search(r'\b\d{4}\b', section):  # Years
                score += 5
            if re.search(r'[A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})', section):  # Locations
                score += 5
            if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', section):  # Emails
                score += 8
            if re.search(r'(?:Series [A-Z]|Seed|Pre-seed)', section, re.IGNORECASE):  # Funding stages
                score += 7
            
            scored_sections.append((score, i, section))
        
        # Sort by score and select top sections
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        # Build contextual chunk
        selected_text = ""
        used_chars = 0
        sections_used = 0
        
        for score, idx, section in scored_sections:
            if used_chars + len(section) <= max_chars and sections_used < 15:  # Limit sections
                selected_text += section + "\n\n"
                used_chars += len(section) + 2
                sections_used += 1
            else:
                break
        
        # If we didn't get enough relevant content, add some general context
        if used_chars < max_chars * 0.4:
            remaining_chars = max_chars - used_chars
            general_context = source_text[:remaining_chars]
            selected_text = general_context + "\n\n[...ADDITIONAL RELEVANT CONTENT...]\n\n" + selected_text
        
        return selected_text.strip()
    
    def _find_content_in_pages(self, content: str, source_files: Dict[str, Dict[int, str]]) -> Tuple[str, int]:
        """ENHANCED: Find content in source files using contextual matching (handles both pages and slides)"""
        if not content or not source_files or content.lower() in ['n/a', 'not found', 'error']:
            return None, None
        
        content_lower = content.lower().strip()
        
        # Extract key terms from content for better matching
        key_terms = re.findall(r'\b[A-Za-z]{3,}\b|\$[\d,]+(?:\.\d+)?[MBK]?|\b\d{4}\b', content_lower)
        
        best_source = None
        best_page = None
        best_score = 0
        
        for source_file, pages in source_files.items():
            for page_num, page_content in pages.items():
                page_content_lower = page_content.lower()
                
                # Multiple matching strategies
                scores = []
                
                # Exact substring match (highest weight)
                if content_lower in page_content_lower:
                    scores.append(100)
                
                # Term-based matching
                if key_terms:
                    term_matches = sum(1 for term in key_terms if term in page_content_lower)
                    term_score = (term_matches / len(key_terms)) * 80 if key_terms else 0
                    scores.append(term_score)
                
                # Partial word matching
                content_words = content_lower.split()[:5]  # First 5 words are most important
                if content_words:
                    word_matches = sum(1 for word in content_words if len(word) > 2 and word in page_content_lower)
                    word_score = (word_matches / len(content_words)) * 60 if content_words else 0
                    scores.append(word_score)
                
                # Pattern-based matching for specific data types
                if re.search(r'\$[\d,]+', content):  # Money amount
                    if re.search(r'\$[\d,]+', page_content):
                        scores.append(70)
                
                if re.search(r'\b\d{4}\b', content):  # Year
                    if re.search(r'\b\d{4}\b', page_content):
                        scores.append(60)
                
                if '@' in content:  # Email
                    if '@' in page_content:
                        scores.append(80)
                
                # Take the best score for this page
                page_score = max(scores) if scores else 0
                
                if page_score > best_score and page_score > 25:  # Minimum threshold
                    best_score = page_score
                    best_source = source_file
                    best_page = page_num
        
        return best_source, best_page
    
    def batch_compare_frontend_fields(self, 
                                    frontend_data: Dict,
                                    source_text: str,
                                    fields: List[str]) -> Dict[str, Dict]:
        """CONTEXTUAL: Process fields with enhanced contextual verification"""
        results = {}
        
        print(f"      🧠 Contextual verification of {len(fields)} fields:")
        
        # Extract page info once
        source_files = self._extract_page_info(source_text)
        
        # Process fields in smaller batches for better accuracy
        batch_size = 4  # Smaller batches for more focused analysis
        field_batches = [fields[i:i + batch_size] for i in range(0, len(fields), batch_size)]
        
        for batch_num, field_batch in enumerate(field_batches, 1):
            print(f"        📦 Processing batch {batch_num}/{len(field_batches)} ({len(field_batch)} fields)")
            
            # Process each field individually for better context
            for field in field_batch:
                ai_value = frontend_data.get(field, "N/A")
                
                # Create contextual chunk specific to this field
                contextual_chunk = self._create_contextual_chunk(field, ai_value, source_text, max_chars=15000)
                
                # Enhanced contextual verification prompt
                prompt = f"""You are verifying AI-generated data against source documents using contextual understanding.

FIELD TO VERIFY: {field}
AI-GENERATED VALUE: "{ai_value}"

RELEVANT SOURCE CONTEXT:
{contextual_chunk}

TASK: Verify if the AI value is correct based on the source context. Use semantic understanding - values don't need to match exactly if they mean the same thing contextually.

EXAMPLES:
- If AI says "John Smith" and source says "J. Smith" or "John Smith, CEO" → CORRECT
- If AI says "San Francisco, CA" and source says "SF" or "San Francisco" → CORRECT  
- If AI says "$5M" and source says "5 million dollars" → CORRECT
- If AI says "2020" and source shows founding timeline in 2020 → CORRECT

Return JSON only:
{{
  "accuracy_score": 0-100,
  "source_value": "what the source actually contains (or 'Not found')",
  "citation": "specific quote from source that supports your finding",
  "contextual_match": true/false
}}"""
                
                try:
                    message = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    response_text = message.content[0].text.strip()
                    result = self._safe_json_parse(response_text)
                    
                    # Process result
                    result['field_name'] = field
                    result['ai_value'] = ai_value
                    
                    # Enhanced source location finding
                    source_file, page_num = None, None
                    if result.get('citation') and source_files:
                        source_file, page_num = self._find_content_in_pages(result['citation'], source_files)
                    elif result.get('source_value') and source_files and result['source_value'] != 'Not found':
                        source_file, page_num = self._find_content_in_pages(result['source_value'], source_files)
                    
                    result['source_file'] = source_file
                    result['page_number'] = page_num
                    
                    # Score-based status
                    score = result.get('accuracy_score', 0)
                    result['status'] = 'PASS' if score >= 50 else 'FAIL'
                    
                    # Add contextual matching info
                    if result.get('contextual_match'):
                        result['verification_type'] = 'Contextual Match'
                    else:
                        result['verification_type'] = 'Direct Match' if score >= 80 else 'No Match'
                    
                    results[field] = result
                    print(f"          ✓ {field}: {score}/100 ({result['status']}) - {result.get('verification_type', 'Unknown')}")
                    
                except Exception as e:
                    print(f"          ❌ Error processing {field}: {e}")
                    results[field] = self._create_fallback_result(field, ai_value, f"API error: {e}")
        
        # Calculate summary
        valid_scores = [r['accuracy_score'] for r in results.values() if isinstance(r.get('accuracy_score'), (int, float))]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        passed = sum(1 for r in results.values() if r.get('status') == 'PASS')
        contextual_matches = sum(1 for r in results.values() if r.get('contextual_match'))
        
        print(f"      📊 Contextual Results: {avg_score:.1f}/100 avg, {passed}/{len(fields)} passed, {contextual_matches} contextual matches")
        
        return results
    
    def _safe_json_parse(self, response_text: str) -> Dict:
        """Safely parse JSON with multiple fallback strategies"""
        if not response_text:
            return {}
        
        # Strategy 1: Direct JSON parse
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON block in response
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```', 
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested braces
            r'(\{[^{}]*\})',  # Simple braces
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Extract key-value pairs manually
        try:
            result = {}
            
            # Look for accuracy_score
            score_match = re.search(r'"accuracy_score":\s*(\d+)', response_text)
            result['accuracy_score'] = int(score_match.group(1)) if score_match else 0
            
            # Look for source_value
            source_match = re.search(r'"source_value":\s*"([^"]*)"', response_text)
            result['source_value'] = source_match.group(1) if source_match else "Not found"
            
            # Look for citation
            citation_match = re.search(r'"citation":\s*"([^"]*)"', response_text)
            result['citation'] = citation_match.group(1) if citation_match else ""
            
            # Look for contextual_match
            contextual_match = re.search(r'"contextual_match":\s*(true|false)', response_text)
            result['contextual_match'] = contextual_match.group(1) == 'true' if contextual_match else False
            
            # Look for status/wrong_info/correct_info for memo
            status_match = re.search(r'"status":\s*"([^"]*)"', response_text)
            result['status'] = status_match.group(1) if status_match else ("PASS" if result['accuracy_score'] >= 50 else "FAIL")
            
            wrong_match = re.search(r'"wrong_info":\s*"([^"]*)"', response_text)
            if wrong_match:
                result['wrong_info'] = wrong_match.group(1)
            
            correct_match = re.search(r'"correct_info":\s*"([^"]*)"', response_text)
            if correct_match:
                result['correct_info'] = correct_match.group(1)
            
            return result
        except:
            pass
        
        # Strategy 4: Return fallback
        return {
            "accuracy_score": 0,
            "status": "FAIL", 
            "source_value": f"Parse error: {response_text[:100]}...",
            "citation": "",
            "contextual_match": False
        }
    
    def batch_compare_memo_sections(self,
                                   memo_sections: Dict[str, str],
                                   source_text: str,
                                   pdf_sections: List[str] = None) -> Dict[str, Dict]:
        """FIXED: Enhanced memo fact-checking with contextual understanding"""
        results = {}
        
        # IMPROVED: Better section filtering with debugging
        print(f"      🔍 DEBUG: Total sections received: {len(memo_sections)}")
        for section_name, content in memo_sections.items():
            content_length = len(content.strip()) if content else 0
            print(f"        📋 {section_name}: {content_length} chars")
        
        # FIXED: More lenient filtering - accept sections with minimal content
        non_empty_sections = {}
        for k, v in memo_sections.items():
            if v and v.strip() and len(v.strip()) >= 5:  # Very minimal requirement
                non_empty_sections[k] = v
            else:
                print(f"        ⚠️ Filtering out section '{k}': {len(v.strip()) if v else 0} chars")
        
        print(f"      🧠 Contextual memo fact-checking of {len(non_empty_sections)} non-empty sections:")
        
        if not non_empty_sections:
            print(f"      ⚠️ No non-empty sections found!")
            # Still process all sections to give them proper status
            for section_name, section_content in memo_sections.items():
                results[section_name] = {
                    "accuracy_score": 70,
                    "status": "PASS",
                    "wrong_info": "Section is empty",
                    "correct_info": "No content to verify",
                    "citation": "",
                    "section_name": section_name,
                    "source_file": None,
                    "page_number": None,
                    "verification_type": "Empty Section"
                }
            return results
        
        # Extract page info once
        source_files = self._extract_page_info(source_text)
        
        # Process each section individually for contextual analysis
        for section_name, section_content in non_empty_sections.items():
            print(f"        🔍 Fact-checking {section_name} ({len(section_content.strip())} chars)...")
            
            try:
                # Extract key claims for contextual search
                key_claims = self._extract_contextual_claims(section_content)
                
                # Create contextual chunk based on memo content
                search_terms = []
                for claim in key_claims:
                    if claim:
                        terms = re.findall(r'\b[A-Za-z]{3,}\b|\$[\d,]+(?:\.\d+)?[MBK]?|\b\d{4}\b', str(claim))
                        search_terms.extend(terms[:8])
                
                # Get contextual chunk focused on this section's claims
                contextual_chunk = self._create_contextual_chunk(section_name, ' '.join(key_claims), source_text, max_chars=18000)
                
                # Enhanced contextual fact-checking prompt
                prompt = f"""You are fact-checking an investment memo section against source documents using contextual understanding.

MEMO SECTION: {section_name}
MEMO CONTENT:
{section_content[:600]}

SOURCE DOCUMENTS CONTEXT:
{contextual_chunk}

TASK: Find any factually incorrect information in the memo by comparing it contextually to the source documents. Use semantic understanding - look for contradictions in meaning, not just exact word matches.

IMPORTANT: 
- If no factual errors are found, set accuracy_score to 85+ and wrong_info to "None"
- Look for contextual contradictions (e.g., different years, amounts, names, stages)
- Consider synonymous terms as correct (e.g., "CEO" vs "Chief Executive")

Return JSON only:
{{
  "accuracy_score": 0-100,
  "wrong_info": "specific incorrect information found, or 'None' if no errors",
  "correct_info": "what the source documents actually say, or 'Verified correct' if no errors",
  "citation": "specific quote from source that contradicts or supports the memo"
}}"""
                
                try:
                    message = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=600,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    response_text = message.content[0].text.strip()
                    result = self._safe_json_parse(response_text)
                    
                    # Process result
                    result['section_name'] = section_name
                    result['ai_content_length'] = len(section_content)
                    
                    # Enhanced source location finding
                    source_file, page_num = None, None
                    if result.get('citation') and source_files:
                        source_file, page_num = self._find_content_in_pages(result['citation'], source_files)
                    
                    result['source_file'] = source_file
                    result['page_number'] = page_num
                    
                    # Enhanced scoring logic
                    accuracy_score = result.get('accuracy_score', 0)
                    wrong_info = result.get('wrong_info', '').strip().lower()
                    
                    # Boost score if no errors found
                    if wrong_info in ['none', 'no errors', 'no wrong information', 'verified correct', '']:
                        accuracy_score = max(85, accuracy_score)
                        result['accuracy_score'] = accuracy_score
                        result['wrong_info'] = 'None'
                        if not result.get('correct_info') or result.get('correct_info') == 'Could not parse response':
                            result['correct_info'] = 'Verified correct'
                        result['verification_type'] = 'Contextually Verified'
                    else:
                        result['verification_type'] = 'Issues Found'
                    
                    result['status'] = 'PASS' if accuracy_score >= 50 else 'FAIL'
                    
                    results[section_name] = result
                    print(f"          ✓ {section_name}: {accuracy_score}/100 ({result['status']}) - {result.get('verification_type', 'Unknown')}")
                    
                except Exception as e:
                    print(f"          ❌ API error for {section_name}: {e}")
                    results[section_name] = self._create_memo_fallback(section_name, f"API error: {e}")
                    
            except Exception as e:
                print(f"          ❌ Error processing {section_name}: {e}")
                results[section_name] = self._create_memo_fallback(section_name, f"Processing error: {e}")
        
        # IMPROVED: Handle remaining sections (including empty ones)
        for section_name, section_content in memo_sections.items():
            if section_name not in results:
                if section_content and section_content.strip() and len(section_content.strip()) >= 5:
                    # Should have been processed above, this is a fallback
                    results[section_name] = self._create_memo_fallback(section_name, "Processing error")
                    print(f"          ⚠️ Fallback processing for {section_name}")
                else:
                    # Truly empty sections
                    results[section_name] = {
                        "accuracy_score": 70,
                        "status": "PASS",
                        "wrong_info": "Section is empty",
                        "correct_info": "No content to verify",
                        "citation": "",
                        "section_name": section_name,
                        "source_file": None,
                        "page_number": None,
                        "verification_type": "Empty Section"
                    }
                    print(f"          📝 Empty section: {section_name}")
        
        # Calculate summary
        valid_scores = [r['accuracy_score'] for r in results.values() if isinstance(r.get('accuracy_score'), (int, float))]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        passed = sum(1 for r in results.values() if r.get('status') == 'PASS')
        verified_correct = sum(1 for r in results.values() if r.get('wrong_info') == 'None')
        
        print(f"      📊 Contextual Memo Results: {avg_score:.1f}/100 avg, {passed}/{len(results)} passed, {verified_correct} verified correct")
        
        return results
    
    def _extract_contextual_claims(self, section_content: str) -> List[str]:
        """Extract key factual claims from memo section for contextual verification"""
        claims = []
        
        if not section_content:
            return claims
        
        # Split into sentences and paragraphs
        sentences = re.split(r'[.!?]+', section_content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Skip very short sentences
                continue
                
            # Check if sentence contains verifiable facts
            has_verifiable_facts = False
            
            # Financial data
            if re.search(r'\$[\d,]+(?:\.\d+)?[MBK]?', sentence):
                has_verifiable_facts = True
            
            # Years and dates
            if re.search(r'\b\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b', sentence):
                has_verifiable_facts = True
            
            # Percentages and metrics
            if re.search(r'\d+(?:\.\d+)?%|\d+(?:,\d{3})*\s*(?:users|customers|employees)', sentence):
                has_verifiable_facts = True
            
            # Business entities and roles
            if re.search(r'\b(?:founded|headquarters|CEO|CTO|Series [A-Z]|raised|funding|valuation|employees|customers|revenue|located|based)\b', sentence, re.IGNORECASE):
                has_verifiable_facts = True
            
            # Locations and addresses
            if re.search(r'\b[A-Z][a-zA-Z]+,\s*[A-Z]{2}\b', sentence):
                has_verifiable_facts = True
            
            # Company names and proper nouns
            if re.search(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+(?:Inc|LLC|Corp|Ltd|Company)\b', sentence):
                has_verifiable_facts = True
            
            if has_verifiable_facts:
                claims.append(sentence)
        
        return claims[:8]  # Limit to 8 claims for token efficiency
    
    def _create_fallback_result(self, field_name: str, ai_value: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback result when API fails"""
        return {
            "accuracy_score": 0,
            "status": "FAIL",
            "semantic_match_found": False,
            "source_value": f"Error: {error_msg}",
            "citation": "",
            "confidence": "LOW",
            "ai_value": ai_value,
            "field_name": field_name,
            "explanation": error_msg,
            "source_file": None,
            "page_number": None,
            "verification_type": "Error",
            "contextual_match": False
        }
    
    def _create_memo_fallback(self, section_name: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback result for memo comparison"""
        return {
            "accuracy_score": 0,
            "status": "FAIL",
            "wrong_info": f"Error: {error_msg}",
            "correct_info": "N/A",
            "citation": "",
            "section_name": section_name,
            "explanation": error_msg,
            "source_file": None,
            "page_number": None,
            "verification_type": "Error"
        }
    
    # Legacy methods for backward compatibility
    def batch_compare_frontend_semantic(self, *args, **kwargs):
        """Legacy method - redirects to contextual processing"""
        return self.batch_compare_frontend_fields(*args, **kwargs)
    
    def batch_compare_memo_semantic(self, *args, **kwargs):
        """Legacy method - redirects to contextual fact-checking"""
        return self.batch_compare_memo_sections(*args, **kwargs)