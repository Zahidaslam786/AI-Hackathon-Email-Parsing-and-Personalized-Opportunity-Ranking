"""
pipeline.py
-----------
All Claude API calls for email classification, opportunity detection, and information extraction.

Functions:
  - classify_emails(emails: list) -> dict
  - extract_opportunity(email: dict) -> dict
  - generate_reasoning(opportunity: dict, profile: dict) -> str
"""

import json
import os
from typing import Dict, List, Any

try:
    import anthropic
    # Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
    else:
        client = None
except Exception as e:
    print(f"Warning: Could not initialize Anthropic client: {e}")
    client = None

MODEL = "claude-sonnet-4-20250514"


def classify_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Screen all emails and classify them as:
    - "opportunity" (real opportunity)
    - "admin" (administrative, social, non-career)
    - "spam" (phishing, scams, unrelated)
    
    Args:
        emails: List of email dicts with 'id', 'subject', 'body', 'sender', etc.
    
    Returns:
        Same emails list with added 'label' field: "opportunity" | "admin" | "spam"
    
    Raises:
        Exception: If API call fails (caught and handled with safe fallback)
    """
    if not client:
        print("⚠️ ANTHROPIC_API_KEY not set. Using demo classification...")
        return _classify_emails_demo(emails)
    
    try:
        # Build the prompt with all emails numbered
        email_list_text = ""
        for email in emails:
            email_list_text += f"\n\n---\nEmail ID: {email['id']}\nSubject: {email['subject']}\nFrom: {email['sender']}\nBody: {email['body'][:500]}\n---"
        
        prompt = f"""You are an email classifier for a student opportunity system. Classify each email as one of:
- "opportunity": Contains a real career/academic opportunity (internship, scholarship, fellowship, research, competition, hackathon, award, grant, event, etc.)
- "admin": Administrative notices, event invitations, photos, social events, campus notices (not career-related)
- "spam": Phishing, scams, lottery prizes, "get rich quick" schemes, suspicious links, fake urgency

Emails to classify:
{email_list_text}

Return a JSON array with this exact format (no markdown, just pure JSON):
[
  {{"id": 1, "label": "opportunity"}},
  {{"id": 2, "label": "admin"}},
  ...
]

Only return the JSON array, nothing else."""

        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Parse the response
        response_text = response.content[0].text.strip()
        classifications = json.loads(response_text)
        
        # Create a lookup dict
        label_map = {item['id']: item['label'] for item in classifications}
        
        # Add labels to original emails
        for email in emails:
            email['label'] = label_map.get(email['id'], 'opportunity')  # Default to opportunity if not found
        
        return emails
    
    except Exception as e:
        print(f"Error in classify_emails: {e}")
        # Safe fallback: use demo classification
        return _classify_emails_demo(emails)


def _classify_emails_demo(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Demo classification using simple keyword matching and heuristics.
    """
    spam_keywords = ["FREE", "CLAIM", "PRIZE", "WINNER", "URGENT", "SUSPENDED", "verify your account", "bank details", "click link", "make money"]
    admin_keywords = ["PHOTO", "PIZZA", "CAFETERIA", "SOCIAL", "ALUMNI NETWORKING", "ALUMNI NIGHT", "NETWORKING", "PORTRAIT"]
    
    for email in emails:
        subject = email.get('subject', '').upper()
        body = email.get('body', '').upper()
        combined = subject + " " + body[:300]  # First 300 chars of body
        
        # Check for spam
        if any(keyword in combined for keyword in spam_keywords):
            email['label'] = 'spam'
        # Check for admin
        elif any(keyword in combined for keyword in admin_keywords):
            email['label'] = 'admin'
        # Default to opportunity
        else:
            email['label'] = 'opportunity'
    
    return emails


def extract_opportunity(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured fields from ONE opportunity email using Claude.
    Extraction is from email itself only (no RAG context).
    
    Args:
        email: Single email dict with 'id', 'subject', 'body', etc.
    
    Returns:
        Dict with structured opportunity fields:
        {
            "title": str,
            "type": "internship|scholarship|fellowship|competition|research|job|event|other",
            "organization": str,
            "deadline": "YYYY-MM-DD or null",
            "deadline_display": "human readable date or null",
            "min_cgpa": float or null,
            "required_skills": [str],
            "required_documents": [str],
            "stipend_pkr": int or null,
            "location": "lahore|islamabad|karachi|remote|international|other",
            "apply_link": str or null,
            "duration": "duration string or null",
            "summary": "one sentence description"
        }
    """
    if not client:
        return _fallback_extract(email)
    
    try:
        from datetime import date
        
        prompt = f"""You are an AI that extracts structured information from opportunity emails.

EMAIL SUBJECT: {email['subject']}
EMAIL BODY: {email['body']}

Extract the following fields and return ONLY a valid JSON object (no markdown, no explanation, no code fences):

{{
  "title": "short opportunity title or job/scholarship name",
  "type": "internship OR scholarship OR fellowship OR competition OR research OR job OR event OR other",
  "organization": "organization or company name",
  "deadline": "YYYY-MM-DD or null if not found",
  "deadline_display": "human readable date like 'April 30, 2026' or null",
  "min_cgpa": "minimum CGPA as float or null",
  "required_skills": ["skill1", "skill2", "..."],
  "required_documents": ["CV", "transcript", "..."],
  "stipend_pkr": "monthly stipend in PKR as integer (convert USD at 280/USD), null if not paid",
  "location": "lahore OR islamabad OR karachi OR remote OR international OR other",
  "apply_link": "application URL or email, null if not found",
  "duration": "duration string like '3 months' or '6-12 months', null if not found",
  "summary": "one sentence describing the opportunity"
}}

Rules:
- Extract ONLY from the email text provided
- If a field is not mentioned, use null (not empty string)
- required_skills: list of technical skills mentioned (Python, ML, NLP, etc.)
- required_documents: what they need to apply (CV, transcript, etc.)
- stipend_pkr: if given in USD, convert using 1 USD = 280 PKR
- For deadlines, parse month and day, assume year 2026
- location: infer from email text or default to "other"
- type: one word only from the list above"""

        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract and clean response
        text = response.content[0].text.strip()
        # Remove markdown code fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(text)
        return result
    
    except Exception as e:
        print(f"Error in extract_opportunity (API): {e}")
        # Fall back to rule-based extraction
        return _fallback_extract(email)


def _fallback_extract(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based extraction using regex when Claude API is unavailable.
    """
    import re
    from datetime import date
    
    body = email.get('body', '')
    subject = email.get('subject', '')
    
    # Extract deadline (flexible date parsing)
    deadline_pattern = r'(\d{1,2}(?:st|nd|rd|th)?)\s+(\w+)\s+(?:2026)?|(\w+)\s+(\d{1,2}),?\s+2026'
    deadline_match = re.search(deadline_pattern, body, re.IGNORECASE)
    deadline_display = deadline_match.group(0) if deadline_match else None
    
    # Extract URL
    url_match = re.search(r'https?://[^\s]+', body)
    apply_link = url_match.group(0) if url_match else None
    
    # Extract CGPA
    cgpa_match = re.search(r'(?:min|minimum|cgpa)[^\d]*(\d\.\d)', body, re.IGNORECASE)
    min_cgpa = float(cgpa_match.group(1)) if cgpa_match else None
    
    # Extract stipend PKR
    pkr_match = re.search(r'PKR\s*([\d,]+)', body, re.IGNORECASE)
    stipend_pkr = None
    if pkr_match:
        try:
            stipend_pkr = int(pkr_match.group(1).replace(',', ''))
        except:
            pass
    
    # Extract stipend USD (convert to PKR)
    if not stipend_pkr:
        usd_match = re.search(r'USD\s*([\d,]+)|USD\s*(\d+(?:,\d+)?)', body, re.IGNORECASE)
        if usd_match:
            try:
                usd_amount = int(usd_match.group(1).replace(',', '') if usd_match.group(1) else usd_match.group(2).replace(',', ''))
                stipend_pkr = int(usd_amount * 280)
            except:
                pass
    
    # Determine opportunity type
    opp_type = "internship"
    if 'scholarship' in body.lower():
        opp_type = "scholarship"
    elif 'fellowship' in body.lower():
        opp_type = "fellowship"
    elif any(w in body.lower() for w in ['hackathon', 'competition', 'contest']):
        opp_type = "competition"
    elif 'research' in body.lower():
        opp_type = "research"
    elif any(w in body.lower() for w in ['job', 'position', 'engineer', 'developer']):
        opp_type = "job"
    elif any(w in body.lower() for w in ['event', 'workshop', 'seminar']):
        opp_type = "event"
    else:
        opp_type = "other"
    
    # Determine location
    location = "other"
    body_lower = body.lower()
    if 'remote' in body_lower or 'work from home' in body_lower:
        location = "remote"
    elif 'lahore' in body_lower:
        location = "lahore"
    elif 'islamabad' in body_lower:
        location = "islamabad"
    elif 'karachi' in body_lower:
        location = "karachi"
    elif 'international' in body_lower or 'usa' in body_lower or 'uk' in body_lower or 'germany' in body_lower:
        location = "international"
    
    # Extract duration
    duration_match = re.search(r'(\d+)\s*(?:week|month|year)s?', body, re.IGNORECASE)
    duration = duration_match.group(0) if duration_match else None
    
    return {
        "title": subject[:80] if subject else "Opportunity",
        "type": opp_type,
        "organization": email.get('sender', '').split('@')[-1].split('.')[0].title(),
        "deadline": None,  # Would need full date parsing
        "deadline_display": deadline_display,
        "min_cgpa": min_cgpa,
        "required_skills": [],
        "required_documents": [],
        "stipend_pkr": stipend_pkr,
        "location": location,
        "apply_link": apply_link,
        "duration": duration,
        "summary": (body[:150] + "...") if body else "Opportunity details"
    }


def generate_reasoning(opportunity: Dict[str, Any], profile: Dict[str, Any], rank: int = 1) -> Dict[str, Any]:
    """
    Generate personalized reasoning for ONE opportunity vs student profile.
    Call only for ranks 1-8 to conserve API calls.
    
    Args:
        opportunity: Extracted opportunity dict (with scores, days_left computed)
        profile: Student profile dict (degree, semester, cgpa, skills, preferred_types, location_pref, financial_need)
        rank: Rank number (1-8 triggers API call, 9+ returns quick fallback)
    
    Returns:
        Dict with keys:
        {
            "why_it_matters": str,
            "next_steps": [str],
            "urgency_label": str (emoji),
            "action_deadline": str
        }
    """
    from scoring import get_urgency_label
    
    days_left = opportunity.get('days_left')
    urgency_label = get_urgency_label(days_left)
    
    # For ranks 9+, return quick fallback without API call (cost optimization)
    if rank > 8:
        return {
            "why_it_matters": opportunity.get('summary', 'This opportunity matches your profile.'),
            "next_steps": [
                f"Visit the application link: {opportunity.get('apply_link', 'check email')}",
                "Prepare your CV and required documents",
                "Verify your eligibility before applying"
            ],
            "urgency_label": urgency_label,
            "action_deadline": f"Apply by {opportunity.get('deadline_display', 'the deadline')}"
        }
    
    if not client:
        # No API available, use fallback
        user_skills = set(s.lower() for s in profile.get('skills', []))
        req_skills = set(s.lower() for s in opportunity.get('required_skills', []))
        matched = list(user_skills & req_skills)[:3]
        
        return {
            "why_it_matters": f"This {opportunity.get('type', 'opportunity')} at {opportunity.get('organization', 'this organization')} aligns with your {profile.get('degree', 'background')} and skills in {', '.join(matched) if matched else 'your field'}.",
            "next_steps": [
                f"Apply at: {opportunity.get('apply_link', 'see email')}",
                "Prepare CV, transcript, and required documents",
                f"Submit before {opportunity.get('deadline_display', 'the deadline')}"
            ],
            "urgency_label": urgency_label,
            "action_deadline": f"Deadline: {opportunity.get('deadline_display', 'Check email')}"
        }
    
    try:
        # Build skills gap analysis
        user_skills = set(s.lower() for s in profile.get('skills', []))
        req_skills = set(s.lower() for s in opportunity.get('required_skills', []))
        matched = user_skills & req_skills
        missing = req_skills - user_skills
        
        stipend_text = ""
        if opportunity.get('stipend_pkr'):
            stipend_text = f"\n- Stipend: PKR {opportunity['stipend_pkr']:,}"
        
        prompt = f"""You are a career advisor helping a Pakistani university student prioritize opportunities.

STUDENT PROFILE:
- Degree: {profile.get('degree', 'Unknown')}
- Semester: {profile.get('semester', 'Unknown')} of 8
- CGPA: {profile.get('cgpa', 'Unknown')}
- Skills: {', '.join(profile.get('skills', [])) if profile.get('skills') else 'Not specified'}
- Looking for: {', '.join(profile.get('preferred_types', [])) if profile.get('preferred_types') else 'Any opportunity'}
- Location preference: {profile.get('location_pref', 'Any')}
- Financial need: {'Yes' if profile.get('financial_need') else 'No'}
- Experience: {profile.get('experience_years', 0)} years

OPPORTUNITY (Ranked #{rank}):
- Title: {opportunity.get('title', 'Unknown')}
- Organization: {opportunity.get('organization', 'Unknown')}
- Type: {opportunity.get('type', 'Unknown')}
- Location: {opportunity.get('location', 'Unknown')}
- Min CGPA: {opportunity.get('min_cgpa', 'Not specified')}{stipend_text}
- Deadline: {opportunity.get('deadline_display', 'Rolling')}
- Days left: {days_left if days_left is not None else 'Unknown'}
- Duration: {opportunity.get('duration', 'Not specified')}
- Skills matched: {', '.join(matched) if matched else 'None listed'}
- Skills gap: {', '.join(missing) if missing else 'Fully qualified'}
- Score: {opportunity.get('scores', {}).get('total', 0):.1f}/100

Generate a JSON response with exactly these keys:
{{
  "why_it_matters": "2 sentences. Mention student degree, specific matched skills, and concrete benefit. If financial_need=true and stipend exists, mention it.",
  "next_steps": [
    "Step 1: specific action (Start with verb: Download, Prepare, Submit, Email, etc.)",
    "Step 2: specific action with document/task detail",
    "Step 3: specific action with submission/follow-up context"
  ],
  "urgency_label": "emoji label (do not use, will be overridden)",
  "action_deadline": "one sentence: student must do X by deadline Y"
}}

Rules:
- why_it_matters must mention actual skills, degree level, and concrete value
- next_steps must be 3 items, each starting with actionable verb
- If no skills required, mention general fit (degree, semester, CGPA)
- Return ONLY valid JSON, no markdown, no code fences"""

        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result['urgency_label'] = urgency_label  # always override from code
        return result
    
    except Exception as e:
        print(f"Error in generate_reasoning (API): {e}")
        # Fall back to simplified reasoning
        user_skills = set(s.lower() for s in profile.get('skills', []))
        req_skills = set(s.lower() for s in opportunity.get('required_skills', []))
        matched = list(user_skills & req_skills)[:3]
        
        return {
            "why_it_matters": f"This {opportunity.get('type', 'opportunity')} at {opportunity.get('organization', 'this organization')} aligns with your {profile.get('degree', 'background')} and skills in {', '.join(matched) if matched else 'your field'}.",
            "next_steps": [
                f"Visit: {opportunity.get('apply_link', 'application link')}",
                "Prepare CV, transcript, and required documents",
                f"Submit before {opportunity.get('deadline_display', 'the deadline')}"
            ],
            "urgency_label": urgency_label,
            "action_deadline": f"Deadline: {opportunity.get('deadline_display', 'Check email')}"
        }


def run_full_pipeline(emails: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Master pipeline function — orchestrates all steps in sequence.
    Call this from app.py with user's emails + profile.
    
    Pipeline steps:
      1. Classify emails → opportunity / admin / spam
      2. Build RAG index for user's opportunity batch only
      3. Detect duplicates within user batch (TF-IDF similarity)
      4. Extract structured fields from each opportunity
      5. Score & rank each vs student profile
      6. Generate personalized reasoning for top 8
    
    Args:
        emails: List of email dicts (user's own emails, not demo data)
        profile: Student profile dict (degree, semester, cgpa, skills, etc.)
    
    Returns:
        List of ranked opportunity dicts with full context:
        [
            {
                "rank": int,
                "email_id": int,
                "title": str,
                "type": str,
                "organization": str,
                "deadline_display": str,
                "apply_link": str,
                "days_left": int or None,
                "is_duplicate": bool,
                "scores": {
                    "profile_fit": float,
                    "urgency": float,
                    "completeness": float,
                    "total": float
                },
                "reasoning": {
                    "why_it_matters": str,
                    "next_steps": [str],
                    "urgency_label": str,
                    "action_deadline": str
                },
                "location": str,
                "stipend_pkr": int or None,
                "required_skills": [str],
                "required_documents": [str],
                "summary": str
            },
            ...
        ]
    """
    from scoring import rank_opportunities
    from rag_engine import RAGEngine
    
    print(f"[Pipeline] Processing {len(emails)} emails for {profile.get('degree', 'student')}...")
    
    # Step 1: Classify
    print("[1/6] Classifying emails...")
    classified = classify_emails(emails)
    opportunities = [e for e in classified if e.get('label') == 'opportunity']
    print(f"  ✓ Found {len(opportunities)} opportunities")
    
    if not opportunities:
        print("  ⚠️ No opportunities found, returning empty list")
        return []
    
    # Step 2-3: Build RAG and detect duplicates within user batch
    print("[2/6] Building RAG index and detecting duplicates...")
    rag = RAGEngine()
    rag.build_index(opportunities)
    dup_ids = rag.get_duplicate_ids(threshold=0.70)
    print(f"  ✓ Detected {len(dup_ids)} duplicates")
    
    # Step 4: Extract structured fields
    print("[3/6] Extracting structured opportunity data...")
    extracted = []
    for i, email in enumerate(opportunities):
        ext = extract_opportunity(email)
        ext['email_id'] = email.get('id', i)
        ext['is_duplicate'] = (i in dup_ids)
        ext['source_email'] = email
        extracted.append(ext)
    print(f"  ✓ Extracted {len(extracted)} opportunities")
    
    # Step 5: Score and rank vs profile
    print("[4/6] Scoring and ranking opportunities...")
    ranked = rank_opportunities(extracted, profile)
    print(f"  ✓ Ranked {len(ranked)} opportunities")
    
    # Step 6: Generate reasoning for top 8
    print("[5/6] Generating personalized reasoning (top 8 only)...")
    for item in ranked:
        item['reasoning'] = generate_reasoning(item, profile, item.get('rank', 1))
    print("  ✓ Reasoning generated")
    
    print(f"[6/6] Pipeline complete! Top opportunity: {ranked[0].get('title', 'N/A')} ({ranked[0].get('scores', {}).get('total', 0):.0f}/100)")
    
    return ranked
