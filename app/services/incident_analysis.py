"""Incident Analysis Service.

Analyzes ticket patterns, identifies recurring technical problems across categories
and departments, extracts frequent keywords, and surfaces explainable hypotheses.
"""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List

from sqlalchemy import select

from app.constants import TicketStatus
from app.extensions import db
from app.models import Ticket

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is",
    "are", "was", "were", "it", "my", "our", "we", "i", "not", "cannot", "issue",
    "problem", "error", "failed", "when", "after", "please", "help", "need", "this",
    "that", "from", "by", "as", "have", "has", "do", "does", "did", "getting",
}


def _tokenize(text: str) -> List[str]:
    """Clean and tokenize text into meaningful keywords."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def analyze_recurring_incidents(min_frequency: int = 2) -> Dict[str, Any]:
    """Analyze all tickets to identify recurring failure clusters and problem hypotheses."""
    tickets = db.session.scalars(select(Ticket).order_by(Ticket.created_at.desc())).all()

    # 1. Category Frequency Breakdown
    category_counts = Counter(t.category for t in tickets)

    # 2. Frequent Keyword Clusters
    keyword_tickets = defaultdict(list)
    for t in tickets:
        tokens = set(_tokenize(t.title) + _tokenize(t.description)[:15])
        for token in tokens:
            keyword_tickets[token].append(t)

    # Filter keywords appearing at least min_frequency times
    recurring_patterns = []
    seen_combinations = set()

    for token, matching_tickets in keyword_tickets.items():
        if len(matching_tickets) >= min_frequency:
            # Group by category among the matches
            top_category = Counter(t.category for t in matching_tickets).most_common(1)[0][0]
            # Check affected departments
            departments = list({t.department.name for t in matching_tickets if t.department})

            pattern_key = f"{token}:{top_category}"
            if pattern_key in seen_combinations:
                continue
            seen_combinations.add(pattern_key)

            # Hypothesis generation
            sample_titles = [t.title for t in matching_tickets[:3]]
            hypothesis = (
                f"Repeated issue with keyword '{token}' detected in {len(matching_tickets)} tickets "
                f"primarily under category '{top_category}'. "
                f"Sample reports: \"{'; '.join(sample_titles)}\"."
            )

            recurring_patterns.append({
                "keyword": token,
                "frequency": len(matching_tickets),
                "primary_category": top_category,
                "departments": departments,
                "sample_tickets": [
                    {
                        "id": t.id,
                        "ticket_number": t.ticket_number,
                        "title": t.title,
                        "status": t.status,
                        "final_priority": t.final_priority,
                    }
                    for t in matching_tickets[:5]
                ],
                "hypothesis": hypothesis,
            })

    # Sort recurring patterns by highest frequency
    recurring_patterns.sort(key=lambda x: x["frequency"], reverse=True)

    return {
        "total_analyzed_tickets": len(tickets),
        "category_distribution": dict(category_counts),
        "recurring_patterns": recurring_patterns,
    }
