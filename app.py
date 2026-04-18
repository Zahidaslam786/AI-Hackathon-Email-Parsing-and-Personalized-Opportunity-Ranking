import streamlit as st
import json
import os
from pathlib import Path
from datetime import date
from pipeline import classify_emails, extract_opportunity, generate_reasoning, run_full_pipeline
from rag_engine import RAGEngine
from scoring import rank_opportunities, get_urgency_label, get_summary_stats, get_fit_breakdown, get_score_color, get_recommendation

# Page configuration
st.set_page_config(
    page_title="Opportunity Inbox Copilot",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📧 Opportunity Inbox Copilot")
st.markdown("_AI-powered email parsing and personalized opportunity ranking for SOFTEC 2026_")

# Initialize session state
if 'emails' not in st.session_state:
    emails_path = Path(__file__).parent / "emails_dataset_v2.json"
    with open(emails_path, 'r', encoding='utf-8') as f:
        st.session_state['emails'] = json.load(f)

if 'run' not in st.session_state:
    st.session_state['run'] = False

if 'student_profile' not in st.session_state:
    st.session_state['student_profile'] = None

if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None

if 'classified' not in st.session_state:
    st.session_state['classified'] = None

if 'extracted' not in st.session_state:
    st.session_state['extracted'] = None

if 'ranked' not in st.session_state:
    st.session_state['ranked'] = None

if 'stats' not in st.session_state:
    st.session_state['stats'] = None

if 'duplicate_ids' not in st.session_state:
    st.session_state['duplicate_ids'] = set()

if 'user_emails' not in st.session_state:
    st.session_state['user_emails'] = None

if 'analyzed' not in st.session_state:
    st.session_state['analyzed'] = False

# ============================================================================
# SIDEBAR: Student Profile Form
# ============================================================================
st.sidebar.header("👤 Student Profile")
st.sidebar.markdown("---")

degree = st.sidebar.selectbox(
    "Degree Program",
    ["BS Computer Science", "BS AI", "BS Software Engineering", "BS Data Science", "BS EE", "MS Computer Science", "MS AI", "Other"],
    key="degree"
)

semester = st.sidebar.slider(
    "Current Semester",
    min_value=1,
    max_value=8,
    value=5,
    key="semester"
)

cgpa = st.sidebar.number_input(
    "CGPA (out of 4.0)",
    min_value=0.0,
    max_value=4.0,
    value=3.2,
    step=0.1,
    key="cgpa"
)

skills = st.sidebar.multiselect(
    "Technical Skills & Interests",
    ["Python", "C++", "Java", "JavaScript", "SQL", "ML", "NLP", "Computer Vision", 
     "LLMs", "PyTorch", "TensorFlow", "Web Development", "Mobile Development", 
     "Cloud Computing", "DevOps", "Data Analysis"],
    default=["Python", "ML", "NLP", "LLMs"],
    key="skills"
)

preferred_types = st.sidebar.multiselect(
    "Preferred Opportunity Types",
    ["Internship", "Scholarship", "Fellowship", "Research", "Competition", "Hackathon", "Grant"],
    default=["Internship", "Research", "Fellowship"],
    key="preferred_types"
)

financial_need = st.sidebar.checkbox(
    "🤑 Financial support needed",
    value=False,
    key="financial_need"
)

location_pref = st.sidebar.selectbox(
    "Location Preference",
    ["Any", "Lahore", "Karachi", "Islamabad", "Remote", "International"],
    key="location_pref"
)

experience_years = st.sidebar.slider(
    "Years of Relevant Experience",
    min_value=0,
    max_value=5,
    value=1,
    key="experience_years"
)

st.sidebar.markdown("---")

# Collect profile into dict
student_profile = {
    "degree": degree,
    "semester": semester,
    "cgpa": cgpa,
    "skills": skills,
    "preferred_types": preferred_types,
    "financial_need": financial_need,
    "location_pref": location_pref,
    "experience_years": experience_years
}

# Store in session state
st.session_state['student_profile'] = student_profile

# Analyze button
if st.sidebar.button("� Analyze My Inbox", use_container_width=True, type="primary"):
    st.session_state['run'] = True
    
    # Determine which emails to analyze
    emails_to_analyze = st.session_state.get('user_emails') or st.session_state['emails']
    dataset_source = "Your uploaded emails" if st.session_state.get('user_emails') else "35 demo emails"
    
    with st.spinner(f"🚀 Running AI pipeline on {dataset_source}..."):
        ranked = run_full_pipeline(emails_to_analyze, student_profile)
        st.session_state['ranked'] = ranked
        st.session_state['analyzed'] = True
        st.sidebar.success(f"✅ Analysis complete! {len(ranked)} opportunities ranked")


st.sidebar.markdown("---")
dataset_info = "Your emails" if st.session_state.get('user_emails') else "35 demo emails (default)"
st.sidebar.markdown(f"**Dataset:** {dataset_info}")

# ============================================================================
# MAIN CONTENT AREA: Tabs
# ============================================================================
if not st.session_state['analyzed']:
    st.info("👈 Fill your profile on the left, then click **Analyze My Inbox** to get started!")
    st.markdown("### ✨ Quick Start")
    st.markdown("""
    1. **Fill your profile** in the sidebar (degree, skills, preferences, etc.)
    2. Click **Analyze My Inbox** to run the AI pipeline
    3. View results in the **🏆 Ranked Opportunities** tab
    4. Or test with your own emails in the **🧪 Test New Emails** tab
    """)
else:
    tab_rank, tab_test, tab_filtered, tab_raw = st.tabs([
        "🏆 Ranked Opportunities", 
        "🧪 Test New Emails", 
        "🗑️ Filtered Out",
        "📬 Raw Inbox"
    ])
    
    # ========================================================================
    # TAB: Ranked Opportunities (PART B)
    # ========================================================================
    with tab_rank:
        if st.session_state.get('analyzed') and st.session_state['ranked']:
            ranked = st.session_state['ranked']
            stats = get_summary_stats(ranked)
            
            # Metrics row (5 columns)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📧 Analyzed", len(ranked))
            c2.metric("⚡ Urgent", stats['urgent'])
            c3.metric("🏆 Top Score", f"{stats['top_score']:.0f}/100")
            c4.metric("🔗 With Links", stats['has_link'])
            c5.metric("📋 Duplicates", sum(1 for r in ranked if r.get('is_duplicate')))
            
            st.divider()
            
            # Filter controls
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                type_filter = st.multiselect(
                    "Filter by type",
                    ["internship", "scholarship", "fellowship", "competition", "research", "job", "event"],
                    default=[],
                    key="type_filter"
                )
            with col_f2:
                hide_dups = st.checkbox("Hide duplicates", value=False, key="hide_dups")
            
            # Apply filters
            display = ranked
            if type_filter:
                display = [r for r in display if r.get('type') in type_filter]
            if hide_dups:
                display = [r for r in display if not r.get('is_duplicate')]
            
            st.markdown(f"**Showing {len(display)} of {len(ranked)} opportunities**")
            st.divider()
            
            # Ranked opportunity cards (PART B)
            for item in display:
                rank = item.get('rank', '?')
                scores = item.get('scores', {})
                reasoning = item.get('reasoning', {})
                urgency_label = reasoning.get('urgency_label', '')
                
                with st.container(border=True):
                    # Header row
                    h_col1, h_col2 = st.columns([4, 1])
                    h_col1.markdown(f"### #{rank} {item.get('title', 'Untitled')[:70]}")
                    h_col2.markdown(f"**{urgency_label}**")
                    
                    # Info row (4 columns)
                    i1, i2, i3, i4 = st.columns(4)
                    i1.write(f"🏢 {item.get('organization', 'Unknown')[:40]}")
                    i2.write(f"📅 {item.get('deadline_display') or '🔵 Rolling'}")
                    if item.get('stipend_pkr'):
                        i3.write(f"💰 PKR {item['stipend_pkr']:,}")
                    else:
                        i3.write(f"💰 N/A")
                    i4.write(f"📍 {item.get('location', '').title()}")
                    
                    # Duplicate warning
                    if item.get('is_duplicate'):
                        st.warning("⚠️ This email is very similar to another in your batch — possible duplicate")
                    
                    st.divider()
                    
                    # Why it matters
                    if reasoning.get('why_it_matters'):
                        st.success(f"💡 {reasoning['why_it_matters']}")
                    
                    # Action deadline
                    if reasoning.get('action_deadline'):
                        st.markdown(f"**⏰ {reasoning['action_deadline']}**")
                    
                    # Action checklist
                    steps = reasoning.get('next_steps', [])
                    if steps:
                        st.markdown("**✅ Action Checklist:**")
                        for s in steps:
                            st.markdown(f"- {s}")
                    
                    st.divider()
                    
                    # Apply button + Score breakdown
                    b_col1, b_col2 = st.columns([3, 2])
                    with b_col1:
                        if item.get('apply_link'):
                            st.link_button("🚀 Apply Now →", item['apply_link'], use_container_width=True)
                        else:
                            st.warning("❌ No application link found")
                    
                    with b_col2:
                        with st.expander("📊 Score breakdown"):
                            st.progress(scores.get('profile_fit', 0) / 40,
                                text=f"Profile Fit: {scores.get('profile_fit', 0):.0f}/40")
                            st.progress(scores.get('urgency', 0) / 35,
                                text=f"Urgency: {scores.get('urgency', 0):.0f}/35")
                            st.progress(scores.get('completeness', 0) / 25,
                                text=f"Completeness: {scores.get('completeness', 0):.0f}/25")
                            st.divider()
                            total_score = scores.get('total', 0)
                            st.progress(min(total_score / 100, 1.0),
                                text=f"**Total: {total_score:.1f}/100**")
        else:
            st.info("👈 Click **Analyze My Inbox** to rank opportunities")
    
    # ========================================================================
    # TAB: Test New Emails (PART C)
    # ========================================================================
    with tab_test:
        st.subheader("🧪 Paste or upload your own emails")
        st.caption("These will be analyzed against your profile — not compared to any database")
        
        input_mode = st.radio("Input method", ["📋 Paste manually", "📁 Upload JSON"], horizontal=True)
        
        if input_mode == "📋 Paste manually":
            with st.form("email_form"):
                subject = st.text_input("Email Subject")
                sender = st.text_input("Sender Email")
                body = st.text_area(
                    "Email Body",
                    height=250,
                    placeholder="Paste the full email body here..."
                )
                if st.form_submit_button("➕ Add Email"):
                    if subject and body:
                        new_email = {
                            "id": 200 + len(st.session_state.get('user_emails', [])),
                            "source": "User Input",
                            "subject": subject,
                            "sender": sender or "unknown@example.com",
                            "date": str(date.today()),
                            "body": body
                        }
                        if st.session_state['user_emails'] is None:
                            st.session_state['user_emails'] = []
                        st.session_state['user_emails'].append(new_email)
                        st.success(f"✅ Added: {subject[:50]}")
                    else:
                        st.error("Subject and body are required")
        
        elif input_mode == "📁 Upload JSON":
            uploaded = st.file_uploader("Upload emails JSON", type=['json'])
            if uploaded:
                try:
                    new_emails = json.load(uploaded)
                    st.session_state['user_emails'] = new_emails
                    st.success(f"✅ Loaded {len(new_emails)} emails from file")
                except Exception as e:
                    st.error(f"Error loading JSON: {e}")
        
        # Show added emails
        user_emails = st.session_state.get('user_emails', [])
        if user_emails:
            st.markdown(f"**{len(user_emails)} email(s) ready for analysis:**")
            for i, e in enumerate(user_emails):
                col_e, col_d = st.columns([5, 1])
                col_e.write(f"📧 {e.get('subject', 'No subject')[:70]}")
                if col_d.button("❌", key=f"del_{i}"):
                    st.session_state['user_emails'].pop(i)
                    st.rerun()
            
            if st.button("🔍 Analyze These Emails", type="primary", use_container_width=True):
                with st.spinner("🚀 Analyzing your emails against your profile..."):
                    ranked = run_full_pipeline(user_emails, student_profile)
                    st.session_state['ranked'] = ranked
                    st.session_state['analyzed'] = True
                    st.success("✅ Done! Check the '🏆 Ranked Opportunities' tab")
                    st.rerun()
        else:
            st.info("📝 Add emails above, then click **Analyze These Emails**")
    
    # ========================================================================
    # TAB: Filtered Out (PART D)
    # ========================================================================
    with tab_filtered:
        st.subheader("🗑️ Spam & Administrative Notices")
        
        # Get all classified emails by running classifier on the analyzed set
        emails_to_classify = st.session_state.get('user_emails') or st.session_state['emails']
        classified = classify_emails(emails_to_classify)
        
        spam_emails = [e for e in classified if e.get('label') == 'spam']
        admin_emails = [e for e in classified if e.get('label') == 'admin']
        
        if spam_emails or admin_emails:
            col1, col2 = st.columns(2)
            col1.metric("🚫 Spam", len(spam_emails))
            col2.metric("📋 Admin/Non-Career", len(admin_emails))
            
            st.divider()
            
            if spam_emails:
                st.error(f"🚫 {len(spam_emails)} spam emails detected — **DO NOT** click any links")
                for e in spam_emails:
                    with st.expander(f"⚠️ {e.get('subject', 'No subject')[:60]}"):
                        st.write(f"**From:** {e.get('sender', 'Unknown')}")
                        st.write(f"**Date:** {e.get('date', 'Unknown')}")
                        st.error("This email has been identified as **spam or phishing**. Do not click links or provide personal information.")
                        with st.expander("View email content"):
                            st.write(e.get('body', 'No content'))
            
            if admin_emails:
                st.info(f"📋 {len(admin_emails)} administrative/general emails")
                for e in admin_emails:
                    with st.expander(f"📌 {e.get('subject', 'No subject')[:60]}"):
                        st.write(f"**From:** {e.get('sender', 'Unknown')}")
                        st.write(f"**Date:** {e.get('date', 'Unknown')}")
                        st.write(e.get('body', 'No content')[:300] + "...")
        else:
            st.success("✅ No spam or administrative emails detected!")
    
    # ========================================================================
    # TAB: Raw Inbox
    # ========================================================================
    with tab_raw:
        st.subheader("📬 All Emails in Your Inbox")
        
        emails_to_show = st.session_state.get('user_emails') or st.session_state['emails']
        classified = classify_emails(emails_to_show)
        
        st.markdown(f"**Total emails:** {len(classified)}")
        
        for email in classified:
            label = email.get('label', 'unknown')
            
            if label == 'opportunity':
                badge = "🎯 Opportunity"
            elif label == 'admin':
                badge = "📋 Admin"
            else:
                badge = "🚫 Spam"
            
            with st.expander(f"{badge} | {email.get('subject', 'No subject')[:60]} (ID: {email.get('id', '?')})"):
                col1, col2 = st.columns([2, 2])
                with col1:
                    st.write(f"**From:** {email.get('sender', 'Unknown')}")
                    st.write(f"**Date:** {email.get('date', 'Unknown')}")
                    st.write(f"**Source:** {email.get('source', 'Unknown')}")
                with col2:
                    st.write(f"**Subject:** {email.get('subject', 'No subject')}")
                    st.write(f"**Label:** {badge}")
                st.divider()
                st.write(email.get('body', 'No content'))

# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    🎓 <b>SOFTEC 2026 AI Hackathon</b> | Opportunity Inbox Copilot MVP<br>
    Built with Streamlit + Claude API
    </div>
    """,
    unsafe_allow_html=True
)
