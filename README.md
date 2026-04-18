# 🎯 Opportunity Inbox Copilot

**AI-powered Email Parsing & Personalized Opportunity Ranking for SOFTEC 2026**

An intelligent system that scans university student emails, extracts critical opportunity data, and ranks them based on academic profile, technical skills, and interests.

---

## 🚀 Overview

University students are overwhelmed by opportunity emails—internships, scholarships, fellowships, competitions, and research programs flood their inboxes. **Opportunity Inbox Copilot** is an AI agent that:

✅ **Classifies emails** into opportunity/spam/admin categories  
✅ **Extracts structured data** (deadlines, eligibility, stipends, apply links)  
✅ **Detects duplicates** using TF-IDF similarity within your email batch  
✅ **Scores & ranks** each opportunity against your unique profile  
✅ **Generates personalized reasoning** with actionable next steps  
✅ **Filters intelligently** by type, deadline urgency, and financial impact  

---

## ✨ Key Features

### 🤖 Agentic Parsing
- Uses Claude API (Anthropic) to extract structured JSON from messy email text
- Graceful fallback to rule-based extraction (regex) when API unavailable
- Handles diverse email formats (forwarded, quoted, poorly formatted)

### 👤 Dynamic Personalization
- **Student Profile:** Degree, semester, CGPA, skills, preferred opportunity types, location preference
- **Profile-Based Ranking:** Matches each opportunity against student's unique background
- **Personalized Reasoning:** Claude generates "why this opportunity matters for YOU" with specific evidence
- **Specially tuned for:** Final-year students (8th semester) interested in **NLP & Agentic AI**

### 📊 Deterministic Scoring Engine
```
Total Score = (Profile Fit × 40%) + (Urgency × 35%) + (Completeness × 25%)

Profile Fit (0-40):
  • Type match: +15 (matches preferred types)
  • CGPA eligible: +10 (meets minimum GPA)
  • Skill overlap: +10 (skills match required)
  • Location: +5 (location preference)

Urgency (0-35):
  • 0-3 days: 35 pts (🔴 Critical)
  • 4-7 days: 30 pts (🟡 This week)
  • 8-14 days: 25 pts (🟢 Upcoming)
  • 15-30 days: 18 pts (🔵 Later)
  • 30+ days: 5 pts (⚫ Rolling)

Completeness (0-25):
  • Apply link present: +10
  • Clear deadline: +8
  • Required documents listed: +4
  • Stipend/financial value: +3
```

### 🎯 Actionable Dashboards
- **Ranked Opportunities Tab:** Color-coded cards with all critical info
- **Action Checklist:** 3 specific next steps for each top opportunity
- **Score Breakdown:** Visual progress bars showing fit/urgency/completeness
- **Filter Controls:** By opportunity type, hide duplicates, urgent-only view
- **Direct Apply Links:** One-click to application portals

### 🧪 Test New Emails
- **Paste manually:** Add individual emails with subject, sender, body
- **Upload JSON:** Batch upload pre-formatted email files
- **Isolated analysis:** Your emails vs profile only (no comparison to 35 base emails)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit (Python web framework) |
| **LLM Brain** | Anthropic Claude API (claude-sonnet-4-20250514) |
| **Classification** | Keyword-based (demo mode) / Claude API |
| **Extraction** | Claude API / Regex patterns (fallback) |
| **Duplicate Detection** | TF-IDF + Cosine Similarity (pure Python, no sklearn) |
| **Scoring** | Deterministic logic (no ML model) |
| **Data** | JSON-based (no database) |
| **Deployment Ready** | Hugging Face Spaces / Streamlit Cloud |

---

## 📸 Screenshot

![Opportunity Inbox Copilot - Ranked View](./screenshot.png)

**Application Interface:**
- **Left Sidebar:** Student profile form with 8 input fields (degree, semester, CGPA, skills, preferences, location, experience)
- **Top Metrics:** Dashboard showing total analyzed, urgent count, top score, apply links available, duplicate count
- **Filter Controls:** Multi-select for opportunity type, checkbox to hide duplicates
- **Ranked Opportunity Card:** Shows:
  - Rank badge and opportunity title
  - Urgency emoji (🔵 = rolling deadline)
  - Organization, deadline, stipend, location
  - **💡 Why it matches:** AI-generated personalized fit explanation
  - **⏰ Deadline:** Specific action deadline reminder
  - **✅ Action Checklist:** 3 concrete next steps with links
  - **🚀 Apply Now:** Direct button to application portal
  - **📊 Score Breakdown:** Expandable detailed component scores (fit/urgency/completeness)

---

## 🚀 Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone https://github.com/Zahidaslam786/AI-Hackathon-Email-Parsing-and-Personalized-Opportunity-Ranking.git
cd "AI Hackaton"

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### 2. **Access the App**

```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### 3. **Fill Student Profile**

In the left sidebar, provide:
- 📚 **Degree Program** (BS CS, BS AI, MS CS, etc.)
- 📅 **Current Semester** (1-8)
- 📊 **CGPA** (0.0 - 4.0)
- 💻 **Technical Skills** (Python, ML, NLP, etc.)
- 🎯 **Preferred Types** (Internship, Scholarship, Fellowship, etc.)
- 💰 **Financial Need** (checkbox)
- 📍 **Location Preference** (Lahore, Remote, International, etc.)
- 📈 **Years of Experience** (0-5)

### 4. **Analyze Your Emails**

**Option A: Demo Mode (35 sample emails)**
- Click **"🔍 Analyze My Inbox"** button
- Wait 10-15 seconds
- View results in **"🏆 Ranked Opportunities"** tab

**Option B: Your Own Emails**
- Go to **"🧪 Test New Emails"** tab
- Paste emails manually OR upload JSON file
- Click **"🔍 Analyze These Emails"**

### 5. **Act on Results**

For each ranked opportunity:
1. Read **"Why it matches"** personalized explanation
2. Follow **"Action Checklist"** steps
3. Click **"🚀 Apply Now"** to go directly to application

---

## 📁 Project Structure

```
AI-Hackathon-Email-Parsing-and-Personalized-Opportunity-Ranking/
│
├── app.py                      # Main Streamlit UI
├── pipeline.py                 # LLM calls (classification, extraction, reasoning)
├── scoring.py                  # Deterministic scoring & ranking logic
├── rag_engine.py               # TF-IDF duplicate detection (pure Python)
├── emails_dataset_v2.json      # 35 sample demo emails
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
└── .git/                       # Git repository
```

---

## 📋 Dependencies

```
streamlit==1.56.0
anthropic==0.96.0
python-dotenv==1.1.0
numpy==2.2.6
```

**Optional (for enhanced duplicate detection):**
```
scikit-learn>=1.3.0
scipy>=1.8.0
```

*Note: The app works without scikit-learn using pure Python TF-IDF.*

---

## 🔑 API Configuration

### Using Claude API (Optional - Enhanced Mode)

1. **Get API Key:** https://console.anthropic.com/
2. **Set Environment Variable:**

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

3. **Restart the app** to enable API mode

### Demo Mode (No API Key)

The app works fully without an API key using:
- **Classification:** Keyword-based fallback
- **Extraction:** Regex patterns
- **Reasoning:** Rule-based templates

This is perfect for testing locally!

---

## 🧪 Testing Guide

### Test 1: Demo Run (35 Sample Emails)

1. Fill profile in sidebar (default values are fine)
2. Click **"🔍 Analyze My Inbox"**
3. Wait ~15 seconds
4. View results in **"🏆 Ranked Opportunities"** tab
5. Try filters: by type, hide duplicates
6. Expand score breakdown to see component scores

### Test 2: Your Own Emails

1. Go to **"🧪 Test New Emails"** tab
2. Paste 2-3 real opportunity emails
3. Click **"🔍 Analyze These Emails"**
4. See how your profile matches YOUR actual opportunities

### Test 3: Spam Detection

1. Check **"🗑️ Filtered Out"** tab
2. See 3-4 spam emails correctly classified
3. Review admin/general notices

### Test 4: With Claude API

1. Set ANTHROPIC_API_KEY environment variable
2. Restart app
3. Analyze emails again
4. Compare reasoning quality with demo mode

---

## 📊 Sample Output

### Ranked Opportunity Card

```
#1 LUMS NLP Research Lab - Summer Research Fellowship 2026 | 🔵 Rolling deadline

🏢 LUMS          📅 26 for      💰 PKR 40,000     📍 Other

💡 Why it matches your profile:
"This fellowship at LUMS aligns with your BS Computer Science background 
and strong interests in NLP. Your CGPA meets requirements, and the research 
focus on Agentic AI matches your stated interests perfectly."

⏰ Deadline:
"Rolling deadline — apply at your earliest convenience"

✅ Action Checklist:
• Apply at: https://lums.edu.pk/opportunities/nlp
• Prepare CV, transcript, and any research portfolio samples
• Submit before deadline via link above

🚀 Apply Now →    📊 Score breakdown ↓
                   Profile Fit: 35/40
                   Urgency: 35/35
                   Completeness: 24/25
                   ─────────────────
                   Total: 94.0/100
```

---

## 🎯 Model Behavior

### Classification Logic (Demo Mode)

| Category | Triggers |
|----------|----------|
| **Opportunity** | Default (if not spam/admin) |
| **Spam** | FREE, PRIZE, CLAIM, WINNER, SUSPENDED, verify account, etc. |
| **Admin** | PHOTO, PIZZA, SOCIAL, ALUMNI, NETWORKING, EVENT, etc. |

### Extraction (Fallback Regex)

Automatically parses:
- **Deadline:** Dates in "April 30, 2026" format
- **CGPA:** Minimum GPA requirements (e.g., "min 3.0 CGPA")
- **Stipend:** PKR amounts; USD converted at 280 PKR/USD
- **Type:** Internship, scholarship, fellowship, hackathon, research, job, event
- **Location:** Lahore, Islamabad, Karachi, Remote, International
- **Apply Link:** HTTP/HTTPS URLs
- **Skills:** Python, C++, ML, NLP, etc.

### Scoring Rules

- **Duplicate Penalty:** 0.70× multiplier for near-duplicates
- **Expired Deadline:** 0 points for urgency
- **No Apply Link:** Reduces completeness but still rankable
- **No Deadline:** 8 points for urgency (rolling)

---

## 🚨 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'sklearn'`

**Solution:** The app uses pure Python TF-IDF and works without scikit-learn.
If you want to install it anyway (requires disk space):

```bash
pip install scikit-learn scipy
```

### Issue: App very slow

**Causes:**
- Claude API calls (10-20 sec for 35 emails due to rate limits)
- TF-IDF vectorization on large batches

**Solution:**
- Use demo mode for quick testing
- Reduce email batch size for custom uploads

### Issue: "ANTHROPIC_API_KEY not set" warning

**Solution:** This is normal. The app works fine without it in demo mode.
Set the env var if you want Claude API enhanced features.

---

## 📈 Performance Metrics

| Operation | Time (Demo Mode) |
|-----------|-----------------|
| Load app | <2 seconds |
| Classify 35 emails | ~2 seconds |
| Detect duplicates | <1 second |
| Extract 28 opportunities | ~3 seconds |
| Score & rank | <1 second |
| Generate reasoning (top 8) | ~8 seconds (fallback) |
| **Total pipeline** | ~15 seconds |

*With Claude API: Add 20-30 seconds for API calls*

---

## 👨‍💻 Team

| Role | Name | Institute |
|------|------|-----------|
| **Lead** | Muhammad Zahid Aslam | BSCS, FAST-NUCES (8th Semester) |
| **Member** | Asjal Atta | FAST-NUCES |
| **Member** | Muhammad Abdullah | FAST-NUCES |

---

## 🎓 SOFTEC 2026 Details

- **Hackathon:** SOFTEC 2026 AI Hackathon
- **Challenge:** "AI-powered Email Parsing and Personalized Opportunity Ranking"
- **Category:** AI/ML Applications
- **Focus:** LLMs, Agentic Systems, Real-world Problem Solving

---

## 📜 License

This project is open source and available for educational use.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
- 📧 Email: contact@softec2026.com
- 🐙 GitHub Issues: [Create an issue](https://github.com/Zahidaslam786/AI-Hackathon-Email-Parsing-and-Personalized-Opportunity-Ranking/issues)
- 💬 Discussions: [Start a discussion](https://github.com/Zahidaslam786/AI-Hackathon-Email-Parsing-and-Personalized-Opportunity-Ranking/discussions)

---

## 🎉 Acknowledgments

- **Anthropic** for Claude API
- **Streamlit** for the web framework
- **SOFTEC 2026** for the opportunity
- **FAST-NUCES** and all mentors who guided this project

---

## 📝 Changelog

### v1.0.0 (April 18, 2026)
- ✅ Initial MVP release
- ✅ Classification, extraction, ranking working
- ✅ Pure Python RAG (no external ML dependencies)
- ✅ Personalized reasoning generation
- ✅ Test new emails feature
- ✅ GitHub integration

---

**Built with ❤️ for students overwhelmed by opportunity emails**

🚀 **Start using it now:** `streamlit run app.py`