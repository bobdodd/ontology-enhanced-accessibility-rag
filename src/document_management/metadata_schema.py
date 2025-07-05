"""
Enhanced metadata schema for document management with ontology-enhanced features.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from config.constants import DocumentType, AuthorityLevel


@dataclass
class AuthorInfo:
    """Information about a document author."""
    name: str
    authority_level: AuthorityLevel
    expertise_areas: List[str]
    affiliation: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class ClassificationInfo:
    """Document classification information."""
    document_type: DocumentType
    confidence: float
    detected_features: Dict[str, List[str]]
    classification_method: str
    reasoning: str


@dataclass
class OntologyMapping:
    """Ontology concept mappings for the document."""
    mentioned_concepts: List[str]
    primary_domains: List[str]
    technology_stack: List[str]
    accessibility_focus: List[str]
    standards_referenced: List[str]


@dataclass
class ProcessingInfo:
    """Information about document processing."""
    ingestion_date: datetime
    processing_version: str
    chunk_count: int
    embedding_model: str
    vector_collection: str
    last_updated: datetime


@dataclass
class QualityMetrics:
    """Quality metrics for the document."""
    completeness_score: float  # 0-1, based on filled metadata fields
    authority_confidence: float  # 0-1, confidence in authority assessment
    classification_confidence: float  # 0-1, confidence in document type
    ontology_coverage: float  # 0-1, how well document maps to ontology


@dataclass
class DocumentMetadata:
    """Complete metadata schema for documents."""
    # Basic document information
    document_id: str
    title: str
    source_path: str
    file_type: str
    file_size: int
    
    # Content information
    authors: List[AuthorInfo]
    publication_date: Optional[datetime] = None
    acm_reference: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = None
    
    # Classification and authority
    classification: ClassificationInfo = None
    overall_authority: AuthorityLevel = AuthorityLevel.UNKNOWN
    
    # Ontology mappings
    ontology_mapping: OntologyMapping = None
    
    # Processing information
    processing_info: ProcessingInfo = None
    
    # Quality metrics
    quality_metrics: QualityMetrics = None
    
    # Legacy compatibility
    chunks_count: int = 0  # For backward compatibility
    added_at: str = ""  # For backward compatibility
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        def convert_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, Enum):
                return value.value
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in asdict(value).items()}
            else:
                return value
        
        return {k: convert_value(v) for k, v in asdict(self).items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """Create from dictionary (for JSON deserialization)."""
        # Handle datetime fields
        if 'publication_date' in data and data['publication_date']:
            data['publication_date'] = datetime.fromisoformat(data['publication_date'])
        
        # Handle processing info
        if 'processing_info' in data and data['processing_info']:
            processing_data = data['processing_info']
            if 'ingestion_date' in processing_data:
                processing_data['ingestion_date'] = datetime.fromisoformat(processing_data['ingestion_date'])
            if 'last_updated' in processing_data:
                processing_data['last_updated'] = datetime.fromisoformat(processing_data['last_updated'])
            data['processing_info'] = ProcessingInfo(**processing_data)
        
        # Handle classification
        if 'classification' in data and data['classification']:
            classification_data = data['classification']
            classification_data['document_type'] = DocumentType(classification_data['document_type'])
            data['classification'] = ClassificationInfo(**classification_data)
        
        # Handle authority level
        if 'overall_authority' in data:
            data['overall_authority'] = AuthorityLevel(data['overall_authority'])
        
        # Handle authors
        if 'authors' in data and data['authors']:
            authors = []
            for author_data in data['authors']:
                author_data['authority_level'] = AuthorityLevel(author_data['authority_level'])
                authors.append(AuthorInfo(**author_data))
            data['authors'] = authors
        
        # Handle ontology mapping
        if 'ontology_mapping' in data and data['ontology_mapping']:
            data['ontology_mapping'] = OntologyMapping(**data['ontology_mapping'])
        
        # Handle quality metrics
        if 'quality_metrics' in data and data['quality_metrics']:
            data['quality_metrics'] = QualityMetrics(**data['quality_metrics'])
        
        return cls(**data)
    
    @classmethod
    def from_legacy_metadata(cls, legacy_data: Dict[str, Any], document_id: str, source_path: str) -> 'DocumentMetadata':
        """Create from legacy metadata format."""
        # Extract basic information
        title = legacy_data.get('title', '')
        authors_str = legacy_data.get('authors', '')
        acm_reference = legacy_data.get('acm_reference', '')
        chunks_count = legacy_data.get('chunks_count', 0)
        added_at = legacy_data.get('added_at', '')
        
        # Parse authors (simple parsing for now)
        authors = []
        if authors_str:
            for author_name in authors_str.split(','):
                authors.append(AuthorInfo(
                    name=author_name.strip(),
                    authority_level=AuthorityLevel.UNKNOWN,
                    expertise_areas=[]
                ))
        
        # Set processing info
        processing_info = ProcessingInfo(
            ingestion_date=datetime.fromisoformat(added_at) if added_at else datetime.now(),
            processing_version="legacy",
            chunk_count=chunks_count,
            embedding_model="unknown",
            vector_collection="legacy",
            last_updated=datetime.now()
        )
        
        return cls(
            document_id=document_id,
            title=title,
            source_path=source_path,
            file_type="pdf",  # Assume PDF for legacy
            file_size=0,  # Unknown for legacy
            authors=authors,
            acm_reference=acm_reference,
            processing_info=processing_info,
            chunks_count=chunks_count,
            added_at=added_at
        )


class MetadataManager:
    """Manages document metadata with enhanced schema."""
    
    def __init__(self, metadata_file_path: str):
        self.metadata_file_path = metadata_file_path
        self._metadata_cache = {}
    
    def load_metadata(self) -> Dict[str, DocumentMetadata]:
        """Load all metadata from file."""
        try:
            import json
            with open(self.metadata_file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            metadata = {}
            for doc_id, doc_data in raw_data.items():
                if self._is_legacy_format(doc_data):
                    metadata[doc_id] = DocumentMetadata.from_legacy_metadata(
                        doc_data, doc_id, doc_id
                    )
                else:
                    metadata[doc_id] = DocumentMetadata.from_dict(doc_data)
            
            self._metadata_cache = metadata
            return metadata
            
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}
    
    def save_metadata(self, metadata: Dict[str, DocumentMetadata]) -> bool:
        """Save metadata to file."""
        try:
            import json
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.metadata_file_path), exist_ok=True)
            
            # Convert to dictionary format
            raw_data = {}
            for doc_id, doc_metadata in metadata.items():
                raw_data[doc_id] = doc_metadata.to_dict()
            
            # Write to file
            with open(self.metadata_file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
            
            self._metadata_cache = metadata
            return True
            
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def add_document(self, metadata: DocumentMetadata) -> bool:
        """Add or update document metadata."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        self._metadata_cache[metadata.document_id] = metadata
        return self.save_metadata(self._metadata_cache)
    
    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a specific document."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        return self._metadata_cache.get(document_id)
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields of document metadata."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        if document_id not in self._metadata_cache:
            return False
        
        doc_metadata = self._metadata_cache[document_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(doc_metadata, field):
                setattr(doc_metadata, field, value)
        
        # Update last_updated timestamp
        if doc_metadata.processing_info:
            doc_metadata.processing_info.last_updated = datetime.now()
        
        return self.save_metadata(self._metadata_cache)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document metadata."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        if document_id in self._metadata_cache:
            del self._metadata_cache[document_id]
            return self.save_metadata(self._metadata_cache)
        
        return False
    
    def search_documents(self, **criteria) -> List[DocumentMetadata]:
        """Search documents by criteria."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        results = []
        for doc_metadata in self._metadata_cache.values():
            if self._matches_criteria(doc_metadata, criteria):
                results.append(doc_metadata)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self._metadata_cache:
            self._metadata_cache = self.load_metadata()
        
        stats = {
            'total_documents': len(self._metadata_cache),
            'document_types': {},
            'authority_levels': {},
            'file_types': {},
            'total_chunks': 0
        }
        
        for doc_metadata in self._metadata_cache.values():
            # Document types
            if doc_metadata.classification:
                doc_type = doc_metadata.classification.document_type.value
                stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
            
            # Authority levels
            authority = doc_metadata.overall_authority.value
            stats['authority_levels'][authority] = stats['authority_levels'].get(authority, 0) + 1
            
            # File types
            file_type = doc_metadata.file_type
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
            
            # Total chunks
            if doc_metadata.processing_info:
                stats['total_chunks'] += doc_metadata.processing_info.chunk_count
        
        return stats
    
    def _is_legacy_format(self, doc_data: Dict[str, Any]) -> bool:
        """Check if metadata is in legacy format."""
        legacy_fields = {'title', 'authors', 'acm_reference', 'chunks_count', 'added_at'}
        enhanced_fields = {'document_id', 'classification', 'ontology_mapping', 'processing_info'}
        
        has_legacy = any(field in doc_data for field in legacy_fields)
        has_enhanced = any(field in doc_data for field in enhanced_fields)
        
        return has_legacy and not has_enhanced
    
    def _matches_criteria(self, doc_metadata: DocumentMetadata, criteria: Dict[str, Any]) -> bool:
        """Check if document matches search criteria."""
        for field, value in criteria.items():
            if field == 'document_type':
                if not doc_metadata.classification or doc_metadata.classification.document_type != value:
                    return False
            elif field == 'authority_level':
                if doc_metadata.overall_authority != value:
                    return False
            elif field == 'author':
                if not any(value.lower() in author.name.lower() for author in doc_metadata.authors):
                    return False
            elif field == 'title':
                if value.lower() not in doc_metadata.title.lower():
                    return False
            # Add more criteria as needed
        
        return True