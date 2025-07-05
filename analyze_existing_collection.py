"""
Comprehensive analysis script for existing 500 document collection.
This script will examine the real collection to improve our classification,
authority mapping, and ontology systems.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.constants import EXPERT_AUTHORS, DocumentType, AuthorityLevel
from document_management.document_classifier import DocumentClassifier
from document_management.authority_mapper import AuthorityMapper
from ontology.ontology_manager import OntologyManager


@dataclass
class AuthorAnalysis:
    """Analysis results for an author."""
    name: str
    document_count: int
    is_known_expert: bool
    current_authority: AuthorityLevel
    potential_authority: AuthorityLevel
    expertise_indicators: List[str]
    affiliations: Set[str]
    sample_titles: List[str]
    research_priority: str  # "high", "medium", "low"


@dataclass
class SourceAnalysis:
    """Analysis of document sources/publications."""
    source_name: str
    document_count: int
    source_type: str  # "conference", "journal", "blog", "standards_org", "unknown"
    authority_level: str
    sample_titles: List[str]
    unique_authors: Set[str]


@dataclass
class CollectionAnalysis:
    """Complete analysis of the document collection."""
    total_documents: int
    classification_results: Dict[str, int]
    author_analysis: List[AuthorAnalysis]
    source_analysis: List[SourceAnalysis]
    terminology_gaps: List[str]
    ontology_improvements: List[str]
    expert_recommendations: List[str]
    blog_discoveries: List[str]


class ExistingCollectionAnalyzer:
    """Analyzes existing document collection for improvements."""
    
    def __init__(self, metadata_file_path: str):
        self.metadata_file_path = metadata_file_path
        self.classifier = DocumentClassifier()
        self.authority_mapper = AuthorityMapper()
        self.ontology = OntologyManager()
        
        # Load existing metadata
        self.metadata = self._load_metadata()
        
    def analyze_complete_collection(self) -> CollectionAnalysis:
        """Perform comprehensive analysis of the collection."""
        print(f"Analyzing collection of {len(self.metadata)} documents...")
        
        # Document classification analysis
        classification_results = self._analyze_document_classification()
        
        # Author analysis
        author_analysis = self._analyze_authors()
        
        # Source analysis  
        source_analysis = self._analyze_sources()
        
        # Terminology and ontology gaps
        terminology_gaps = self._find_terminology_gaps()
        ontology_improvements = self._suggest_ontology_improvements()
        
        # Expert and blog recommendations
        expert_recommendations = self._recommend_new_experts(author_analysis)
        blog_discoveries = self._discover_authoritative_blogs()
        
        return CollectionAnalysis(
            total_documents=len(self.metadata),
            classification_results=classification_results,
            author_analysis=author_analysis,
            source_analysis=source_analysis,
            terminology_gaps=terminology_gaps,
            ontology_improvements=ontology_improvements,
            expert_recommendations=expert_recommendations,
            blog_discoveries=blog_discoveries
        )
    
    def generate_detailed_report(self, analysis: CollectionAnalysis) -> str:
        """Generate a detailed analysis report."""
        report = []
        report.append("# Existing Collection Analysis Report")
        report.append("=" * 50)
        report.append(f"\n**Total Documents**: {analysis.total_documents}")
        
        # Document Classification Results
        report.append("\n## Document Classification Analysis")
        report.append("-" * 40)
        for doc_type, count in analysis.classification_results.items():
            percentage = (count / analysis.total_documents) * 100
            report.append(f"- **{doc_type}**: {count} documents ({percentage:.1f}%)")
        
        # Top Authors Analysis
        report.append("\n## Author Analysis")
        report.append("-" * 40)
        
        # High priority authors to research
        high_priority_authors = [a for a in analysis.author_analysis if a.research_priority == "high"]
        if high_priority_authors:
            report.append("\n### 🔍 HIGH PRIORITY: Authors to Research")
            for author in high_priority_authors[:10]:
                report.append(f"**{author.name}** ({author.document_count} docs)")
                report.append(f"  - Current authority: {author.current_authority.value}")
                report.append(f"  - Potential authority: {author.potential_authority.value}")
                report.append(f"  - Expertise indicators: {', '.join(author.expertise_indicators[:3])}")
                report.append(f"  - Sample title: {author.sample_titles[0] if author.sample_titles else 'N/A'}")
                report.append("")
        
        # Known experts in collection
        known_experts = [a for a in analysis.author_analysis if a.is_known_expert]
        if known_experts:
            report.append(f"\n### ✅ Known Experts Found ({len(known_experts)})")
            for expert in known_experts:
                report.append(f"- **{expert.name}**: {expert.document_count} documents")
        
        # Source Analysis
        report.append("\n## Source Analysis")
        report.append("-" * 40)
        top_sources = sorted(analysis.source_analysis, key=lambda x: x.document_count, reverse=True)
        
        for source in top_sources[:15]:
            report.append(f"**{source.source_name}** ({source.document_count} docs)")
            report.append(f"  - Type: {source.source_type}")
            report.append(f"  - Authority: {source.authority_level}")
            report.append(f"  - Authors: {len(source.unique_authors)} unique")
            report.append("")
        
        # Blog Discoveries
        if analysis.blog_discoveries:
            report.append("\n## 📝 Authoritative Blogs Discovered")
            report.append("-" * 40)
            for blog in analysis.blog_discoveries:
                report.append(f"- {blog}")
        
        # Expert Recommendations
        if analysis.expert_recommendations:
            report.append("\n## 👥 New Expert Recommendations")
            report.append("-" * 40)
            for recommendation in analysis.expert_recommendations:
                report.append(f"- {recommendation}")
        
        # Ontology Improvements
        if analysis.ontology_improvements:
            report.append("\n## 🧠 Ontology Enhancement Suggestions")
            report.append("-" * 40)
            for improvement in analysis.ontology_improvements:
                report.append(f"- {improvement}")
        
        # Terminology Gaps
        if analysis.terminology_gaps:
            report.append("\n## 📚 Terminology Gaps Found")
            report.append("-" * 40)
            for gap in analysis.terminology_gaps[:10]:
                report.append(f"- {gap}")
        
        return "\n".join(report)
    
    def save_author_research_file(self, analysis: CollectionAnalysis) -> str:
        """Save detailed author information for manual research."""
        research_file = "author_research_needed.json"
        
        research_data = {
            "high_priority_authors": [],
            "medium_priority_authors": [],
            "potential_experts": []
        }
        
        for author in analysis.author_analysis:
            author_data = {
                "name": author.name,
                "document_count": author.document_count,
                "sample_titles": author.sample_titles,
                "affiliations": list(author.affiliations),
                "expertise_indicators": author.expertise_indicators,
                "current_authority": author.current_authority.value,
                "potential_authority": author.potential_authority.value,
                "research_notes": ""
            }
            
            if author.research_priority == "high":
                research_data["high_priority_authors"].append(author_data)
            elif author.research_priority == "medium":
                research_data["medium_priority_authors"].append(author_data)
            
            if author.document_count > 3 and not author.is_known_expert:
                research_data["potential_experts"].append(author_data)
        
        with open(research_file, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        return research_file
    
    def _load_metadata(self) -> Dict:
        """Load metadata from file."""
        try:
            with open(self.metadata_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Metadata file not found: {self.metadata_file_path}")
            return {}
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}
    
    def _analyze_document_classification(self) -> Dict[str, int]:
        """Analyze how documents would be classified."""
        classification_counts = defaultdict(int)
        
        print("Classifying documents...")
        for i, (doc_path, doc_info) in enumerate(self.metadata.items()):
            if i % 50 == 0:
                print(f"  Processed {i}/{len(self.metadata)} documents")
            
            # Simulate classification (without full content)
            title = doc_info.get('title', '')
            authors = doc_info.get('authors', '')
            acm_ref = doc_info.get('acm_reference', '')
            
            # Simple classification based on available metadata
            if any(keyword in acm_ref.lower() for keyword in ['w3c', 'wcag', 'recommendation', 'standard']):
                doc_type = 'standards_document'
            elif any(expert in authors for expert in EXPERT_AUTHORS.keys()):
                doc_type = 'expert_blog'
            elif any(keyword in acm_ref.lower() for keyword in ['acm', 'proceedings', 'conference', 'doi']):
                doc_type = 'academic_paper'
            elif 'blog' in acm_ref.lower() or any(keyword in title.lower() for keyword in ['tips', 'guide', 'how to']):
                doc_type = 'expert_blog'
            else:
                doc_type = 'unknown'
            
            classification_counts[doc_type] += 1
        
        return dict(classification_counts)
    
    def _analyze_authors(self) -> List[AuthorAnalysis]:
        """Analyze all authors in the collection."""
        author_stats = defaultdict(lambda: {
            'count': 0, 
            'titles': [], 
            'affiliations': set(), 
            'acm_refs': []
        })
        
        # Collect author statistics
        for doc_info in self.metadata.values():
            authors_str = doc_info.get('authors', '')
            title = doc_info.get('title', '')
            acm_ref = doc_info.get('acm_reference', '')
            
            if authors_str:
                # Parse authors (simple splitting)
                authors = re.split(r'[,;&]|\sand\s', authors_str)
                for author in authors:
                    author = author.strip()
                    if author:
                        author_stats[author]['count'] += 1
                        author_stats[author]['titles'].append(title)
                        author_stats[author]['acm_refs'].append(acm_ref)
                        
                        # Extract potential affiliations
                        if '(' in author:
                            affiliation = re.search(r'\(([^)]+)\)', author)
                            if affiliation:
                                author_stats[author]['affiliations'].add(affiliation.group(1))
        
        # Analyze each author
        author_analyses = []
        for author_name, stats in author_stats.items():
            if stats['count'] < 2:  # Skip authors with only 1 document
                continue
            
            analysis = self._analyze_single_author(author_name, stats)
            author_analyses.append(analysis)
        
        # Sort by priority and document count
        author_analyses.sort(key=lambda x: (x.research_priority == "high", x.document_count), reverse=True)
        return author_analyses
    
    def _analyze_single_author(self, author_name: str, stats: Dict) -> AuthorAnalysis:
        """Analyze a single author."""
        cleaned_name = re.sub(r'\s*\([^)]*\)', '', author_name).strip()
        
        # Check if known expert
        is_known = cleaned_name in EXPERT_AUTHORS
        current_authority = AuthorityLevel.EXPERT_INTERPRETIVE if is_known else AuthorityLevel.UNKNOWN
        
        # Analyze expertise indicators
        expertise_indicators = []
        all_text = ' '.join(stats['titles'] + stats['acm_refs']).lower()
        
        if 'wcag' in all_text:
            expertise_indicators.append('WCAG')
        if any(term in all_text for term in ['aria', 'screen reader', 'accessibility']):
            expertise_indicators.append('Accessibility')
        if any(term in all_text for term in ['usability', 'user experience', 'ux']):
            expertise_indicators.append('UX/Usability')
        if any(term in all_text for term in ['testing', 'evaluation', 'audit']):
            expertise_indicators.append('Testing')
        if any(term in all_text for term in ['standards', 'guidelines', 'compliance']):
            expertise_indicators.append('Standards')
        
        # Determine potential authority
        potential_authority = AuthorityLevel.UNKNOWN
        if stats['count'] >= 5:
            if any(term in all_text for term in ['w3c', 'wcag', 'standard']):
                potential_authority = AuthorityLevel.NORMATIVE
            elif len(expertise_indicators) >= 3:
                potential_authority = AuthorityLevel.EXPERT_INTERPRETIVE
            elif any(affil for affil in stats['affiliations'] if 'university' in affil.lower()):
                potential_authority = AuthorityLevel.PEER_REVIEWED
            else:
                potential_authority = AuthorityLevel.PROFESSIONAL
        elif stats['count'] >= 3:
            potential_authority = AuthorityLevel.PROFESSIONAL
        
        # Determine research priority
        research_priority = "low"
        if not is_known and stats['count'] >= 5:
            research_priority = "high"
        elif not is_known and stats['count'] >= 3:
            research_priority = "medium"
        
        return AuthorAnalysis(
            name=cleaned_name,
            document_count=stats['count'],
            is_known_expert=is_known,
            current_authority=current_authority,
            potential_authority=potential_authority,
            expertise_indicators=expertise_indicators,
            affiliations=stats['affiliations'],
            sample_titles=stats['titles'][:3],
            research_priority=research_priority
        )
    
    def _analyze_sources(self) -> List[SourceAnalysis]:
        """Analyze document sources and publications."""
        source_stats = defaultdict(lambda: {
            'count': 0,
            'titles': [],
            'authors': set(),
            'type': 'unknown',
            'authority': 'unknown'
        })
        
        for doc_info in self.metadata.values():
            acm_ref = doc_info.get('acm_reference', '')
            title = doc_info.get('title', '')
            authors = doc_info.get('authors', '')
            
            if acm_ref:
                # Extract source name
                source_name = self._extract_source_name(acm_ref)
                if source_name:
                    source_stats[source_name]['count'] += 1
                    source_stats[source_name]['titles'].append(title)
                    source_stats[source_name]['authors'].add(authors)
                    
                    # Classify source type
                    source_type, authority = self._classify_source(acm_ref)
                    source_stats[source_name]['type'] = source_type
                    source_stats[source_name]['authority'] = authority
        
        # Convert to SourceAnalysis objects
        source_analyses = []
        for source_name, stats in source_stats.items():
            if stats['count'] >= 2:  # Only include sources with multiple documents
                analysis = SourceAnalysis(
                    source_name=source_name,
                    document_count=stats['count'],
                    source_type=stats['type'],
                    authority_level=stats['authority'],
                    sample_titles=stats['titles'][:3],
                    unique_authors=stats['authors']
                )
                source_analyses.append(analysis)
        
        return sorted(source_analyses, key=lambda x: x.document_count, reverse=True)
    
    def _extract_source_name(self, acm_ref: str) -> Optional[str]:
        """Extract source/publication name from ACM reference."""
        # Common patterns for extracting publication names
        patterns = [
            r'In\s+(.+?)\s+\(',  # "In CONFERENCE_NAME ("
            r'\.(.+?)\s+\d{4}',  # ".JOURNAL_NAME 2023"
            r'Proceedings of (.+?)[\.\,]',  # "Proceedings of CONFERENCE"
            r'(\w+\.?(?:\s+\w+)*)\s+(?:Conference|Symposium|Workshop)',  # Conference names
            r'Journal of (.+?)[\.\,]',  # Journal names
            r'ACM (.+?)[\.\,]',  # ACM publications
        ]
        
        for pattern in patterns:
            match = re.search(pattern, acm_ref, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, try to extract first significant part
        parts = acm_ref.split('.')
        if len(parts) > 1:
            return parts[0].strip()
        
        return None
    
    def _classify_source(self, acm_ref: str) -> Tuple[str, str]:
        """Classify source type and authority level."""
        acm_ref_lower = acm_ref.lower()
        
        # Standards organizations
        if any(org in acm_ref_lower for org in ['w3c', 'iso', 'ieee standards']):
            return 'standards_org', 'normative'
        
        # Academic conferences/journals
        if any(term in acm_ref_lower for term in ['proceedings', 'conference', 'symposium', 'journal', 'acm']):
            return 'conference', 'peer_reviewed'
        
        # Blogs and websites
        if any(term in acm_ref_lower for term in ['blog', 'medium', 'dev.to', 'smashing magazine']):
            return 'blog', 'professional'
        
        return 'unknown', 'unknown'
    
    def _find_terminology_gaps(self) -> List[str]:
        """Find accessibility terms not covered in our ontology."""
        # Extract all terms from titles and references
        all_text = []
        for doc_info in self.metadata.values():
            title = doc_info.get('title', '')
            acm_ref = doc_info.get('acm_reference', '')
            all_text.append(f"{title} {acm_ref}")
        
        combined_text = ' '.join(all_text).lower()
        
        # Extract accessibility-related terms
        accessibility_terms = set()
        
        # Use regex to find potential accessibility terms
        patterns = [
            r'\b\w*accessibility\w*\b',
            r'\b\w*wcag\w*\b', 
            r'\b\w*aria\w*\b',
            r'\b\w*screen.?reader\w*\b',
            r'\b\w*keyboard\w*\b',
            r'\b\w*focus\w*\b',
            r'\b\w*contrast\w*\b',
            r'\b\w*usability\w*\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, combined_text)
            accessibility_terms.update(matches)
        
        # Check which terms are not in our ontology
        ontology_terms = set()
        for concept_data in self.ontology.concept_index.values():
            ontology_terms.add(concept_data.get('label', '').lower())
            ontology_terms.update([s.lower() for s in concept_data.get('synonyms', [])])
            ontology_terms.update([s.lower() for s in concept_data.get('related_terms', [])])
        
        gaps = [term for term in accessibility_terms if term not in ontology_terms and len(term) > 3]
        return sorted(set(gaps))[:20]  # Return top 20 gaps
    
    def _suggest_ontology_improvements(self) -> List[str]:
        """Suggest improvements to the ontology."""
        suggestions = []
        
        # Analyze common term combinations
        term_frequency = Counter()
        for doc_info in self.metadata.values():
            title = doc_info.get('title', '').lower()
            words = re.findall(r'\b\w{4,}\b', title)
            term_frequency.update(words)
        
        # Suggest new concepts based on frequent terms
        accessibility_keywords = ['accessibility', 'wcag', 'aria', 'screen', 'keyboard', 'usability']
        for term, count in term_frequency.most_common(50):
            if count > 10 and any(keyword in term for keyword in accessibility_keywords):
                suggestions.append(f"Consider adding '{term}' concept (appears {count} times)")
        
        return suggestions[:10]
    
    def _recommend_new_experts(self, author_analysis: List[AuthorAnalysis]) -> List[str]:
        """Recommend new experts to add to the database."""
        recommendations = []
        
        high_priority = [a for a in author_analysis if a.research_priority == "high"]
        for author in high_priority[:10]:
            rec = f"Research {author.name} ({author.document_count} docs) - expertise in {', '.join(author.expertise_indicators[:2])}"
            recommendations.append(rec)
        
        return recommendations
    
    def _discover_authoritative_blogs(self) -> List[str]:
        """Discover authoritative accessibility blogs."""
        blog_indicators = []
        
        for doc_info in self.metadata.values():
            acm_ref = doc_info.get('acm_reference', '')
            if any(term in acm_ref.lower() for term in ['blog', 'medium', 'dev.to', 'smashing']):
                # Extract potential blog names
                if 'blog' in acm_ref.lower():
                    blog_indicators.append(acm_ref)
        
        return list(set(blog_indicators))[:10]


def main():
    """Run collection analysis."""
    print("🔍 EXISTING COLLECTION ANALYSIS")
    print("=" * 50)
    
    # Path to your existing metadata file
    metadata_path = "/home/bob/Documents/acm4-rag/ollama-fundamentals/chroma_db/documents_metadata.json"
    
    if not Path(metadata_path).exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        print("Please update the path to your actual metadata file.")
        return
    
    analyzer = ExistingCollectionAnalyzer(metadata_path)
    analysis = analyzer.analyze_complete_collection()
    
    # Generate detailed report
    report = analyzer.generate_detailed_report(analysis)
    
    # Save report
    with open("COLLECTION_ANALYSIS_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save author research file
    research_file = analyzer.save_author_research_file(analysis)
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Detailed report saved: COLLECTION_ANALYSIS_REPORT.md")
    print(f"👥 Author research data saved: {research_file}")
    print(f"\n📊 Quick Summary:")
    print(f"   - Total documents: {analysis.total_documents}")
    print(f"   - High priority authors to research: {len([a for a in analysis.author_analysis if a.research_priority == 'high'])}")
    print(f"   - Potential new experts: {len([a for a in analysis.author_analysis if a.document_count > 3 and not a.is_known_expert])}")
    print(f"   - Blog sources discovered: {len(analysis.blog_discoveries)}")


if __name__ == "__main__":
    main()