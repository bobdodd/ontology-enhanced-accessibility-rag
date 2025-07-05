"""
Content analyzer for examining existing document collections and extracting patterns.
"""

import json
import re
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from config.constants import DocumentType, EXPERT_AUTHORS
from .document_classifier import DocumentClassifier
from .authority_mapper import AuthorityMapper


@dataclass
class ContentAnalysisResult:
    """Result of content analysis."""
    total_documents: int
    document_type_distribution: Dict[str, int]
    authority_distribution: Dict[str, int]
    common_terms: List[Tuple[str, int]]
    author_analysis: Dict[str, int]
    missing_metadata_fields: List[str]
    recommendations: List[str]


class ContentAnalyzer:
    """
    Analyzes existing document collections to identify patterns and improvement opportunities.
    """
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.authority_mapper = AuthorityMapper()
    
    def analyze_document_collection(self, metadata_file_path: str) -> ContentAnalysisResult:
        """
        Analyze a collection of documents from metadata file.
        
        Args:
            metadata_file_path: Path to the documents metadata JSON file
            
        Returns:
            ContentAnalysisResult with analysis findings
        """
        # Load existing metadata
        try:
            with open(metadata_file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            print(f"Metadata file not found: {metadata_file_path}")
            return self._empty_analysis_result()
        except json.JSONDecodeError:
            print(f"Invalid JSON in metadata file: {metadata_file_path}")
            return self._empty_analysis_result()
        
        if not metadata:
            print("No documents found in metadata file")
            return self._empty_analysis_result()
        
        # Analyze documents
        print(f"Analyzing {len(metadata)} documents...")
        
        # Document type distribution (estimate from current metadata)
        doc_type_dist = self._analyze_document_types(metadata)
        
        # Authority distribution (estimate from authors)
        authority_dist = self._analyze_authority_distribution(metadata)
        
        # Common terms analysis
        common_terms = self._extract_common_terms(metadata)
        
        # Author analysis
        author_analysis = self._analyze_authors(metadata)
        
        # Missing metadata analysis
        missing_fields = self._find_missing_metadata(metadata)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            len(metadata), doc_type_dist, authority_dist, missing_fields
        )
        
        return ContentAnalysisResult(
            total_documents=len(metadata),
            document_type_distribution=doc_type_dist,
            authority_distribution=authority_dist,
            common_terms=common_terms,
            author_analysis=author_analysis,
            missing_metadata_fields=missing_fields,
            recommendations=recommendations
        )
    
    def suggest_ontology_improvements(self, analysis_result: ContentAnalysisResult) -> List[str]:
        """
        Suggest improvements to ontology based on content analysis.
        
        Args:
            analysis_result: Result from content analysis
            
        Returns:
            List of suggested improvements
        """
        suggestions = []
        
        # Analyze common terms for missing ontology concepts
        common_terms = [term for term, count in analysis_result.common_terms[:50]]
        
        # Suggest new concepts based on frequent terms
        accessibility_terms = [
            term for term in common_terms 
            if any(keyword in term.lower() for keyword in [
                'accessibility', 'wcag', 'aria', 'screen', 'keyboard', 
                'color', 'contrast', 'focus', 'navigation', 'usability'
            ])
        ]
        
        if accessibility_terms:
            suggestions.append(
                f"Consider adding these frequent accessibility terms to ontology: {', '.join(accessibility_terms[:10])}"
            )
        
        # Suggest author authority updates
        if analysis_result.author_analysis:
            top_authors = [
                author for author, count in 
                Counter(analysis_result.author_analysis).most_common(10)
                if author not in EXPERT_AUTHORS
            ]
            if top_authors:
                suggestions.append(
                    f"Consider adding these frequent authors to expert database: {', '.join(top_authors[:5])}"
                )
        
        # Suggest document type refinements
        unknown_percentage = (
            analysis_result.document_type_distribution.get('unknown', 0) / 
            analysis_result.total_documents * 100
        )
        if unknown_percentage > 20:
            suggestions.append(
                f"High percentage ({unknown_percentage:.1f}%) of unknown document types. "
                "Consider improving classification rules."
            )
        
        return suggestions
    
    def _analyze_document_types(self, metadata: Dict) -> Dict[str, int]:
        """Analyze document type distribution."""
        type_counts = defaultdict(int)
        
        for doc_path, doc_info in metadata.items():
            # Try to classify based on existing metadata
            title = doc_info.get('title', '')
            authors = doc_info.get('authors', '')
            acm_ref = doc_info.get('acm_reference', '')
            
            # Simple heuristic classification
            if 'WCAG' in acm_ref or 'W3C' in acm_ref:
                doc_type = 'standards_document'
            elif any(expert in authors for expert in EXPERT_AUTHORS.keys()):
                doc_type = 'expert_blog'
            elif 'ACM' in acm_ref or 'Proceedings' in acm_ref:
                doc_type = 'academic_paper'
            elif 'audit' in title.lower() or 'violation' in title.lower():
                doc_type = 'audit_ticket'
            elif 'test' in title.lower() and 'transcript' in title.lower():
                doc_type = 'testing_transcript'
            else:
                doc_type = 'unknown'
            
            type_counts[doc_type] += 1
        
        return dict(type_counts)
    
    def _analyze_authority_distribution(self, metadata: Dict) -> Dict[str, int]:
        """Analyze authority level distribution."""
        authority_counts = defaultdict(int)
        
        for doc_path, doc_info in metadata.items():
            authors = doc_info.get('authors', '')
            
            # Get authority level
            authority_level, confidence = self.authority_mapper.get_document_authority_score(authors)
            authority_counts[authority_level.value] += 1
        
        return dict(authority_counts)
    
    def _extract_common_terms(self, metadata: Dict) -> List[Tuple[str, int]]:
        """Extract common terms from titles and references."""
        all_text = []
        
        for doc_info in metadata.values():
            title = doc_info.get('title', '')
            acm_ref = doc_info.get('acm_reference', '')
            all_text.append(f"{title} {acm_ref}")
        
        # Extract terms
        terms = []
        for text in all_text:
            # Simple term extraction (could be improved with NLP)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            terms.extend(words)
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 
            'did', 'what', 'where', 'when', 'will', 'with', 'have', 'this', 'that',
            'from', 'they', 'she', 'been', 'than', 'said', 'each', 'which', 'their',
            'time', 'way', 'about', 'many', 'then', 'them', 'these', 'so', 'some',
            'her', 'would', 'make', 'like', 'into', 'him', 'has', 'more', 'go',
            'no', 'do', 'does', 'were', 'my', 'very', 'an', 'is', 'it', 'be', 'to',
            'of', 'in', 'a'
        }
        
        filtered_terms = [term for term in terms if term not in stop_words and len(term) > 3]
        
        # Count and return top terms
        term_counts = Counter(filtered_terms)
        return term_counts.most_common(100)
    
    def _analyze_authors(self, metadata: Dict) -> Dict[str, int]:
        """Analyze author frequency."""
        author_counts = defaultdict(int)
        
        for doc_info in metadata.values():
            authors_str = doc_info.get('authors', '')
            if authors_str:
                # Simple author parsing
                authors = re.split(r'[,;&]|\sand\s', authors_str)
                for author in authors:
                    author = author.strip()
                    if author:
                        author_counts[author] += 1
        
        return dict(author_counts)
    
    def _find_missing_metadata(self, metadata: Dict) -> List[str]:
        """Find commonly missing metadata fields."""
        missing_counts = defaultdict(int)
        total_docs = len(metadata)
        
        expected_fields = ['title', 'authors', 'acm_reference', 'added_at', 'chunks_count']
        
        for doc_info in metadata.values():
            for field in expected_fields:
                if not doc_info.get(field):
                    missing_counts[field] += 1
        
        # Return fields missing from >10% of documents
        missing_fields = []
        for field, count in missing_counts.items():
            percentage = (count / total_docs) * 100
            if percentage > 10:
                missing_fields.append(f"{field} ({percentage:.1f}% missing)")
        
        return missing_fields
    
    def _generate_recommendations(
        self, 
        total_docs: int, 
        doc_types: Dict[str, int], 
        authority_dist: Dict[str, int],
        missing_fields: List[str]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Document type recommendations
        unknown_count = doc_types.get('unknown', 0)
        if unknown_count > total_docs * 0.2:
            recommendations.append(
                f"High number of unclassified documents ({unknown_count}). "
                "Improve document type classification rules."
            )
        
        # Authority distribution recommendations
        unknown_authority = authority_dist.get('unknown', 0)
        if unknown_authority > total_docs * 0.5:
            recommendations.append(
                f"Many documents have unknown authority ({unknown_authority}). "
                "Expand expert author database."
            )
        
        # Metadata completeness recommendations
        if missing_fields:
            recommendations.append(
                f"Improve metadata completeness. Fields often missing: {', '.join(missing_fields[:3])}"
            )
        
        # Scale recommendations
        if total_docs > 1000:
            recommendations.append(
                "Large collection detected. Consider implementing batch processing "
                "and performance optimizations."
            )
        
        # Document type balance recommendations
        academic_papers = doc_types.get('academic_paper', 0)
        if academic_papers > total_docs * 0.8:
            recommendations.append(
                "Collection heavily skewed toward academic papers. "
                "Consider adding more diverse document types (standards, expert blogs, audit tickets)."
            )
        
        return recommendations
    
    def _empty_analysis_result(self) -> ContentAnalysisResult:
        """Return empty analysis result."""
        return ContentAnalysisResult(
            total_documents=0,
            document_type_distribution={},
            authority_distribution={},
            common_terms=[],
            author_analysis={},
            missing_metadata_fields=[],
            recommendations=["No documents found for analysis"]
        )