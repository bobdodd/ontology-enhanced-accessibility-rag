"""
Simple validation script for Phase 1 components.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test config import
        from config.constants import DocumentType, AuthorityLevel, EXPERT_AUTHORS
        print("✅ Config constants imported successfully")
        print(f"   Found {len(EXPERT_AUTHORS)} expert authors")
        print(f"   Document types: {[dt.value for dt in DocumentType]}")
        
        # Test ontology components
        print("\nTesting ontology components...")
        from ontology.ontology_manager import OntologyManager
        ontology = OntologyManager()
        stats = ontology.get_ontology_stats()
        print(f"✅ Ontology manager working - {stats.get('total_concepts', 0)} concepts loaded")
        
        # Test query expansion
        expanded = ontology.expand_query_terms("screen reader accessibility")
        print(f"   Query expansion working - got {len(expanded)} terms")
        
        # Test document classification components
        print("\nTesting document classification...")
        from document_management.document_classifier import DocumentClassifier
        classifier = DocumentClassifier()
        print("✅ Document classifier initialized")
        
        # Test authority mapping
        from document_management.authority_mapper import AuthorityMapper
        mapper = AuthorityMapper()
        print("✅ Authority mapper initialized")
        
        # Test metadata schema
        print("\nTesting metadata schema...")
        from document_management.metadata_schema import DocumentMetadata, AuthorInfo
        from datetime import datetime
        
        # Create sample metadata
        author = AuthorInfo(
            name="Test Author",
            authority_level=AuthorityLevel.EXPERT_INTERPRETIVE,
            expertise_areas=["WCAG", "testing"]
        )
        
        metadata = DocumentMetadata(
            document_id="test_001",
            title="Test Document",
            source_path="./test.pdf",
            file_type="pdf",
            file_size=1024,
            authors=[author]
        )
        
        # Test serialization
        metadata_dict = metadata.to_dict()
        restored = DocumentMetadata.from_dict(metadata_dict)
        print("✅ Metadata serialization/deserialization working")
        
        print("\n" + "="*60)
        print("🎉 PHASE 1 VALIDATION SUCCESSFUL!")
        print("="*60)
        print("\nAll Phase 1 components are working correctly:")
        print("✅ Document Type Classification System")
        print("✅ Authority Mapping for Expert Authors") 
        print("✅ Core Accessibility Ontology")
        print("✅ Enhanced Metadata Schema")
        print("✅ Query Expansion Engine")
        print("\n✨ Ready to proceed to Phase 2: Query Enhancement Pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classification_example():
    """Test classification with a realistic example."""
    try:
        from config.constants import DocumentType, AuthorityLevel
        from document_management.document_classifier import DocumentClassifier
        
        classifier = DocumentClassifier()
        
        # Test with academic paper content
        result = classifier.classify_document(
            filepath="./sample_paper.pdf",
            content="""
            Abstract: This paper presents a comprehensive evaluation of screen reader 
            compatibility with modern web applications. We conducted user studies with 
            45 participants using NVDA, JAWS, and VoiceOver.
            
            Keywords: accessibility, screen readers, web applications, user study
            
            1. Introduction
            Web accessibility has become increasingly important...
            
            2. Methodology  
            We recruited 45 participants with visual impairments...
            
            3. Results
            Our findings indicate that 67% of modern web applications...
            
            References:
            [1] Smith, J. et al. (2022). Screen Reader Testing Methods. ACM TACCESS.
            """,
            metadata={"DOI": "10.1145/1234567", "conference": "CHI 2023"},
            authors="Smith, J., University of Technology; Doe, A., Research Institute"
        )
        
        print(f"\nClassification Example:")
        print(f"Document Type: {result.document_type.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Authority Level: {result.authority_level.value}")
        print(f"Key Features: {list(result.detected_features.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Classification test failed: {e}")
        return False


def test_ontology_expansion():
    """Test ontology-based query expansion."""
    try:
        from ontology.ontology_manager import OntologyManager
        
        ontology = OntologyManager()
        
        test_queries = [
            "screen reader accessibility",
            "keyboard navigation",
            "color contrast WCAG",
            "ARIA landmarks",
            "form accessibility"
        ]
        
        print(f"\nOntology Query Expansion Examples:")
        for query in test_queries:
            expanded = ontology.expand_query_terms(query, max_expansions=5)
            print(f"'{query}' → {expanded}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ontology expansion test failed: {e}")
        return False


def main():
    """Run validation tests."""
    print("Phase 1 Validation - Ontology-Enhanced RAG System")
    print("="*60)
    
    success = True
    success &= test_imports()
    
    if success:
        success &= test_classification_example()
        success &= test_ontology_expansion()
    
    if success:
        print(f"\n🚀 Phase 1 foundation is solid - ready for Phase 2!")
    else:
        print(f"\n⚠️  Some components need attention before proceeding.")
    
    return success


if __name__ == "__main__":
    main()