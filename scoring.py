"""
scoring.py
-----------
Deterministic scoring engine for ranking opportunities.

Pure logic: extracted opportunity vs student profile.
Weights: profile_fit=40%, urgency=35%, completeness=25%

NO machine learning, NO external context, NO comparison with base dataset.
"""

from datetime import date, datetime
from typing import Dict, List, Any, Optional


def score_opportunity(extracted: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single extracted opportunity against student profile.
    
    Args:
        extracted: Opportunity dict from extract_opportunity() with email_id, type, etc.
        profile: Student profile dict with degree, cgpa, skills, preferred_types, etc.
    
    Returns:
        Dict with keys:
        {
            "total": float (0-100),
            "profile_fit": float (0-40),
            "urgency": float (0-35),
            "completeness": float (0-25),
            "days_left": int or None
        }
    """
    
    # === PROFILE FIT (max 40) ===
    fit = 0.0
    
    # Type match (+15)
    if extracted.get('type') in [t.lower() for t in profile.get('preferred_types', [])]:
        fit += 15
    
    # CGPA eligible (+10)
    min_cgpa = extracted.get('min_cgpa')
    if min_cgpa is None or profile.get('cgpa', 0) >= min_cgpa:
        fit += 10
    
    # Skill overlap (+10)
    user_skills = set(s.lower() for s in profile.get('skills', []))
    req_skills = set(s.lower() for s in (extracted.get('required_skills') or []))
    
    if req_skills:
        overlap = len(user_skills & req_skills) / len(req_skills)
        fit += min(overlap, 1.0) * 10
    else:
        fit += 5  # No skills required = accessible to anyone
    
    # Location match (+5)
    loc_pref = profile.get('location_pref', 'any').lower()
    loc_opp = extracted.get('location', 'other').lower()
    
    if loc_pref == 'any' or loc_pref == loc_opp or loc_opp == 'remote':
        fit += 5
    
    # === URGENCY (max 35) ===
    urgency = 0.0
    days_left = None
    deadline_str = extracted.get('deadline')
    
    if deadline_str:
        try:
            # Parse deadline string as ISO format (YYYY-MM-DD)
            deadline_date = date.fromisoformat(deadline_str)
            days_left = (deadline_date - date.today()).days
            
            # Urgency scoring based on days left
            if days_left <= 0:
                urgency = 0  # Expired
            elif days_left <= 3:
                urgency = 35  # Highly urgent
            elif days_left <= 7:
                urgency = 30  # Urgent
            elif days_left <= 14:
                urgency = 25  # This week/next week
            elif days_left <= 30:
                urgency = 18  # This month
            elif days_left <= 60:
                urgency = 10  # Next 2 months
            else:
                urgency = 5  # Far future
        except Exception as e:
            # Couldn't parse deadline
            urgency = 8  # Rolling deadline or unclear
            days_left = None
    else:
        urgency = 8  # No deadline specified (rolling deadline)
    
    # === COMPLETENESS (max 25) ===
    comp = 0.0
    
    if extracted.get('apply_link'):
        comp += 10  # Clear way to apply
    
    if extracted.get('deadline') or extracted.get('deadline_display'):
        comp += 8  # Deadline is clear
    
    if extracted.get('required_documents'):
        comp += 4  # Requirements are documented
    
    if extracted.get('stipend_pkr'):
        comp += 3  # Financial information available
    
    # === TOTAL SCORE ===
    total = fit + urgency + comp
    
    # Apply duplicate penalty
    if extracted.get('is_duplicate', False):
        total *= 0.70  # 30% penalty for duplicates
    
    return {
        "total": round(total, 1),
        "profile_fit": round(fit, 1),
        "urgency": round(urgency, 1),
        "completeness": round(comp, 1),
        "days_left": days_left
    }


def rank_opportunities(
    extracted_list: List[Dict[str, Any]],
    profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all opportunities and rank by total score (highest first).
    
    Args:
        extracted_list: List of extracted opportunity dicts
        profile: Student profile dict
    
    Returns:
        List of enriched dicts with 'scores' field, sorted by total score descending
    """
    results = []
    
    for item in extracted_list:
        scores = score_opportunity(item, profile)
        enriched = {**item, "scores": scores, "days_left": scores.get("days_left")}
        results.append(enriched)
    
    # Sort by total score descending
    results.sort(key=lambda x: x['scores']['total'], reverse=True)
    
    # Assign ranks
    for i, item in enumerate(results):
        item['rank'] = i + 1
    
    return results


def get_urgency_label(days_left: Optional[int]) -> str:
    """
    Return emoji + label for deadline urgency.
    
    Args:
        days_left: Days until deadline, or None if rolling/unknown
    
    Returns:
        Human-readable urgency label with emoji
    """
    if days_left is None:
        return "🔵 Rolling deadline"
    
    if days_left <= 0:
        return "⚫ Expired"
    
    if days_left <= 5:
        return "🔴 Urgent — act today"
    
    if days_left <= 14:
        return "🟡 Apply this week"
    
    return "🟢 Plenty of time"


def get_summary_stats(ranked: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate statistics for the ranked list.
    
    Args:
        ranked: List of ranked opportunity dicts with scores
    
    Returns:
        Dict with summary statistics for UI display
    """
    total = len(ranked)
    
    # Count urgent opportunities (0-7 days left)
    urgent = sum(
        1 for r in ranked
        if r.get('days_left') is not None
        and 0 <= r['days_left'] <= 7
    )
    
    # Highest score
    top_score = ranked[0]['scores']['total'] if ranked else 0
    
    # Count opportunities with apply links
    has_link = sum(1 for r in ranked if r.get('apply_link'))
    
    # Average score
    avg_score = round(
        sum(r['scores']['total'] for r in ranked) / total,
        1
    ) if total > 0 else 0
    
    return {
        "total": total,
        "urgent": urgent,
        "top_score": top_score,
        "has_link": has_link,
        "avg_score": avg_score
    }


def get_fit_breakdown(scores: Dict[str, Any]) -> str:
    """
    Return human-readable breakdown of score components.
    
    Args:
        scores: Dict from score_opportunity with component scores
    
    Returns:
        Formatted string showing breakdown
    """
    fit = scores.get('profile_fit', 0)
    urg = scores.get('urgency', 0)
    comp = scores.get('completeness', 0)
    
    return f"Profile fit: {fit}/40 | Urgency: {urg}/35 | Completeness: {comp}/25"


def get_score_color(total: float) -> str:
    """
    Return Streamlit color for score visualization.
    
    Args:
        total: Total score (0-100)
    
    Returns:
        Color name: 'green', 'orange', 'red'
    """
    if total >= 70:
        return "green"
    elif total >= 50:
        return "orange"
    else:
        return "red"


def get_recommendation(total: float) -> str:
    """
    Return recommendation text based on score.
    
    Args:
        total: Total score (0-100)
    
    Returns:
        Short recommendation string
    """
    if total >= 80:
        return "⭐⭐⭐ Excellent match — Highly recommended"
    elif total >= 70:
        return "⭐⭐ Good match — Worth applying"
    elif total >= 60:
        return "⭐ Okay match — Consider applying"
    elif total >= 50:
        return "Consider if time permits"
    else:
        return "Lower priority"
