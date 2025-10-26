"""
Data models for representing Jira issues.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class JiraIssue:
    """Represents a single Jira issue and its relevant fields."""
    
    key: str
    project: str
    title: str
    status: str
    priority: Optional[str]
    reporter: Optional[str]
    assignee: Optional[str]
    labels: List[str]
    created: Optional[str]
    updated: Optional[str]
    description: str
    comments: List[Dict[str, Any]]

    def to_corpus(self) -> Dict[str, Any]:
        """Convert issue into JSON structure suitable for LLM training."""
        return asdict(self)
