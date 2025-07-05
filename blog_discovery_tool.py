"""
Tool for discovering and cataloguing authoritative accessibility blogs and sources.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from urllib.parse import urlparse

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.constants import EXPERT_AUTHORS


@dataclass
class BlogSource:
    """Information about a blog source."""
    name: str
    url: Optional[str]
    document_count: int
    authors: Set[str]
    authority_indicators: List[str]
    content_focus: List[str]
    recommended_authority: str  # "high", "medium", "low"
    sample_titles: List[str]
    notes: str = ""


class BlogDiscoveryTool:
    """Tool for discovering authoritative accessibility blogs."""
    
    def __init__(self, metadata_file_path: str):
        self.metadata_file_path = metadata_file_path
        self.metadata = self._load_metadata()
        
        # Known authoritative blog domains/sources
        self.known_authoritative_sources = {
            "webaim.org": {"name": "WebAIM", "authority": "high"},
            "a11yproject.com": {"name": "The A11Y Project", "authority": "high"},
            "deque.com": {"name": "Deque Blog", "authority": "high"},
            "paciellogroup.com": {"name": "TPG Blog", "authority": "high"},
            "tpg": {"name": "The Paciello Group", "authority": "high"},
            "smashingmagazine.com": {"name": "Smashing Magazine", "authority": "medium"},
            "css-tricks.com": {"name": "CSS-Tricks", "authority": "medium"},
            "medium.com": {"name": "Medium", "authority": "variable"},
            "dev.to": {"name": "DEV Community", "authority": "variable"},
            "inclusive-components.design": {"name": "Inclusive Components", "authority": "high"},
            "adrianroselli.com": {"name": "Adrian Roselli", "authority": "high"},
            "stevefaulkner.github.io": {"name": "Steve Faulkner", "authority": "high"},
            "scottohara.me": {"name": "Scott O'Hara", "authority": "high"},
            "heydonworks.com": {"name": "Heydon Pickering", "authority": "high"},
        }
        
        self.accessibility_indicators = [
            "accessibility", "a11y", "wcag", "aria", "screen reader",
            "inclusive design", "universal design", "assistive technology",
            "keyboard navigation", "color contrast", "focus management"
        ]
    
    def discover_blog_sources(self) -> List[BlogSource]:
        """Discover blog sources from the collection."""
        print("Discovering blog sources...")
        
        blog_sources = defaultdict(lambda: {
            'count': 0,
            'authors': set(),
            'titles': [],
            'urls': set(),
            'authority_indicators': [],
            'content_focus': []
        })
        
        # Analyze each document for blog indicators
        for doc_info in self.metadata.values():
            acm_ref = doc_info.get('acm_reference', '')
            title = doc_info.get('title', '')
            authors = doc_info.get('authors', '')
            
            # Check if this looks like a blog post
            if self._is_blog_content(acm_ref, title):
                source_name = self._extract_blog_source(acm_ref)
                if source_name:
                    blog_sources[source_name]['count'] += 1
                    blog_sources[source_name]['authors'].add(authors)
                    blog_sources[source_name]['titles'].append(title)
                    
                    # Extract URL if present
                    url = self._extract_url(acm_ref)
                    if url:
                        blog_sources[source_name]['urls'].add(url)
                    
                    # Analyze authority indicators
                    authority_indicators = self._analyze_authority_indicators(authors, acm_ref, title)
                    blog_sources[source_name]['authority_indicators'].extend(authority_indicators)
                    
                    # Analyze content focus
                    content_focus = self._analyze_content_focus(title, acm_ref)
                    blog_sources[source_name]['content_focus'].extend(content_focus)
        
        # Convert to BlogSource objects
        discovered_sources = []
        for source_name, data in blog_sources.items():
            if data['count'] >= 2:  # Only include sources with multiple posts
                source = BlogSource(
                    name=source_name,
                    url=next(iter(data['urls'])) if data['urls'] else None,
                    document_count=data['count'],
                    authors=data['authors'],
                    authority_indicators=list(set(data['authority_indicators'])),
                    content_focus=list(set(data['content_focus'])),
                    recommended_authority=self._determine_authority_level(source_name, data),
                    sample_titles=data['titles'][:3]
                )
                discovered_sources.append(source)
        
        return sorted(discovered_sources, key=lambda x: x.document_count, reverse=True)
    
    def generate_blog_catalog(self, blog_sources: List[BlogSource]) -> Dict:
        """Generate a catalog of authoritative accessibility blogs."""
        catalog = {
            "high_authority_blogs": [],
            "medium_authority_blogs": [],
            "emerging_sources": [],
            "expert_personal_blogs": [],
            "research_needed": []
        }
        
        for source in blog_sources:
            source_data = asdict(source)
            
            if source.recommended_authority == "high":
                catalog["high_authority_blogs"].append(source_data)
            elif source.recommended_authority == "medium":
                catalog["medium_authority_blogs"].append(source_data)
            elif any(expert in str(source.authors) for expert in EXPERT_AUTHORS.keys()):
                catalog["expert_personal_blogs"].append(source_data)
            elif source.document_count >= 5:
                catalog["research_needed"].append(source_data)
            else:
                catalog["emerging_sources"].append(source_data)
        
        return catalog
    
    def generate_blog_report(self, catalog: Dict) -> str:
        """Generate a human-readable blog discovery report."""
        report = []
        report.append("# Accessibility Blog Discovery Report")
        report.append("=" * 50)
        
        # High authority blogs
        high_auth = catalog.get("high_authority_blogs", [])
        if high_auth:
            report.append(f"\n## 🌟 HIGH AUTHORITY BLOGS ({len(high_auth)})")
            report.append("-" * 40)
            for blog in high_auth:
                report.append(f"\n### {blog['name']}")
                report.append(f"**Documents**: {blog['document_count']}")
                if blog['url']:
                    report.append(f"**URL**: {blog['url']}")
                report.append(f"**Authority Indicators**: {', '.join(blog['authority_indicators'][:3])}")
                report.append(f"**Content Focus**: {', '.join(blog['content_focus'][:3])}")
                report.append(f"**Sample Title**: {blog['sample_titles'][0] if blog['sample_titles'] else 'N/A'}")
        
        # Medium authority blogs
        medium_auth = catalog.get("medium_authority_blogs", [])
        if medium_auth:
            report.append(f"\n## 📝 MEDIUM AUTHORITY BLOGS ({len(medium_auth)})")
            report.append("-" * 40)
            for blog in medium_auth:
                report.append(f"- **{blog['name']}** ({blog['document_count']} docs)")
                if blog['url']:
                    report.append(f"  URL: {blog['url']}")
        
        # Expert personal blogs
        expert_blogs = catalog.get("expert_personal_blogs", [])
        if expert_blogs:
            report.append(f"\n## 👤 EXPERT PERSONAL BLOGS ({len(expert_blogs)})")
            report.append("-" * 40)
            for blog in expert_blogs:
                report.append(f"- **{blog['name']}** ({blog['document_count']} docs)")
                if blog['url']:
                    report.append(f"  URL: {blog['url']}")
        
        # Sources needing research
        research_needed = catalog.get("research_needed", [])
        if research_needed:
            report.append(f"\n## 🔍 SOURCES REQUIRING RESEARCH ({len(research_needed)})")
            report.append("-" * 40)
            for blog in research_needed:
                report.append(f"\n### {blog['name']} - NEEDS INVESTIGATION")
                report.append(f"**Documents**: {blog['document_count']}")
                if blog['url']:
                    report.append(f"**URL**: {blog['url']}")
                report.append(f"**Authors**: {len(blog['authors'])} unique")
                report.append(f"**Research Priority**: High (multiple documents)")
        
        # Recommendations
        report.append(f"\n## 📋 RECOMMENDATIONS")
        report.append("-" * 40)
        
        total_high = len(high_auth)
        total_research = len(research_needed)
        
        report.append(f"1. **Monitor {total_high} high-authority blogs** for new accessibility content")
        report.append(f"2. **Research {total_research} unknown sources** to determine their authority")
        report.append(f"3. **Consider reaching out** to expert bloggers for collaboration")
        report.append(f"4. **Prioritize content** from high-authority sources in retrieval")
        
        return "\n".join(report)
    
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
    
    def _is_blog_content(self, acm_ref: str, title: str) -> bool:
        """Determine if content appears to be from a blog."""
        blog_indicators = [
            'blog', 'medium.com', 'dev.to', 'smashingmagazine.com',
            'css-tricks.com', 'a11yproject.com', 'webaim.org/blog',
            'deque.com/blog', 'adrianroselli.com', 'scottohara.me'
        ]
        
        combined_text = f"{acm_ref} {title}".lower()
        return any(indicator in combined_text for indicator in blog_indicators)
    
    def _extract_blog_source(self, acm_ref: str) -> Optional[str]:
        """Extract blog source name from ACM reference."""
        # Try to extract from URL first
        url_match = re.search(r'https?://([^/\s]+)', acm_ref)
        if url_match:
            domain = url_match.group(1)
            # Clean up domain
            domain = re.sub(r'^www\.', '', domain)
            return domain
        
        # Try to extract from common blog patterns
        blog_patterns = [
            r'(\w+\.com)\s+blog',
            r'blog\.(\w+\.com)',
            r'(\w+)\s+blog',
            r'medium\.com/@(\w+)',
            r'dev\.to/(\w+)',
        ]
        
        for pattern in blog_patterns:
            match = re.search(pattern, acm_ref, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: use first significant word
        words = acm_ref.split()
        for word in words:
            if len(word) > 3 and word.lower() not in ['http', 'https', 'www']:
                return word
        
        return None
    
    def _extract_url(self, acm_ref: str) -> Optional[str]:
        """Extract URL from ACM reference."""
        url_match = re.search(r'https?://[^\s]+', acm_ref)
        return url_match.group(0) if url_match else None
    
    def _analyze_authority_indicators(self, authors: str, acm_ref: str, title: str) -> List[str]:
        """Analyze authority indicators for a blog source."""
        indicators = []
        
        # Check for known experts
        for expert in EXPERT_AUTHORS.keys():
            if expert.lower() in authors.lower():
                indicators.append(f"Known expert: {expert}")
        
        # Check for accessibility organization affiliation
        org_indicators = ['webaim', 'deque', 'tpg', 'paciello', 'w3c']
        for org in org_indicators:
            if org in acm_ref.lower():
                indicators.append(f"Organization: {org}")
        
        # Check for accessibility focus
        combined_text = f"{authors} {acm_ref} {title}".lower()
        if any(term in combined_text for term in self.accessibility_indicators):
            indicators.append("Accessibility focused")
        
        return indicators
    
    def _analyze_content_focus(self, title: str, acm_ref: str) -> List[str]:
        """Analyze the content focus areas."""
        focus_areas = []
        combined_text = f"{title} {acm_ref}".lower()
        
        focus_mapping = {
            "WCAG": ["wcag", "guidelines", "standards"],
            "ARIA": ["aria", "roles", "properties"],
            "Testing": ["testing", "audit", "evaluation"],
            "Screen Readers": ["screen reader", "nvda", "jaws", "voiceover"],
            "Keyboard Navigation": ["keyboard", "navigation", "focus"],
            "Color/Contrast": ["color", "contrast", "vision"],
            "Forms": ["form", "input", "label"],
            "JavaScript": ["javascript", "js", "dynamic", "spa"],
            "Design": ["design", "ux", "ui", "inclusive"]
        }
        
        for focus, keywords in focus_mapping.items():
            if any(keyword in combined_text for keyword in keywords):
                focus_areas.append(focus)
        
        return focus_areas
    
    def _determine_authority_level(self, source_name: str, data: Dict) -> str:
        """Determine authority level for a blog source."""
        # Check against known authoritative sources
        for domain, info in self.known_authoritative_sources.items():
            if domain in source_name.lower():
                return info["authority"]
        
        # Check for expert authors
        for authors in data['authors']:
            if any(expert.lower() in authors.lower() for expert in EXPERT_AUTHORS.keys()):
                return "high"
        
        # Check for authority indicators
        authority_indicators = data.get('authority_indicators', [])
        if len(authority_indicators) >= 2:
            return "medium"
        elif len(authority_indicators) >= 1:
            return "low"
        
        # Default based on document count
        if data['count'] >= 10:
            return "medium"
        elif data['count'] >= 5:
            return "low"
        
        return "emerging"


def main():
    """Run blog discovery tool."""
    print("📝 ACCESSIBILITY BLOG DISCOVERY TOOL")
    print("=" * 50)
    
    # Path to your existing metadata file
    metadata_path = "/home/bob/Documents/acm4-rag/ollama-fundamentals/chroma_db/documents_metadata.json"
    
    if not Path(metadata_path).exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        print("Please update the path to your actual metadata file.")
        return
    
    # Run blog discovery
    discovery_tool = BlogDiscoveryTool(metadata_path)
    blog_sources = discovery_tool.discover_blog_sources()
    
    print(f"Found {len(blog_sources)} blog sources")
    
    # Generate catalog
    catalog = discovery_tool.generate_blog_catalog(blog_sources)
    
    # Save catalog
    with open("accessibility_blog_catalog.json", 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False, default=list)
    
    # Generate report
    report = discovery_tool.generate_blog_report(catalog)
    with open("BLOG_DISCOVERY_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Blog discovery complete!")
    print(f"📄 Report saved: BLOG_DISCOVERY_REPORT.md")
    print(f"📋 Catalog saved: accessibility_blog_catalog.json")
    
    # Summary
    high_auth = len(catalog.get("high_authority_blogs", []))
    research_needed = len(catalog.get("research_needed", []))
    expert_blogs = len(catalog.get("expert_personal_blogs", []))
    
    print(f"\n📊 Discovery Summary:")
    print(f"   - High authority blogs: {high_auth}")
    print(f"   - Expert personal blogs: {expert_blogs}")
    print(f"   - Sources needing research: {research_needed}")


if __name__ == "__main__":
    main()