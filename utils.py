"""
Utility functions for text processing and data manipulation.
"""

import re
from typing import Any, Dict, List, Optional


def safe_get(d: Dict, *keys, default=None):
    """Safely get a nested key from a dict, returning default if missing."""
    cur = d
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def strip_html(text: Optional[str]) -> str:
    """Remove HTML and Jira wiki markup from text, returning plain text."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # remove HTML tags
    text = re.sub(r"\{code[^}]*\}.*?\{code\}", "", text, flags=re.S)  # remove Jira {code} blocks
    text = re.sub(r"(?m)^h\d\.\s*", "", text)  # remove headings
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # remove *bold*
    text = re.sub(r"_(.*?)_", r"\1", text)      # remove _italic_
    text = re.sub(r"\s+", " ", text).strip()   # collapse extra whitespace
    return text
