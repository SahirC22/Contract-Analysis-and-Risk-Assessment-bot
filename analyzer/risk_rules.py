"""
risk_rules.py - Advanced Rule-Based Risk Detection

Enhanced with:
- Comprehensive legal pattern matching
- Weighted risk scoring
- Category-based analysis
- Detailed risk explanations
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import re


RISK_LEVELS = ["Low", "Medium", "High"]


@dataclass
class RuleMatch:
    rule_id: str
    description: str
    risk_level: str
    category: str = "General"
    severity_weight: float = 1.0


# Expanded and categorized rule set
RULES: Dict[str, Dict] = {
    # HIGH RISK - Liability & Indemnification
    "unlimited_liability": {
        "pattern": re.compile(
            r"\b(unlimited|unbounded|without limit of) liability\b|"
            r"\bliable for all (damages|losses|claims)\b|"
            r"\bno cap on liability\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Liability",
        "severity_weight": 2.5,
        "description": "Unlimited or uncapped liability exposure for one party, creating potentially catastrophic financial risk."
    },
    
    "one_sided_indemnity": {
        "pattern": re.compile(
            r"\b(shall|must|agrees to) indemnify.+(and hold harmless|from and against all|"
            r"defend.*against any)\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Liability",
        "severity_weight": 2.0,
        "description": "Strong unilateral indemnification obligation favoring one party without reciprocal protection."
    },
    
    "broad_consequential_damages": {
        "pattern": re.compile(
            r"\bliable for (any|all) consequential damages\b|"
            r"\bincluding.*lost profits.*lost revenue\b|"
            r"\bindirect.*special.*incidental damages\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Liability",
        "severity_weight": 2.0,
        "description": "Broad liability for consequential damages including lost profits, revenue, or business opportunities."
    },
    
    # HIGH RISK - Termination & Duration
    "no_termination_right": {
        "pattern": re.compile(
            r"\b(may not|cannot|shall not) terminate\b|"
            r"\bno right to terminate\b|"
            r"\bnon-terminable\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Termination",
        "severity_weight": 2.5,
        "description": "Explicitly removes or severely restricts termination rights, potentially locking party into unfavorable agreement."
    },
    
    "unilateral_termination": {
        "pattern": re.compile(
            r"\bmay terminate (this )?agreement at any time( without (notice|cause))?\b|"
            r"\bat.*sole discretion.*terminate\b|"
            r"\bterminate.*immediately.*without (reason|cause)\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Termination",
        "severity_weight": 2.0,
        "description": "Unilateral termination rights granted to one party, creating business instability and relationship imbalance."
    },
    
    "perpetual_term": {
        "pattern": re.compile(
            r"\bperpetual\b|"
            r"\bin perpetuity\b|"
            r"\bno expiration\b|"
            r"\bunlimited duration\b",
            re.IGNORECASE
        ),
        "risk_level": "High",
        "category": "Duration",
        "severity_weight": 1.8,
        "description": "Perpetual or indefinite contract term without clear exit mechanism or review period."
    },
    
    # MEDIUM RISK - Payment & Financial
    "automatic_renewal": {
        "pattern": re.compile(
            r"\b(automatically|auto-) renew(s|al)?\b|"
            r"\bshall be renewed automatically\b|"
            r"\bunless.*notice.*renew\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Financial",
        "severity_weight": 1.5,
        "description": "Automatic renewal provision without explicit opt-in, potentially creating unwanted long-term obligations."
    },
    
    "vague_payment_terms": {
        "pattern": re.compile(
            r"\bpayment.*(as mutually agreed|to be determined|from time to time)\b|"
            r"\breasonable (fee|price|compensation)\b|"
            r"\bpayment terms.*subject to change\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Financial",
        "severity_weight": 1.5,
        "description": "Unclear, variable, or undefined payment terms creating uncertainty in financial obligations."
    },
    
    "penalty_interest_high": {
        "pattern": re.compile(
            r"\binterest.*(rate|charge).*(2[4-9]|[3-9][0-9])\s?%|"
            r"\bpenalty.*(2[0-9]|[3-9][0-9])\s?%",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Financial",
        "severity_weight": 1.5,
        "description": "Excessive interest rates or financial penalties for late payment or breach."
    },
    
    "price_escalation": {
        "pattern": re.compile(
            r"\bprice.*increase.*without (notice|limit)\b|"
            r"\bunilateral.*pricing.*adjustment\b|"
            r"\bsubject to.*price.*changes.*discretion\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Financial",
        "severity_weight": 1.5,
        "description": "Unilateral price increase provisions without reasonable caps or notice requirements."
    },
    
    # MEDIUM RISK - Intellectual Property
    "broad_ip_assignment": {
        "pattern": re.compile(
            r"\bassigns? all (intellectual property|IP|rights)\b|"
            r"\ball rights?,? title,? and interest\b|"
            r"\bexclusive.*ownership.*all.*work\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Intellectual Property",
        "severity_weight": 1.8,
        "description": "Very broad assignment of intellectual property rights without limitations or exceptions."
    },
    
    "work_for_hire": {
        "pattern": re.compile(
            r"\bwork (made )?for hire\b|"
            r"\ball.*work.*deemed.*property of\b|"
            r"\bcreated.*course of.*automatically owned\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Intellectual Property",
        "severity_weight": 1.6,
        "description": "Work-for-hire provision transferring all IP rights without compensation or credit."
    },
    
    "no_derivative_works": {
        "pattern": re.compile(
            r"\bno derivative works\b|"
            r"\bcannot.*modify.*create.*based on\b|"
            r"\bprohibited.*from.*creating.*adaptations\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Intellectual Property",
        "severity_weight": 1.3,
        "description": "Restrictive prohibition on creating derivative works or modifications."
    },
    
    # MEDIUM RISK - Confidentiality & Data
    "broad_confidentiality": {
        "pattern": re.compile(
            r"\bperpetual confidentiality\b|"
            r"\bconfidentiality.*(without time limitation|in perpetuity)\b|"
            r"\bconfidential.*forever\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Confidentiality",
        "severity_weight": 1.5,
        "description": "Overly broad or perpetual confidentiality obligations restricting future business operations."
    },
    
    "broad_nda_scope": {
        "pattern": re.compile(
            r"\ball information.*deemed confidential\b|"
            r"\bany and all.*confidential\b|"
            r"\beverything.*disclosed.*confidential\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Confidentiality",
        "severity_weight": 1.4,
        "description": "Excessively broad definition of confidential information without reasonable exceptions."
    },
    
    # MEDIUM RISK - Performance & Obligations
    "ambiguous_terms": {
        "pattern": re.compile(
            r"\breasonable efforts\b|"
            r"\bcommercially reasonable\b|"
            r"\bbest efforts\b|"
            r"\bto the extent (possible|practicable)\b|"
            r"\bif (reasonably|commercially) feasible\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Performance",
        "severity_weight": 1.2,
        "description": "Ambiguous or subjective performance standards that may be difficult to enforce or measure."
    },
    
    "open_ended_obligations": {
        "pattern": re.compile(
            r"\band any other.*as.*may require\b|"
            r"\bincluding but not limited to\b.*\bany\b|"
            r"\bsuch other (duties|obligations).*determined\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Performance",
        "severity_weight": 1.5,
        "description": "Open-ended obligations allowing unilateral expansion of responsibilities."
    },
    
    "no_limitation_period": {
        "pattern": re.compile(
            r"\bno (time )?limit.*obligations\b|"
            r"\bobligations.*survive.*indefinitely\b|"
            r"\bperpetual obligations\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Performance",
        "severity_weight": 1.4,
        "description": "Obligations that survive indefinitely without reasonable time limitations."
    },
    
    # MEDIUM RISK - Dispute Resolution
    "mandatory_arbitration": {
        "pattern": re.compile(
            r"\b(shall|must) (be )?resolve[d]? (by|through) (binding )?arbitration\b|"
            r"\bexclusive.*arbitration\b|"
            r"\bwaive.*right.*jury trial\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Dispute Resolution",
        "severity_weight": 1.3,
        "description": "Mandatory arbitration clause potentially limiting access to courts and jury trials."
    },
    
    "unfavorable_jurisdiction": {
        "pattern": re.compile(
            r"\bexclusive jurisdiction.*(in|of)\b|"
            r"\bvenue.*limited to\b|"
            r"\bmust.*file.*in\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Dispute Resolution",
        "severity_weight": 1.2,
        "description": "Exclusive jurisdiction clause that may create inconvenience or disadvantage in disputes."
    },
    
    # LOW-MEDIUM RISK - Representations & Warranties
    "limited_warranties": {
        "pattern": re.compile(
            r"\bas is\b.*\bwithout (any )?warranties\b|"
            r"\bdisclaims all warranties\b|"
            r"\bno (express|implied) warranties\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Warranties",
        "severity_weight": 1.3,
        "description": "Broad disclaimer of warranties limiting recourse for defects or non-performance."
    },
    
    "seller_representation_only": {
        "pattern": re.compile(
            r"\bmakes no representations\b|"
            r"\bbuyer.*acknowledges.*no.*representations\b|"
            r"\bexcept.*expressly.*stated.*no representations\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Warranties",
        "severity_weight": 1.2,
        "description": "Limitation on representations potentially leaving party without recourse for misstatements."
    },
    
    # MEDIUM RISK - Change Control
    "unilateral_modification": {
        "pattern": re.compile(
            r"\bmay.*modify.*(at any time|without notice)\b|"
            r"\breserves? (the )?right.*amend.*sole discretion\b|"
            r"\bchanges?.*effective immediately\b",
            re.IGNORECASE
        ),
        "risk_level": "Medium",
        "category": "Modifications",
        "severity_weight": 1.5,
        "description": "Unilateral modification rights allowing one party to change terms without consent or notice."
    },
}


def evaluate_rules(clause_text: str) -> List[RuleMatch]:
    """
    Evaluate clause against comprehensive rule set.
    
    Returns:
        List of RuleMatch objects for all matching patterns
    """
    if not clause_text or not isinstance(clause_text, str):
        return []
    
    matches: List[RuleMatch] = []
    text = clause_text.strip()
    
    for rule_id, spec in RULES.items():
        if spec["pattern"].search(text):
            matches.append(
                RuleMatch(
                    rule_id=rule_id,
                    description=spec["description"],
                    risk_level=spec["risk_level"],
                    category=spec.get("category", "General"),
                    severity_weight=spec.get("severity_weight", 1.0)
                )
            )
    
    return matches


def aggregate_risk_from_rules(matches: List[RuleMatch]) -> str:
    """
    Combine multiple rule matches using weighted severity scoring.
    
    Args:
        matches: List of RuleMatch objects
        
    Returns:
        Overall risk level: "Low", "Medium", or "High"
    """
    if not matches:
        return "Low"
    
    # If any High risk, return High
    if any(m.risk_level == "High" for m in matches):
        return "High"
    
    # Calculate weighted score for Medium risks
    medium_matches = [m for m in matches if m.risk_level == "Medium"]
    
    if not medium_matches:
        return "Low"
    
    # If 3+ medium risks or high weighted severity, escalate to High
    total_weight = sum(m.severity_weight for m in medium_matches)
    
    if len(medium_matches) >= 3 or total_weight >= 5.0:
        return "High"
    
    return "Medium"


def get_risk_summary(matches: List[RuleMatch]) -> Dict[str, any]:
    """
    Generate detailed risk summary from rule matches.
    
    Returns:
        Dictionary with risk categories, counts, and severity scores
    """
    if not matches:
        return {
            "total_matches": 0,
            "risk_level": "Low",
            "categories": {},
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "total_severity": 0.0
        }
    
    categories = {}
    for match in matches:
        cat = match.category
        if cat not in categories:
            categories[cat] = {
                "count": 0,
                "rules": [],
                "severity": 0.0
            }
        categories[cat]["count"] += 1
        categories[cat]["rules"].append(match.rule_id)
        categories[cat]["severity"] += match.severity_weight
    
    high_risk = [m for m in matches if m.risk_level == "High"]
    medium_risk = [m for m in matches if m.risk_level == "Medium"]
    total_severity = sum(m.severity_weight for m in matches)
    
    return {
        "total_matches": len(matches),
        "risk_level": aggregate_risk_from_rules(matches),
        "categories": categories,
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "total_severity": total_severity,
        "top_concerns": [m.description for m in sorted(
            matches,
            key=lambda x: (
                2 if x.risk_level == "High" else 1,
                x.severity_weight
            ),
            reverse=True
        )[:5]]
    }