"""
Authority mapping system for identifying and scoring author expertise in accessibility.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config.constants import EXPERT_AUTHORS, AuthorityLevel


@dataclass
class AuthorProfile:
    """Profile information for an author."""
    name: str
    authority_level: AuthorityLevel
    expertise_areas: List[str]
    affiliations: List[str]
    confidence: float


class AuthorityMapper:
    """
    Maps authors to authority levels and expertise areas for content weighting.
    """
    
    def __init__(self):
        self.expert_database = self._build_expert_database()
        self.affiliation_patterns = self._build_affiliation_patterns()
    
    def analyze_authors(self, authors_string: str) -> List[AuthorProfile]:
        """
        Analyze author string and return authority profiles.
        
        Args:
            authors_string: String containing author names and affiliations
            
        Returns:
            List of AuthorProfile objects
        """
        if not authors_string:
            return []
        
        # Parse individual authors
        parsed_authors = self._parse_authors(authors_string)
        
        # Analyze each author
        profiles = []
        for author_info in parsed_authors:
            profile = self._analyze_single_author(author_info)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    def get_document_authority_score(self, authors_string: str) -> Tuple[AuthorityLevel, float]:
        """
        Get overall authority score for a document based on its authors.
        
        Args:
            authors_string: String containing author names
            
        Returns:
            Tuple of (highest_authority_level, confidence_score)
        """
        profiles = self.analyze_authors(authors_string)
        
        if not profiles:
            return AuthorityLevel.UNKNOWN, 0.0
        
        # Find highest authority level
        highest_authority = max(profiles, key=lambda p: p.authority_level.value)
        
        # Calculate confidence based on known authors
        known_authors = [p for p in profiles if p.confidence > 0.7]
        confidence = min(len(known_authors) / max(len(profiles), 1), 1.0)
        
        return highest_authority.authority_level, confidence
    
    def _parse_authors(self, authors_string: str) -> List[Dict[str, str]]:
        """Parse author string into individual author information."""
        authors = []
        
        # Split by common delimiters
        author_parts = re.split(r'[,;]|\sand\s|\&', authors_string)
        
        for part in author_parts:
            part = part.strip()
            if not part:
                continue
            
            # Extract name and affiliation
            name, affiliation = self._extract_name_and_affiliation(part)
            if name:
                authors.append({
                    'name': name,
                    'affiliation': affiliation,
                    'raw': part
                })
        
        return authors
    
    def _extract_name_and_affiliation(self, author_part: str) -> Tuple[str, str]:
        """Extract name and affiliation from author string part."""
        # Common patterns for affiliations
        affiliation_patterns = [
            r'^(.+?)\s*\((.+?)\)$',  # Name (Affiliation)
            r'^(.+?)\s*,\s*(.+?)$',   # Name, Affiliation
            r'^(.+?)\s*-\s*(.+?)$',   # Name - Affiliation
        ]
        
        for pattern in affiliation_patterns:
            match = re.match(pattern, author_part.strip())
            if match:
                name = match.group(1).strip()
                affiliation = match.group(2).strip()
                return self._clean_name(name), affiliation
        
        # No affiliation found, treat as name only
        return self._clean_name(author_part.strip()), ""
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize author name."""
        # Remove titles and suffixes
        cleaned = re.sub(r'\b(Dr|Prof|Professor|Mr|Ms|Mrs)\.?\s*', '', name, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*(Jr|Sr|PhD|Ph\.D\.|MD|M\.D\.)\.?\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _analyze_single_author(self, author_info: Dict[str, str]) -> Optional[AuthorProfile]:
        """Analyze a single author for authority and expertise."""
        name = author_info['name']
        affiliation = author_info['affiliation']
        
        # Check against known experts (exact and fuzzy matching)
        expert_match = self._find_expert_match(name)
        if expert_match:
            expert_data = self.expert_database[expert_match]
            return AuthorProfile(
                name=name,
                authority_level=AuthorityLevel(expert_data['authority']),
                expertise_areas=expert_data['expertise'],
                affiliations=[affiliation] if affiliation else [],
                confidence=0.9
            )
        
        # Analyze affiliation for authority indicators
        authority_from_affiliation = self._analyze_affiliation(affiliation)
        
        # Determine authority level based on available information
        if authority_from_affiliation:
            return AuthorProfile(
                name=name,
                authority_level=authority_from_affiliation,
                expertise_areas=[],
                affiliations=[affiliation] if affiliation else [],
                confidence=0.5
            )
        
        # Default profile for unknown authors
        return AuthorProfile(
            name=name,
            authority_level=AuthorityLevel.UNKNOWN,
            expertise_areas=[],
            affiliations=[affiliation] if affiliation else [],
            confidence=0.1
        )
    
    def _find_expert_match(self, name: str) -> Optional[str]:
        """Find matching expert name with fuzzy matching."""
        name_lower = name.lower()
        
        # Exact match
        for expert_name in self.expert_database:
            if expert_name.lower() == name_lower:
                return expert_name
        
        # Fuzzy matching - check for partial matches
        for expert_name in self.expert_database:
            expert_lower = expert_name.lower()
            
            # Check if all parts of the input name appear in expert name
            name_parts = name_lower.split()
            expert_parts = expert_lower.split()
            
            # Match if most significant parts match (first name + last name)
            if len(name_parts) >= 2 and len(expert_parts) >= 2:
                if (name_parts[0] in expert_parts and name_parts[-1] in expert_parts) or \
                   (expert_parts[0] in name_parts and expert_parts[-1] in name_parts):
                    return expert_name
        
        return None
    
    def _analyze_affiliation(self, affiliation: str) -> Optional[AuthorityLevel]:
        """Analyze affiliation for authority indicators."""
        if not affiliation:
            return None
        
        affiliation_lower = affiliation.lower()
        
        # W3C and standards organizations
        if any(org in affiliation_lower for org in ['w3c', 'world wide web consortium', 'iso']):
            return AuthorityLevel.NORMATIVE
        
        # Major tech companies with accessibility teams
        tech_companies = ['google', 'microsoft', 'apple', 'mozilla', 'adobe', 'facebook', 'meta']
        if any(company in affiliation_lower for company in tech_companies):
            return AuthorityLevel.PROFESSIONAL
        
        # Academic institutions
        academic_indicators = ['university', 'college', 'institute', 'research']
        if any(indicator in affiliation_lower for indicator in academic_indicators):
            return AuthorityLevel.PEER_REVIEWED
        
        # Accessibility consulting companies
        consulting_indicators = ['accessibility', 'usability', 'inclusive', 'deque', 'tpg']
        if any(indicator in affiliation_lower for indicator in consulting_indicators):
            return AuthorityLevel.PROFESSIONAL
        
        return None
    
    def _build_expert_database(self) -> Dict[str, Dict]:
        """Build database of known experts from constants."""
        return {name: data for name, data in EXPERT_AUTHORS.items()}
    
    def _build_affiliation_patterns(self) -> Dict[str, AuthorityLevel]:
        """Build patterns for organization-based authority mapping."""
        return {
            'w3c': AuthorityLevel.NORMATIVE,
            'world wide web consortium': AuthorityLevel.NORMATIVE,
            'iso': AuthorityLevel.NORMATIVE,
            'deque': AuthorityLevel.PROFESSIONAL,
            'tpg': AuthorityLevel.PROFESSIONAL,
            'paciello group': AuthorityLevel.PROFESSIONAL,
            'university': AuthorityLevel.PEER_REVIEWED,
            'college': AuthorityLevel.PEER_REVIEWED,
            'institute': AuthorityLevel.PEER_REVIEWED
        }
    
    def add_expert(self, name: str, authority: int, expertise: List[str]) -> None:
        """Add a new expert to the database."""
        self.expert_database[name] = {
            'authority': authority,
            'expertise': expertise
        }
    
    def get_expertise_areas(self, authors_string: str) -> List[str]:
        """Get all expertise areas covered by the authors."""
        profiles = self.analyze_authors(authors_string)
        expertise_areas = []
        
        for profile in profiles:
            expertise_areas.extend(profile.expertise_areas)
        
        return list(set(expertise_areas))  # Remove duplicates