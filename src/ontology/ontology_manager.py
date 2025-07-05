"""
Ontology manager for loading, querying, and expanding accessibility concepts.
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from config.constants import ACCESSIBILITY_DOMAINS, TECHNOLOGY_DOMAINS


@dataclass
class ConceptExpansion:
    """Result of concept expansion."""
    original_term: str
    synonyms: List[str]
    related_terms: List[str]
    subconcepts: List[str]
    parent_concepts: List[str]
    expansion_weight: float


class OntologyManager:
    """
    Manages accessibility ontology for query expansion and concept relationships.
    """
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize ontology manager.
        
        Args:
            ontology_path: Path to ontology files directory
        """
        if ontology_path is None:
            # Default to schemas directory relative to this file
            ontology_path = Path(__file__).parent / "schemas"
        
        self.ontology_path = Path(ontology_path)
        self.ontology_data = {}
        self.concept_index = {}
        self.term_to_concept = {}
        
        self._load_ontologies()
        self._build_indexes()
    
    def expand_query_terms(self, query: str, max_expansions: int = 10) -> List[str]:
        """
        Expand query terms using ontology relationships.
        
        Args:
            query: Original query string
            max_expansions: Maximum number of expansion terms to return
            
        Returns:
            List of expanded terms
        """
        query_lower = query.lower()
        expanded_terms = set()
        
        # Find concepts mentioned in the query
        mentioned_concepts = self._find_mentioned_concepts(query_lower)
        
        for concept in mentioned_concepts:
            expansion = self._expand_concept(concept)
            if expansion:
                # Add synonyms (highest weight)
                expanded_terms.update(expansion.synonyms[:3])
                
                # Add related terms (medium weight)
                expanded_terms.update(expansion.related_terms[:3])
                
                # Add subconcepts (lower weight)
                expanded_terms.update(expansion.subconcepts[:2])
        
        # Remove original query terms to avoid duplication
        query_words = set(query_lower.split())
        expanded_terms = expanded_terms - query_words
        
        # Convert to list and limit
        return list(expanded_terms)[:max_expansions]
    
    def get_concept_relationships(self, concept_id: str) -> Dict[str, List[str]]:
        """
        Get all relationships for a concept.
        
        Args:
            concept_id: ID of the concept
            
        Returns:
            Dictionary with relationship types and related concepts
        """
        if concept_id not in self.concept_index:
            return {}
        
        concept_data = self.concept_index[concept_id]
        relationships = {
            'synonyms': concept_data.get('synonyms', []),
            'related_terms': concept_data.get('related_terms', []),
            'subconcepts': concept_data.get('subconcepts', []),
            'parent': [concept_data.get('parent')] if concept_data.get('parent') else [],
            'technologies': concept_data.get('technologies', []),
            'standards': concept_data.get('standards', []),
            'wcag_criteria': concept_data.get('wcag_criteria', [])
        }
        
        # Remove empty lists
        return {k: v for k, v in relationships.items() if v and v != [None]}
    
    def find_related_concepts(self, term: str, relationship_types: List[str] = None) -> List[str]:
        """
        Find concepts related to a term.
        
        Args:
            term: Search term
            relationship_types: Types of relationships to include
            
        Returns:
            List of related concept IDs
        """
        if relationship_types is None:
            relationship_types = ['synonyms', 'related_terms', 'subconcepts']
        
        term_lower = term.lower()
        related_concepts = set()
        
        # Find direct concept match
        concept_id = self.term_to_concept.get(term_lower)
        if concept_id:
            relationships = self.get_concept_relationships(concept_id)
            for rel_type in relationship_types:
                if rel_type in relationships:
                    related_concepts.update(relationships[rel_type])
        
        # Find concepts that mention this term
        for concept_id, concept_data in self.concept_index.items():
            for rel_type in relationship_types:
                if rel_type in concept_data:
                    if term_lower in [item.lower() for item in concept_data[rel_type]]:
                        related_concepts.add(concept_id)
        
        return list(related_concepts)
    
    def get_domain_terms(self, domain: str) -> List[str]:
        """
        Get all terms related to a specific domain.
        
        Args:
            domain: Domain name (e.g., 'visual', 'motor', 'html', 'aria')
            
        Returns:
            List of terms in the domain
        """
        # Check built-in domains first
        if domain in ACCESSIBILITY_DOMAINS:
            return ACCESSIBILITY_DOMAINS[domain]
        elif domain in TECHNOLOGY_DOMAINS:
            return TECHNOLOGY_DOMAINS[domain]
        
        # Check ontology concepts
        domain_terms = []
        for concept_id, concept_data in self.concept_index.items():
            if concept_data.get('parent') == domain or concept_id == domain:
                domain_terms.append(concept_data.get('label', concept_id))
                domain_terms.extend(concept_data.get('synonyms', []))
                domain_terms.extend(concept_data.get('subconcepts', []))
        
        return list(set(domain_terms))
    
    def classify_query_domain(self, query: str) -> List[Tuple[str, float]]:
        """
        Classify query into accessibility domains.
        
        Args:
            query: Query string
            
        Returns:
            List of (domain, confidence) tuples
        """
        query_lower = query.lower()
        domain_scores = {}
        
        # Check accessibility domains
        for domain, terms in ACCESSIBILITY_DOMAINS.items():
            score = sum(1 for term in terms if term in query_lower)
            if score > 0:
                domain_scores[domain] = score / len(terms)
        
        # Check technology domains
        for domain, terms in TECHNOLOGY_DOMAINS.items():
            score = sum(1 for term in terms if term in query_lower)
            if score > 0:
                domain_scores[f"tech_{domain}"] = score / len(terms)
        
        # Sort by score
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_domains
    
    def _load_ontologies(self) -> None:
        """Load all ontology files from the schemas directory."""
        if not self.ontology_path.exists():
            print(f"Warning: Ontology path {self.ontology_path} does not exist")
            return
        
        for ontology_file in self.ontology_path.glob("*.json"):
            try:
                with open(ontology_file, 'r', encoding='utf-8') as f:
                    ontology_data = json.load(f)
                    self.ontology_data[ontology_file.stem] = ontology_data
                    print(f"Loaded ontology: {ontology_file.stem}")
            except Exception as e:
                print(f"Error loading ontology {ontology_file}: {e}")
    
    def _build_indexes(self) -> None:
        """Build search indexes from loaded ontologies."""
        for ontology_name, ontology_data in self.ontology_data.items():
            # Index concepts
            if 'concepts' in ontology_data:
                for concept_id, concept_info in ontology_data['concepts'].items():
                    self.concept_index[concept_id] = concept_info
                    
                    # Index terms to concepts
                    self.term_to_concept[concept_id.lower()] = concept_id
                    self.term_to_concept[concept_info.get('label', '').lower()] = concept_id
                    
                    # Index synonyms
                    for synonym in concept_info.get('synonyms', []):
                        self.term_to_concept[synonym.lower()] = concept_id
            
            # Index technologies
            if 'technologies' in ontology_data:
                for tech_id, tech_info in ontology_data['technologies'].items():
                    self.concept_index[tech_id] = tech_info
                    self.term_to_concept[tech_id.lower()] = tech_id
                    self.term_to_concept[tech_info.get('label', '').lower()] = tech_id
                    
                    # Index examples/instances
                    for example in tech_info.get('examples', []):
                        self.term_to_concept[example.lower()] = tech_id
    
    def _find_mentioned_concepts(self, query: str) -> List[str]:
        """Find concepts mentioned in the query."""
        mentioned = []
        
        # Direct term matches
        for term, concept_id in self.term_to_concept.items():
            if term in query:
                mentioned.append(concept_id)
        
        # Fuzzy matches for multi-word terms
        query_words = query.split()
        for term, concept_id in self.term_to_concept.items():
            term_words = term.split()
            if len(term_words) > 1:
                # Check if all words of the term appear in the query
                if all(word in query_words for word in term_words):
                    mentioned.append(concept_id)
        
        return list(set(mentioned))
    
    def _expand_concept(self, concept_id: str) -> Optional[ConceptExpansion]:
        """Expand a single concept."""
        if concept_id not in self.concept_index:
            return None
        
        concept_data = self.concept_index[concept_id]
        
        return ConceptExpansion(
            original_term=concept_data.get('label', concept_id),
            synonyms=concept_data.get('synonyms', []),
            related_terms=concept_data.get('related_terms', []),
            subconcepts=concept_data.get('subconcepts', []),
            parent_concepts=[concept_data.get('parent')] if concept_data.get('parent') else [],
            expansion_weight=1.0
        )
    
    def get_ontology_stats(self) -> Dict[str, int]:
        """Get statistics about loaded ontologies."""
        stats = {
            'total_ontologies': len(self.ontology_data),
            'total_concepts': len(self.concept_index),
            'total_term_mappings': len(self.term_to_concept)
        }
        
        # Count by type
        concept_types = {}
        for concept_data in self.concept_index.values():
            concept_type = concept_data.get('type', 'concept')
            concept_types[concept_type] = concept_types.get(concept_type, 0) + 1
        
        stats.update(concept_types)
        return stats
    
    def validate_ontology_consistency(self) -> List[str]:
        """Validate ontology for consistency issues."""
        issues = []
        
        # Check for broken parent relationships
        for concept_id, concept_data in self.concept_index.items():
            parent = concept_data.get('parent')
            if parent and parent not in self.concept_index:
                issues.append(f"Concept {concept_id} references unknown parent: {parent}")
            
            # Check subconcepts
            for subconcept in concept_data.get('subconcepts', []):
                if subconcept not in self.concept_index:
                    issues.append(f"Concept {concept_id} references unknown subconcept: {subconcept}")
        
        return issues