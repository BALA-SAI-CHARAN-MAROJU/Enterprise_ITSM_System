"""Rule-based priority recommendation engine.

Evaluates ticket attributes (impact, urgency, affected users, category)
deterministically without machine learning, and produces a recommended
priority along with an explainable justification reason.
"""

from dataclasses import dataclass, field
from typing import List

from app.constants import Priority, TicketCategory


@dataclass
class PriorityResult:
    recommended_priority: str
    total_score: int
    reasons: List[str] = field(default_factory=list)

    @property
    def justification(self) -> str:
        return " | ".join(self.reasons)


# Scoring constants
IMPACT_SCORES = {
    "critical": 40,
    "high": 30,
    "medium": 20,
    "low": 10,
}

URGENCY_SCORES = {
    "critical": 30,
    "high": 22,
    "medium": 14,
    "low": 6,
}

CATEGORY_MODIFIERS = {
    TicketCategory.SECURITY: 10,
    TicketCategory.DATABASE: 8,
    TicketCategory.NETWORK: 8,
    TicketCategory.HARDWARE: 4,
    TicketCategory.SOFTWARE: 0,
    TicketCategory.OTHER: 0,
}


def calculate_priority(
    category: str,
    business_impact: str,
    urgency: str,
    affected_users_count: int = 1,
) -> PriorityResult:
    """Calculate recommended priority and generate explanation reasons."""
    reasons: List[str] = []
    impact_norm = (business_impact or "low").strip().lower()
    urgency_norm = (urgency or "low").strip().lower()
    category_norm = (category or TicketCategory.OTHER).strip()

    # 1. Business Impact Score (0 - 40)
    impact_score = IMPACT_SCORES.get(impact_norm, 10)
    reasons.append(f"Business impact is '{impact_norm}' (+{impact_score} pts)")

    # 2. Urgency Score (0 - 30)
    urgency_score = URGENCY_SCORES.get(urgency_norm, 6)
    reasons.append(f"Urgency is '{urgency_norm}' (+{urgency_score} pts)")

    # 3. Affected Users Count Score (0 - 20)
    try:
        user_count = max(1, int(affected_users_count))
    except (TypeError, ValueError):
        user_count = 1

    if user_count >= 50:
        users_score = 20
        reasons.append(f"Affects widespread users ({user_count} users: +20 pts)")
    elif user_count >= 11:
        users_score = 15
        reasons.append(f"Affects a team/group ({user_count} users: +15 pts)")
    elif user_count >= 2:
        users_score = 10
        reasons.append(f"Affects multiple individuals ({user_count} users: +10 pts)")
    else:
        users_score = 5
        reasons.append(f"Affects single user (+5 pts)")

    # 4. Category Modifier (-10 to +10)
    cat_mod = CATEGORY_MODIFIERS.get(category_norm, 0)
    if cat_mod > 0:
        reasons.append(f"Category '{category_norm}' carries an operational risk modifier (+{cat_mod} pts)")
    else:
        reasons.append(f"Category '{category_norm}' modifier (+0 pts)")

    total_score = impact_score + urgency_score + users_score + cat_mod

    # Priority determination with safety overrides
    if (impact_norm == "critical" and urgency_norm == "critical") or (user_count >= 100 and impact_norm in ("critical", "high")):
        recommended = Priority.CRITICAL
        reasons.append("Safety rule applied: Critical impact and urgency mandate Critical priority override.")
    elif total_score >= 75:
        recommended = Priority.CRITICAL
    elif total_score >= 55:
        recommended = Priority.HIGH
    elif total_score >= 35:
        recommended = Priority.MEDIUM
    else:
        recommended = Priority.LOW

    reasons.append(f"Total calculated score: {total_score} points -> Priority: {recommended}")

    return PriorityResult(
        recommended_priority=recommended,
        total_score=total_score,
        reasons=reasons,
    )
