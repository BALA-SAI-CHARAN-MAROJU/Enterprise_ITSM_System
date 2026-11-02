from app.constants import Priority, TicketCategory
from app.services.priority_engine import calculate_priority


def test_priority_critical_when_impact_and_urgency_are_critical():
    result = calculate_priority(
        category=TicketCategory.NETWORK,
        business_impact="critical",
        urgency="critical",
        affected_users_count=50,
    )
    assert result.recommended_priority == Priority.CRITICAL
    assert result.total_score >= 75
    assert "Critical impact and urgency" in result.justification or result.total_score >= 75


def test_priority_high():
    result = calculate_priority(
        category=TicketCategory.DATABASE,
        business_impact="high",
        urgency="high",
        affected_users_count=5,
    )
    assert result.recommended_priority == Priority.HIGH
    assert 55 <= result.total_score < 75


def test_priority_medium():
    result = calculate_priority(
        category=TicketCategory.HARDWARE,
        business_impact="medium",
        urgency="medium",
        affected_users_count=1,
    )
    assert result.recommended_priority == Priority.MEDIUM
    assert 35 <= result.total_score < 55


def test_priority_low():
    result = calculate_priority(
        category=TicketCategory.OTHER,
        business_impact="low",
        urgency="low",
        affected_users_count=1,
    )
    assert result.recommended_priority == Priority.LOW
    assert result.total_score < 35


def test_priority_category_modifier_boosts_score():
    base = calculate_priority(
        category=TicketCategory.SOFTWARE,
        business_impact="medium",
        urgency="medium",
        affected_users_count=1,
    )
    boosted = calculate_priority(
        category=TicketCategory.SECURITY,
        business_impact="medium",
        urgency="medium",
        affected_users_count=1,
    )
    assert boosted.total_score == base.total_score + 10
