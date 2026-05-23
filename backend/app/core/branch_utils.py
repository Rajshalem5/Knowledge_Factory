"""Utility for normalizing and matching academic branch names."""

import re

# Map of common branch abbreviations to their full names and vice-versa
BRANCH_SYNONYMS = {
    "it": ["information technology", "it", "infotech"],
    "cse": ["computer science", "computer science and engineering", "cse", "compsci"],
    "ece": ["electronics and communication", "electronics and communication engineering", "ece", "electronics & communication"],
    "eee": ["electrical and electronics", "electrical and electronics engineering", "eee", "electrical & electronics"],
    "me": ["mechanical engineering", "mechanical", "me"],
    "ce": ["civil engineering", "civil", "ce"],
    "ai": ["artificial intelligence", "ai", "artificial intelligence and machine learning", "ai & ml", "aiml"],
    "ds": ["data science", "ds", "data science and engineering"],
}

def is_branch_eligible(candidate_branch: str, allowed_branches: list[str]) -> bool:
    """
    Check if a candidate's branch is eligible based on a list of allowed branches.
    Handles common abbreviations and case-insensitive matching.
    """
    if not allowed_branches:
        return True
    
    # Normalize candidate branch
    cb = candidate_branch.strip().lower()
    # Remove common suffixes/prefixes like "B.Tech in ", "Department of " etc.
    cb = re.sub(r'^(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|diploma)\s+(in|of)\s+', '', cb)
    cb = cb.replace("&", "and")
    
    # Get all potential synonyms for the candidate's branch
    candidate_synonyms = {cb}
    for syn_list in BRANCH_SYNONYMS.values():
        if cb in syn_list:
            candidate_synonyms.update(syn_list)
            break

    # Normalize allowed branches and check for any overlap
    for allowed in allowed_branches:
        norm_allowed = allowed.strip().lower().replace("&", "and")
        
        # 1. Direct match (normalized)
        if norm_allowed in candidate_synonyms:
            return True
        
        # 2. Check if norm_allowed is a key in synonyms
        if norm_allowed in BRANCH_SYNONYMS:
            if any(syn in candidate_synonyms for syn in BRANCH_SYNONYMS[norm_allowed]):
                return True
        
        # 3. Partial match for "CS" related keywords
        if "cs" in norm_allowed or "computer" in norm_allowed:
            if "computer" in cb or "cs" in cb or "it" in cb or "information technology" in cb:
                return True
                
    return False
