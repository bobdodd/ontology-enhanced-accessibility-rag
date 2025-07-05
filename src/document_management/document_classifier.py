"""
Document type classification system for identifying and categorizing different types of accessibility documents.
"""

import re
import os
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from config.constants import (
    DocumentType, 
    AuthorityLevel, 
    DOCUMENT_TYPE_PATTERNS, 
    EXPERT_AUTHORS
)


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: DocumentType
    confidence: float
    authority_level: AuthorityLevel
    detected_features: Dict[str, List[str]]
    reasoning: str


class DocumentClassifier:
    """
    Classifies documents into types based on filename, metadata, content, and author analysis.
    """
    
    def __init__(self):
        self.classification_rules = self._build_classification_rules()
    
    def classify_document(
        self, 
        filepath: str, 
        content: str, 
        metadata: Dict, 
        authors: str = ""
    ) -> ClassificationResult:
        """
        Classify a document based on multiple signals.
        
        Args:
            filepath: Path to the document file
            content: Document text content
            metadata: Document metadata dictionary
            authors: Author names string
            
        Returns:
            ClassificationResult with type, confidence, and reasoning
        """
        filename = os.path.basename(filepath).lower()
        content_lower = content.lower()
        metadata_text = " ".join(str(v) for v in metadata.values()).lower()
        
        # Collect classification signals
        signals = {
            "filename": self._analyze_filename(filename),
            "metadata": self._analyze_metadata(metadata_text),
            "content": self._analyze_content(content_lower),
            "author": self._analyze_authors(authors),
            "structure": self._analyze_document_structure(content)
        }
        
        # Determine document type
        doc_type, confidence = self._determine_document_type(signals)
        
        # Determine authority level
        authority_level = self._determine_authority_level(doc_type, authors, metadata, content)
        
        # Build reasoning
        reasoning = self._build_reasoning(signals, doc_type, authority_level)
        
        return ClassificationResult(
            document_type=doc_type,
            confidence=confidence,
            authority_level=authority_level,
            detected_features=signals,
            reasoning=reasoning
        )
    
    def _analyze_filename(self, filename: str) -> Dict[str, float]:
        """Analyze filename for document type indicators."""
        scores = {}
        
        # Academic paper indicators
        if re.search(r'\d{4}\.\d{4}\.\d{4}', filename):  # ACM DOI pattern
            scores['academic_paper'] = 0.8
        if re.search(r'(ieee|acm|chi|assets|w4a)', filename):
            scores['academic_paper'] = scores.get('academic_paper', 0) + 0.6
        
        # Standards document indicators
        if re.search(r'(wcag|section.?508|en.?301)', filename):
            scores['standards_document'] = 0.9
        if re.search(r'(w3c|iso|standard|spec)', filename):
            scores['standards_document'] = scores.get('standards_document', 0) + 0.5
        
        # Blog/article indicators
        if re.search(r'(blog|post|article)', filename):
            scores['expert_blog'] = 0.6
        
        # Audit/ticket indicators
        if re.search(r'(audit|ticket|issue|violation)', filename):
            scores['audit_ticket'] = 0.7
        
        # Testing transcript indicators
        if re.search(r'(test|transcript|recording|session)', filename):
            scores['testing_transcript'] = 0.6
        
        return scores
    
    def _analyze_metadata(self, metadata_text: str) -> Dict[str, float]:
        """Analyze metadata for document type indicators."""
        scores = {}
        
        # Academic paper indicators
        academic_indicators = ['doi:', 'abstract:', 'keywords:', 'acm', 'ieee', 'conference', 'proceedings']
        academic_score = sum(0.2 for indicator in academic_indicators if indicator in metadata_text)
        if academic_score > 0:
            scores['academic_paper'] = min(academic_score, 1.0)
        
        # Standards indicators
        standards_indicators = ['w3c', 'iso', 'standard', 'specification', 'recommendation']
        standards_score = sum(0.3 for indicator in standards_indicators if indicator in metadata_text)
        if standards_score > 0:
            scores['standards_document'] = min(standards_score, 1.0)
        
        # Blog indicators
        blog_indicators = ['blog', 'post', 'article', 'medium', 'dev.to']
        blog_score = sum(0.3 for indicator in blog_indicators if indicator in metadata_text)
        if blog_score > 0:
            scores['expert_blog'] = min(blog_score, 1.0)
        
        return scores
    
    def _analyze_content(self, content: str) -> Dict[str, float]:
        """Analyze content for document type indicators."""
        scores = {}
        
        # Academic paper patterns
        academic_patterns = [
            r'\babstract\b.*?\bkeywords\b',
            r'\bmethodology\b.*?\bresults\b',
            r'\bexperiment\b.*?\bconclusion\b',
            r'\breferences\b.*?\bcitation\b',
            r'\bp\s*<\s*0\.\d+',  # statistical significance
            r'\bn\s*=\s*\d+',     # sample size
        ]
        academic_score = sum(0.15 for pattern in academic_patterns if re.search(pattern, content))
        if academic_score > 0:
            scores['academic_paper'] = min(academic_score, 1.0)
        
        # Standards document patterns
        standards_patterns = [
            r'\b(must|shall|should|may)\b.*\b(conformance|compliance)\b',
            r'\bsuccess criteri[ao]n?\b',
            r'\blevel\s+(a|aa|aaa)\b',
            r'\bnormative\b.*\binformative\b',
            r'\bthis\s+(standard|specification|recommendation)\b'
        ]
        standards_score = sum(0.2 for pattern in standards_patterns if re.search(pattern, content))
        if standards_score > 0:
            scores['standards_document'] = min(standards_score, 1.0)
        
        # Blog/expert content patterns
        blog_patterns = [
            r'\bin this (post|article)\b',
            r'\bi (recommend|suggest|think)\b',
            r'\bbest practice\b',
            r'\btip\b.*\btrick\b',
            r'\bhow to\b.*\bstep\b'
        ]
        blog_score = sum(0.2 for pattern in blog_patterns if re.search(pattern, content))
        if blog_score > 0:
            scores['expert_blog'] = min(blog_score, 1.0)
        
        # Audit ticket patterns
        audit_patterns = [
            r'\b(violation|issue|error|warning)\b.*\b(found|detected|identified)\b',
            r'\bremediation\b.*\bsteps?\b',
            r'\bpriority\b.*\b(high|medium|low|critical)\b',
            r'\bwcag\s+\d+\.\d+\.\d+\b',
            r'\bassistive technology\b.*\b(fails?|problem)\b'
        ]
        audit_score = sum(0.2 for pattern in audit_patterns if re.search(pattern, content))
        if audit_score > 0:
            scores['audit_ticket'] = min(audit_score, 1.0)
        
        # Testing transcript patterns
        testing_patterns = [
            r'\b(user|tester)\b.*\b(said|reported|mentioned)\b',
            r'\bscreen reader\b.*\b(announced|read|spoke)\b',
            r'\bnavigation\b.*\b(successful|failed|difficult)\b',
            r'\btask\b.*\b(completed|failed|abandoned)\b',
            r'\btimestamp\b|\b\d{2}:\d{2}\b'
        ]
        testing_score = sum(0.2 for pattern in testing_patterns if re.search(pattern, content))
        if testing_score > 0:
            scores['testing_transcript'] = min(testing_score, 1.0)
        
        return scores
    
    def _analyze_authors(self, authors: str) -> Dict[str, float]:
        """Analyze authors for expertise indicators."""
        scores = {}
        
        if not authors:
            return scores
        
        # Check against known expert authors
        for expert_name, expert_info in EXPERT_AUTHORS.items():
            if expert_name.lower() in authors.lower():
                # High authority authors typically write expert blogs or standards
                if expert_info["authority"] >= 4:
                    scores['expert_blog'] = 0.8
                    scores['standards_document'] = 0.6
                break
        
        # Academic institution indicators
        academic_indicators = ['university', 'college', 'institute', 'research', 'lab']
        if any(indicator in authors.lower() for indicator in academic_indicators):
            scores['academic_paper'] = 0.5
        
        return scores
    
    def _analyze_document_structure(self, content: str) -> Dict[str, float]:
        """Analyze document structure for type indicators."""
        scores = {}
        
        # Count specific structural elements
        section_headers = len(re.findall(r'\n\s*\d+\.?\s+[A-Z]', content))
        bullet_points = len(re.findall(r'\n\s*[•\-\*]\s+', content))
        numbered_lists = len(re.findall(r'\n\s*\d+\.\s+', content))
        citations = len(re.findall(r'\[\d+\]|\(\d{4}\)', content))
        
        # Academic papers typically have many citations and numbered sections
        if citations > 10 and section_headers > 3:
            scores['academic_paper'] = 0.6
        
        # Standards documents have numbered sections and formal structure
        if section_headers > 5 and numbered_lists > 10:
            scores['standards_document'] = 0.5
        
        # Blog posts typically have bullet points and informal structure
        if bullet_points > 5 and citations < 5:
            scores['expert_blog'] = 0.4
        
        return scores
    
    def _determine_document_type(self, signals: Dict) -> Tuple[DocumentType, float]:
        """Determine document type from all signals."""
        # Aggregate scores for each document type
        type_scores = {}
        
        for signal_type, signal_scores in signals.items():
            for doc_type, score in signal_scores.items():
                if doc_type in type_scores:
                    type_scores[doc_type] += score * self._get_signal_weight(signal_type)
                else:
                    type_scores[doc_type] = score * self._get_signal_weight(signal_type)
        
        if not type_scores:
            return DocumentType.UNKNOWN, 0.0
        
        # Find the highest scoring type
        best_type = max(type_scores.items(), key=lambda x: x[1])
        doc_type_str = best_type[0]
        confidence = min(best_type[1], 1.0)
        
        # Convert string to DocumentType enum
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            # Handle legacy string values
            type_mapping = {
                'academic_paper': DocumentType.ACADEMIC_PAPER,
                'standards_document': DocumentType.STANDARDS_DOCUMENT,
                'expert_blog': DocumentType.EXPERT_BLOG,
                'audit_ticket': DocumentType.AUDIT_TICKET,
                'testing_transcript': DocumentType.TESTING_TRANSCRIPT
            }
            doc_type = type_mapping.get(doc_type_str, DocumentType.UNKNOWN)
        
        return doc_type, confidence
    
    def _get_signal_weight(self, signal_type: str) -> float:
        """Get weight for different signal types."""
        weights = {
            'filename': 0.2,
            'metadata': 0.3,
            'content': 0.4,
            'author': 0.25,
            'structure': 0.15
        }
        return weights.get(signal_type, 0.1)
    
    def _determine_authority_level(
        self, 
        doc_type: DocumentType, 
        authors: str, 
        metadata: Dict, 
        content: str
    ) -> AuthorityLevel:
        """Determine authority level based on document type and authorship."""
        
        # Check for known expert authors
        for expert_name, expert_info in EXPERT_AUTHORS.items():
            if expert_name.lower() in authors.lower():
                if expert_info["authority"] == 5:
                    return AuthorityLevel.NORMATIVE if doc_type == DocumentType.STANDARDS_DOCUMENT else AuthorityLevel.EXPERT_INTERPRETIVE
                elif expert_info["authority"] == 4:
                    return AuthorityLevel.EXPERT_INTERPRETIVE
        
        # Default authority levels by document type
        authority_defaults = {
            DocumentType.STANDARDS_DOCUMENT: AuthorityLevel.NORMATIVE,
            DocumentType.ACADEMIC_PAPER: AuthorityLevel.PEER_REVIEWED,
            DocumentType.EXPERT_BLOG: AuthorityLevel.PROFESSIONAL,
            DocumentType.AUDIT_TICKET: AuthorityLevel.PROFESSIONAL,
            DocumentType.TESTING_TRANSCRIPT: AuthorityLevel.PROFESSIONAL,
            DocumentType.NEWSLETTER: AuthorityLevel.COMMUNITY,
            DocumentType.JOURNAL_ARTICLE: AuthorityLevel.PEER_REVIEWED
        }
        
        return authority_defaults.get(doc_type, AuthorityLevel.UNKNOWN)
    
    def _build_reasoning(
        self, 
        signals: Dict, 
        doc_type: DocumentType, 
        authority_level: AuthorityLevel
    ) -> str:
        """Build human-readable reasoning for the classification."""
        reasons = []
        
        for signal_type, signal_scores in signals.items():
            if signal_scores:
                top_signal = max(signal_scores.items(), key=lambda x: x[1])
                if top_signal[1] > 0.3:
                    reasons.append(f"{signal_type}: {top_signal[0]} (score: {top_signal[1]:.2f})")
        
        reasoning = f"Classified as {doc_type.value} (authority: {authority_level.value}) based on: " + "; ".join(reasons)
        return reasoning
    
    def _build_classification_rules(self) -> Dict:
        """Build classification rules from patterns."""
        # This would be expanded with more sophisticated rule building
        return DOCUMENT_TYPE_PATTERNS