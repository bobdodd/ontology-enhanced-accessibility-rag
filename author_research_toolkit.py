"""
Author research toolkit for investigating unknown accessibility experts.
This tool helps research potential expert authors found in the collection.
"""

import sys
import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import quote

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.constants import EXPERT_AUTHORS, AuthorityLevel


@dataclass
class AuthorResearchProfile:
    """Research profile for an author."""
    name: str
    document_count: int
    sample_titles: List[str]
    potential_affiliations: Set[str]
    expertise_areas: List[str]
    
    # Research findings
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    personal_website: Optional[str] = None
    current_affiliation: Optional[str] = None
    w3c_involvement: bool = False
    accessibility_credentials: List[str] = None
    recommended_authority: AuthorityLevel = AuthorityLevel.UNKNOWN
    research_notes: str = ""
    research_status: str = "pending"  # "pending", "completed", "skip"


class AuthorResearcher:
    """Tools for researching potential accessibility experts."""
    
    def __init__(self):
        self.accessibility_organizations = {
            "W3C": ["w3.org", "w3c"],
            "WebAIM": ["webaim.org"],
            "Deque": ["deque.com"],
            "TPG": ["paciellogroup.com", "tpg"],
            "Level Access": ["levelaccess.com"],
            "UsableNet": ["usablenet.com"],
            "IAAP": ["accessibilityassociation.org"]
        }
        
        self.accessibility_keywords = [
            "accessibility", "WCAG", "ARIA", "screen reader", "inclusive design",
            "universal design", "digital accessibility", "web accessibility",
            "a11y", "Section 508", "ADA compliance", "assistive technology"
        ]
    
    def research_author_batch(self, author_research_file: str) -> Dict:
        """Process a batch of authors for research."""
        try:
            with open(author_research_file, 'r', encoding='utf-8') as f:
                research_data = json.load(f)
        except FileNotFoundError:
            print(f"Research file not found: {author_research_file}")
            return {}
        
        # Process high priority authors first
        print("Researching high priority authors...")
        for author_data in research_data.get("high_priority_authors", []):
            profile = self._create_research_profile(author_data)
            enhanced_profile = self._research_single_author(profile)
            author_data.update(asdict(enhanced_profile))
        
        # Save updated research data
        output_file = "author_research_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        return research_data
    
    def generate_research_report(self, research_results: Dict) -> str:
        """Generate a research report for manual review."""
        report = []
        report.append("# Author Research Report")
        report.append("=" * 50)
        
        # High priority findings
        high_priority = research_results.get("high_priority_authors", [])
        if high_priority:
            report.append("\n## 🔍 HIGH PRIORITY RESEARCH RESULTS")
            report.append("-" * 40)
            
            for author in high_priority:
                profile = AuthorResearchProfile(**author)
                report.append(f"\n### {profile.name}")
                report.append(f"**Documents**: {profile.document_count}")
                report.append(f"**Sample Work**: {profile.sample_titles[0] if profile.sample_titles else 'N/A'}")
                
                if profile.current_affiliation:
                    report.append(f"**Current Role**: {profile.current_affiliation}")
                
                if profile.w3c_involvement:
                    report.append("**W3C Involvement**: ✅ Yes")
                
                if profile.accessibility_credentials:
                    report.append(f"**Credentials**: {', '.join(profile.accessibility_credentials)}")
                
                report.append(f"**Recommended Authority**: {profile.recommended_authority.value}")
                
                if profile.research_notes:
                    report.append(f"**Research Notes**: {profile.research_notes}")
                
                # Links for manual verification
                links = []
                if profile.linkedin_url:
                    links.append(f"[LinkedIn]({profile.linkedin_url})")
                if profile.twitter_url:
                    links.append(f"[Twitter]({profile.twitter_url})")
                if profile.personal_website:
                    links.append(f"[Website]({profile.personal_website})")
                
                if links:
                    report.append(f"**Links**: {' | '.join(links)}")
                
                report.append("")
        
        # Summary and recommendations
        report.append("\n## 📋 SUMMARY & RECOMMENDATIONS")
        report.append("-" * 40)
        
        # Count recommendations by authority level
        authority_counts = {}
        for author in high_priority:
            auth_level = AuthorityLevel(author.get("recommended_authority", 0))
            authority_counts[auth_level] = authority_counts.get(auth_level, 0) + 1
        
        report.append(f"**Total Authors Researched**: {len(high_priority)}")
        for auth_level, count in authority_counts.items():
            if count > 0:
                report.append(f"**{auth_level.name}**: {count} authors")
        
        # Action items
        report.append("\n### 🎯 RECOMMENDED ACTIONS")
        experts_to_add = [a for a in high_priority 
                         if AuthorityLevel(a.get("recommended_authority", 0)) in [
                             AuthorityLevel.NORMATIVE, 
                             AuthorityLevel.EXPERT_INTERPRETIVE
                         ]]
        
        if experts_to_add:
            report.append(f"1. **Add {len(experts_to_add)} new experts** to the expert database")
            for expert in experts_to_add[:5]:
                report.append(f"   - {expert['name']} ({AuthorityLevel(expert['recommended_authority']).name})")
        
        return "\n".join(report)
    
    def generate_expert_database_update(self, research_results: Dict) -> Dict:
        """Generate updated expert database entries."""
        new_experts = {}
        
        high_priority = research_results.get("high_priority_authors", [])
        for author in high_priority:
            auth_level = AuthorityLevel(author.get("recommended_authority", 0))
            
            # Only include experts with high authority
            if auth_level in [AuthorityLevel.NORMATIVE, AuthorityLevel.EXPERT_INTERPRETIVE]:
                new_experts[author["name"]] = {
                    "authority": auth_level.value,
                    "expertise": author.get("expertise_areas", []),
                    "research_notes": author.get("research_notes", ""),
                    "affiliation": author.get("current_affiliation", ""),
                    "source": "collection_analysis"
                }
        
        return new_experts
    
    def _create_research_profile(self, author_data: Dict) -> AuthorResearchProfile:
        """Create research profile from author data."""
        return AuthorResearchProfile(
            name=author_data["name"],
            document_count=author_data["document_count"],
            sample_titles=author_data.get("sample_titles", []),
            potential_affiliations=set(author_data.get("affiliations", [])),
            expertise_areas=author_data.get("expertise_indicators", []),
            accessibility_credentials=[]
        )
    
    def _research_single_author(self, profile: AuthorResearchProfile) -> AuthorResearchProfile:
        """Research a single author (placeholder for manual research)."""
        # This is a framework for research - actual implementation would involve:
        # 1. LinkedIn API or web scraping
        # 2. Google Scholar searches
        # 3. W3C member directory checks
        # 4. Social media presence analysis
        
        # For now, provide heuristic analysis
        profile = self._analyze_author_heuristically(profile)
        return profile
    
    def _analyze_author_heuristically(self, profile: AuthorResearchProfile) -> AuthorResearchProfile:
        """Analyze author using heuristic methods."""
        # Analyze based on document titles and expertise areas
        all_text = ' '.join(profile.sample_titles + profile.expertise_areas).lower()
        
        # Check for W3C involvement indicators
        if any(term in all_text for term in ['w3c', 'wcag', 'wai', 'working group']):
            profile.w3c_involvement = True
            profile.research_notes += "Potential W3C involvement based on content. "
        
        # Estimate authority level based on expertise breadth and document count
        expertise_score = len(profile.expertise_areas)
        doc_score = min(profile.document_count / 10, 1.0)  # Normalize to 0-1
        
        if profile.w3c_involvement and expertise_score >= 3:
            profile.recommended_authority = AuthorityLevel.NORMATIVE
            profile.research_notes += "High authority due to W3C involvement and broad expertise. "
        elif expertise_score >= 3 and doc_score > 0.5:
            profile.recommended_authority = AuthorityLevel.EXPERT_INTERPRETIVE
            profile.research_notes += "Expert level due to broad accessibility expertise. "
        elif doc_score > 0.3:
            profile.recommended_authority = AuthorityLevel.PROFESSIONAL
            profile.research_notes += "Professional level based on publication count. "
        else:
            profile.recommended_authority = AuthorityLevel.COMMUNITY
        
        # Check for known affiliations
        for affiliation in profile.potential_affiliations:
            affiliation_lower = affiliation.lower()
            for org, keywords in self.accessibility_organizations.items():
                if any(keyword in affiliation_lower for keyword in keywords):
                    profile.current_affiliation = f"{org} ({affiliation})"
                    profile.accessibility_credentials.append(org)
                    profile.research_notes += f"Affiliated with {org}. "
                    
                    # Boost authority for known accessibility organizations
                    if profile.recommended_authority.value < AuthorityLevel.EXPERT_INTERPRETIVE.value:
                        profile.recommended_authority = AuthorityLevel.EXPERT_INTERPRETIVE
        
        profile.research_status = "automated_analysis"
        return profile


def create_manual_research_template(author_research_file: str) -> str:
    """Create a template for manual research."""
    try:
        with open(author_research_file, 'r', encoding='utf-8') as f:
            research_data = json.load(f)
    except FileNotFoundError:
        print(f"Research file not found: {author_research_file}")
        return ""
    
    template = []
    template.append("# Manual Author Research Template")
    template.append("=" * 50)
    template.append("\nInstructions: For each high-priority author, research the following:")
    template.append("1. Search LinkedIn for current role and accessibility experience")
    template.append("2. Check W3C member directory: https://www.w3.org/groups/")
    template.append("3. Search for their personal website or blog")
    template.append("4. Look for accessibility-related social media presence")
    template.append("5. Check for speaking engagements at accessibility conferences")
    template.append("\n" + "-" * 50)
    
    high_priority = research_data.get("high_priority_authors", [])
    for i, author in enumerate(high_priority[:10], 1):  # Limit to top 10
        template.append(f"\n## {i}. {author['name']} ({author['document_count']} documents)")
        template.append(f"**Sample Work**: {author['sample_titles'][0] if author['sample_titles'] else 'N/A'}")
        template.append(f"**Expertise Indicators**: {', '.join(author.get('expertise_indicators', []))}")
        
        template.append("\n**Research Checklist**:")
        template.append("- [ ] LinkedIn profile found")
        template.append("- [ ] Current role/affiliation identified")  
        template.append("- [ ] W3C involvement confirmed")
        template.append("- [ ] Accessibility credentials verified")
        template.append("- [ ] Personal website/blog found")
        template.append("- [ ] Social media presence checked")
        
        template.append("\n**Research Notes**:")
        template.append("```")
        template.append("Current Role: ")
        template.append("Organization: ")
        template.append("W3C Groups: ")
        template.append("Accessibility Focus: ")
        template.append("Recommended Authority Level: ")
        template.append("Additional Notes: ")
        template.append("```")
        template.append("\n" + "-" * 30)
    
    # Save template
    template_file = "MANUAL_RESEARCH_TEMPLATE.md"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(template))
    
    return template_file


def main():
    """Run author research toolkit."""
    print("👥 AUTHOR RESEARCH TOOLKIT")
    print("=" * 50)
    
    # Check if research file exists
    research_file = "author_research_needed.json"
    if not Path(research_file).exists():
        print(f"❌ Research file not found: {research_file}")
        print("Please run the collection analysis first to generate author research data.")
        return
    
    # Run automated research
    researcher = AuthorResearcher()
    results = researcher.research_author_batch(research_file)
    
    # Generate reports
    report = researcher.generate_research_report(results)
    with open("AUTHOR_RESEARCH_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Generate expert database updates
    new_experts = researcher.generate_expert_database_update(results)
    with open("new_experts_to_add.json", 'w', encoding='utf-8') as f:
        json.dump(new_experts, f, indent=2, ensure_ascii=False)
    
    # Create manual research template
    template_file = create_manual_research_template(research_file)
    
    print(f"\n✅ Author research complete!")
    print(f"📄 Research report: AUTHOR_RESEARCH_REPORT.md")
    print(f"👥 New experts file: new_experts_to_add.json")
    print(f"📋 Manual research template: {template_file}")
    
    # Summary
    high_priority_count = len(results.get("high_priority_authors", []))
    recommended_experts = len(new_experts)
    
    print(f"\n📊 Research Summary:")
    print(f"   - High priority authors analyzed: {high_priority_count}")
    print(f"   - New experts recommended: {recommended_experts}")
    print(f"   - Manual research template created for detailed investigation")


if __name__ == "__main__":
    main()