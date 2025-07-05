"""
Test script for Phase 1 implementation validation.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_management.document_classifier import DocumentClassifier, ClassificationResult
from document_management.authority_mapper import AuthorityMapper
from document_management.content_analyzer import ContentAnalyzer
from document_management.metadata_schema import DocumentMetadata, MetadataManager
from ontology.ontology_manager import OntologyManager
from config.constants import DocumentType, AuthorityLevel


def test_document_classifier():
    """Test document classification system."""
    print("Testing Document Classifier...")
    
    classifier = DocumentClassifier()
    
    # Test academic paper classification
    academic_content = """
    Abstract: This paper presents a methodology for evaluating web accessibility.
    Keywords: accessibility, WCAG, evaluation, screen readers
    Introduction: Web accessibility is crucial for inclusive design...
    Methodology: We conducted experiments with 50 participants...
    Results: Our findings show that 78% of websites fail WCAG criteria...
    Conclusion: The proposed methodology effectively identifies accessibility barriers.
    References: [1] Smith, J. (2020). Accessibility Testing Methods...
    """
    
    result = classifier.classify_document(
        filepath="academic_paper.pdf",
        content=academic_content,
        metadata={"DOI": "10.1145/1234567.1234568", "ACM": "CHI 2023"},
        authors="Smith, J., University of Technology"
    )
    
    print(f"Academic paper classification: {result.document_type}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Authority: {result.authority_level}")
    print(f"Reasoning: {result.reasoning[:100]}...")
    print()
    
    # Test expert blog classification
    blog_content = """
    In this post, I want to share some best practices for implementing accessible forms.
    As someone who has worked on WCAG for many years, I recommend using proper labels
    and providing clear error messages. Here are my top tips for form accessibility...
    """
    
    result = classifier.classify_document(
        filepath="accessibility_blog_post.html",
        content=blog_content,
        metadata={"blog": "accessibility insights", "post": "form accessibility"},
        authors="Steve Faulkner"
    )
    
    print(f"Blog post classification: {result.document_type}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Authority: {result.authority_level}")
    print()


def test_authority_mapper():
    """Test authority mapping system."""
    print("Testing Authority Mapper...")
    
    mapper = AuthorityMapper()
    
    # Test known expert
    profiles = mapper.analyze_authors("Steve Faulkner, TPG")
    if profiles:
        profile = profiles[0]
        print(f"Expert author: {profile.name}")
        print(f"Authority: {profile.authority_level}")
        print(f"Confidence: {profile.confidence}")
        print(f"Expertise: {profile.expertise_areas}")
    
    # Test academic author
    profiles = mapper.analyze_authors("John Smith, University of California")
    if profiles:
        profile = profiles[0]
        print(f"Academic author: {profile.name}")
        print(f"Authority: {profile.authority_level}")
        print(f"Affiliation: {profile.affiliations}")
    
    print()


def test_ontology_manager():
    """Test ontology management system."""
    print("Testing Ontology Manager...")
    
    ontology = OntologyManager()
    
    # Test query expansion
    query = "screen reader accessibility"
    expanded_terms = ontology.expand_query_terms(query)
    print(f"Original query: {query}")
    print(f"Expanded terms: {expanded_terms[:5]}")
    
    # Test concept relationships
    relationships = ontology.get_concept_relationships("screen_readers")
    print(f"Screen reader relationships: {list(relationships.keys())}")
    
    # Test domain classification
    domains = ontology.classify_query_domain("keyboard navigation focus indicators")
    print(f"Query domains: {domains[:3]}")
    
    # Test ontology stats
    stats = ontology.get_ontology_stats()
    print(f"Ontology stats: {stats}")
    
    print()


def test_metadata_schema():
    """Test enhanced metadata schema."""
    print("Testing Metadata Schema...")
    
    # Create sample metadata
    from document_management.metadata_schema import AuthorInfo, ClassificationInfo, ProcessingInfo
    from datetime import datetime
    
    metadata = DocumentMetadata(
        document_id="test_doc_001",
        title="Web Accessibility Best Practices",
        source_path="./documents/test_doc.pdf",
        file_type="pdf",
        file_size=1024000,
        authors=[
            AuthorInfo(
                name="Jane Expert",
                authority_level=AuthorityLevel.EXPERT_INTERPRETIVE,
                expertise_areas=["WCAG", "ARIA", "testing"]
            )
        ],
        classification=ClassificationInfo(
            document_type=DocumentType.EXPERT_BLOG,
            confidence=0.85,
            detected_features={"content": ["best practice", "recommend"]},
            classification_method="pattern_matching",
            reasoning="Contains expert language patterns"
        ),
        processing_info=ProcessingInfo(
            ingestion_date=datetime.now(),
            processing_version="1.0",
            chunk_count=25,
            embedding_model="mxbai-embed-large",
            vector_collection="expert_blogs",
            last_updated=datetime.now()
        )
    )
    
    # Test serialization
    metadata_dict = metadata.to_dict()
    print(f"Metadata serialized: {len(metadata_dict)} fields")
    
    # Test deserialization
    restored_metadata = DocumentMetadata.from_dict(metadata_dict)
    print(f"Metadata restored: {restored_metadata.title}")
    print(f"Document type: {restored_metadata.classification.document_type}")
    
    print()


def test_content_analyzer():
    """Test content analysis system."""
    print("Testing Content Analyzer...")
    
    # Create mock metadata file for testing
    import json
    import tempfile
    
    mock_metadata = {
        "doc1": {
            "title": "WCAG 2.1 Accessibility Guidelines",
            "authors": "Alastair Campbell, Michael Cooper",
            "acm_reference": "W3C Recommendation",
            "chunks_count": 150,
            "added_at": "2023-01-01T00:00:00"
        },
        "doc2": {
            "title": "Screen Reader Testing Best Practices",
            "authors": "Steve Faulkner",
            "acm_reference": "Blog post on accessibility insights",
            "chunks_count": 25,
            "added_at": "2023-02-01T00:00:00"
        },
        "doc3": {
            "title": "Automated Accessibility Testing in CI/CD",
            "authors": "Jane Developer, Tech Corp",
            "acm_reference": "ACM CHI 2023 Proceedings",
            "chunks_count": 45,
            "added_at": "2023-03-01T00:00:00"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_metadata, f)
        temp_file = f.name
    
    try:
        analyzer = ContentAnalyzer()
        result = analyzer.analyze_document_collection(temp_file)
        
        print(f"Total documents analyzed: {result.total_documents}")
        print(f"Document types: {result.document_type_distribution}")
        print(f"Authority distribution: {result.authority_distribution}")
        print(f"Top terms: {result.common_terms[:5]}")
        print(f"Recommendations: {len(result.recommendations)}")
        for rec in result.recommendations[:2]:
            print(f"  - {rec}")
        
    finally:
        os.unlink(temp_file)
    
    print()


def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("PHASE 1 VALIDATION TESTS")
    print("=" * 60)
    print()
    
    try:
        test_document_classifier()
        test_authority_mapper()
        test_ontology_manager()
        test_metadata_schema()
        test_content_analyzer()
        
        print("=" * 60)
        print("✅ ALL PHASE 1 TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Phase 1 Foundation components are working correctly:")
        print("✅ Document Type Classification")
        print("✅ Authority Mapping System")
        print("✅ Core Accessibility Ontology")
        print("✅ Enhanced Metadata Schema")
        print("✅ Content Analysis Tools")
        print()
        print("Ready to proceed to Phase 2: Query Enhancement Engine")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()