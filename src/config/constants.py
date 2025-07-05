"""
Application constants and configuration values.
"""

from enum import Enum
from typing import Dict, List

# Document Types
class DocumentType(Enum):
    ACADEMIC_PAPER = "academic_paper"
    STANDARDS_DOCUMENT = "standards_document"
    EXPERT_BLOG = "expert_blog"
    AUDIT_TICKET = "audit_ticket"
    TESTING_TRANSCRIPT = "testing_transcript"
    NEWSLETTER = "newsletter"
    JOURNAL_ARTICLE = "journal_article"
    UNKNOWN = "unknown"

# Authority Levels (1-5 scale)
class AuthorityLevel(Enum):
    NORMATIVE = 5  # WCAG standards, official specifications
    EXPERT_INTERPRETIVE = 4  # WCAG authors' blogs, expert guidance
    PEER_REVIEWED = 3  # Academic papers, research
    PROFESSIONAL = 2  # Industry best practices, audit findings
    COMMUNITY = 1  # General community content
    UNKNOWN = 0  # Unclassified content

# Query Intent Types
class QueryIntent(Enum):
    RESEARCH = "research"  # "What does research show..."
    STANDARDS = "standards"  # "According to WCAG..."
    IMPLEMENTATION = "implementation"  # "How do I implement..."
    TESTING = "testing"  # "How to test..."
    NEWS_UPDATES = "news_updates"  # "What's the latest..."
    TROUBLESHOOTING = "troubleshooting"  # "Why is X not working..."

# Accessibility Domains
ACCESSIBILITY_DOMAINS = {
    "visual": [
        "blindness", "low_vision", "color_blindness", "photosensitivity",
        "screen_reader", "magnification", "high_contrast"
    ],
    "motor": [
        "limited_fine_motor", "tremor", "paralysis", "switch_navigation",
        "keyboard_only", "voice_control", "eye_tracking"
    ],
    "cognitive": [
        "dyslexia", "adhd", "memory_issues", "processing_disorders",
        "autism", "learning_disabilities", "cognitive_load"
    ],
    "auditory": [
        "deafness", "hard_of_hearing", "auditory_processing",
        "captions", "transcripts", "sign_language"
    ]
}

# Technology Domains
TECHNOLOGY_DOMAINS = {
    "html": [
        "semantic_elements", "forms", "tables", "images", "landmarks",
        "headings", "lists", "links", "buttons"
    ],
    "aria": [
        "roles", "properties", "states", "live_regions", "labels",
        "descriptions", "controls", "expanded", "hidden"
    ],
    "css": [
        "focus_indicators", "responsive_design", "animations", "transforms",
        "visibility", "color_contrast", "typography", "layout"
    ],
    "javascript": [
        "dynamic_content", "spa_navigation", "event_handling", "ajax",
        "progressive_enhancement", "frameworks", "libraries"
    ]
}

# Standards Hierarchy
STANDARDS_HIERARCHY = {
    "wcag": {
        "2.1": ["A", "AA", "AAA"],
        "2.2": ["A", "AA", "AAA"]
    },
    "section_508": ["compliance"],
    "en_301_549": ["compliance"],
    "ada": ["compliance"]
}

# Known Expert Authors (WCAG contributors and accessibility leaders)
EXPERT_AUTHORS = {
    # WCAG Working Group chairs and editors
    "Alastair Campbell": {"authority": 5, "expertise": ["wcag", "usability", "cognitive"]},
    "Michael Cooper": {"authority": 5, "expertise": ["wcag", "aria", "standards"]},
    "Andrew Kirkpatrick": {"authority": 5, "expertise": ["wcag", "policy", "testing"]},
    "Joshue O Connor": {"authority": 5, "expertise": ["wcag", "html", "advocacy"]},
    
    # Prominent accessibility experts
    "Steve Faulkner": {"authority": 4, "expertise": ["html", "aria", "testing"]},
    "Léonie Watson": {"authority": 4, "expertise": ["screen_readers", "html", "aria"]},
    "Scott O'Hara": {"authority": 4, "expertise": ["aria", "forms", "navigation"]},
    "Adrian Roselli": {"authority": 4, "expertise": ["forms", "tables", "testing"]},
    "Heydon Pickering": {"authority": 4, "expertise": ["design_systems", "inclusive_design"]},
    "Eric Eggert": {"authority": 4, "expertise": ["wcag", "tutorials", "education"]},
    "Laura Kalbag": {"authority": 4, "expertise": ["design", "privacy", "ethics"]},
    "Derek Featherstone": {"authority": 4, "expertise": ["testing", "training", "consulting"]},
    "Karl Groves": {"authority": 4, "expertise": ["automation", "testing", "business"]},
    "Marcy Sutton": {"authority": 4, "expertise": ["javascript", "react", "testing"]},
    
    # Academic researchers
    "Clayton Lewis": {"authority": 3, "expertise": ["research", "cognitive", "design"]},
    "Gregg Vanderheiden": {"authority": 3, "expertise": ["research", "standards", "technology"]},
    "Jeffrey Bigham": {"authority": 3, "expertise": ["research", "ai", "crowdsourcing"]},
}

# File type patterns for document classification
DOCUMENT_TYPE_PATTERNS = {
    DocumentType.ACADEMIC_PAPER: {
        "filename_patterns": [r"\.pdf$"],
        "metadata_patterns": ["DOI:", "Abstract:", "Keywords:", "ACM", "IEEE"],
        "content_patterns": ["methodology", "experiment", "results", "conclusion", "references"]
    },
    DocumentType.STANDARDS_DOCUMENT: {
        "filename_patterns": [r"wcag", r"section.?508", r"en.?301.?549"],
        "metadata_patterns": ["W3C", "ISO", "standard", "specification"],
        "content_patterns": ["MUST", "SHALL", "conformance", "success criteria"]
    },
    DocumentType.EXPERT_BLOG: {
        "filename_patterns": [r"blog", r"article"],
        "metadata_patterns": ["blog", "post", "article"],
        "content_patterns": ["In this post", "I recommend", "best practice", "tip"]
    }
}

# Chunk processing constants
CHUNK_SIZE = 850
CHUNK_OVERLAP = 300
MAX_CHUNKS_PER_DOCUMENT = 1000

# Vector database constants
EMBEDDING_MODEL = "mxbai-embed-large:v1"
LLM_MODEL = "llama3.1:8b"
VECTOR_STORE_NAME = "accessibility-rag"
COLLECTION_NAMES = {
    DocumentType.ACADEMIC_PAPER: "academic_papers",
    DocumentType.STANDARDS_DOCUMENT: "standards",
    DocumentType.EXPERT_BLOG: "expert_blogs",
    DocumentType.AUDIT_TICKET: "audit_tickets",
    DocumentType.TESTING_TRANSCRIPT: "testing_transcripts",
    DocumentType.NEWSLETTER: "newsletters",
    DocumentType.JOURNAL_ARTICLE: "journal_articles"
}