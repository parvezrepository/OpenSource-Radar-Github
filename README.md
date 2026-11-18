# 📡 OpenSource Radar

> **AI-Powered Tech Intelligence & Content Discovery Platform**  
> Scout, analyze, score, and transform emerging open-source GitHub repositories into structured research dossiers and multi-platform content.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit%201.35%2B-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-SQLite%20WAL%20%2B%20SQLAlchemy-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 💡 What is OpenSource Radar?

**OpenSource Radar** is a 100% Python-based intelligence engine designed for tech creators, developers, researchers, and investors. Instead of manually sifting through GitHub, OpenSource Radar continuously scans the open-source ecosystem, tracks rising stars before they go viral, conducts deep static codebase inspections, and generates ready-to-publish educational content (YouTube scripts, viral Shorts, tech blogs) in English, Bengali, and Banglish.

---

## ⚙️ How It Works

The platform operates as a seamless 5-stage automated pipeline:

```
[1. GitHub REST API] ──► [2. Discovery & Telemetry] ──► [3. Zero-Code Inspection]
                                                                  │
[5. Multilingual Content Studio] ◄── [4. 5-Pillar Scoring] ◄──────┘
 (YouTube, Shorts, Blogs)              (0 - 100 Score)
```

1. **📡 Telemetry & Discovery**: Scans GitHub across 9 specialized modes (Trending, Fast Movers, Hidden Gems, AI Agents, Trading/FinTech, CyberSec, DevTools) and deduplicates in a local SQLite database.
2. **🔍 Zero-Code Static Inspection**: Safely inspects file trees, dependency manifests (`requirements.txt`, `package.json`, `Cargo.toml`), and README structures without ever executing untrusted code.
3. **📊 5-Pillar Opportunity Scoring**: Ranks repositories from 0 to 100 based on Star Velocity (25%), Architectural Quality (25%), Documentation Clarity (20%), Practical Utility (15%), and Content Appeal (15%).
4. **🤖 Dual AI Research Intelligence**: Leverages OpenAI, OpenRouter, or Google Gemini to generate structured technical dossiers with prompt-injection XML fences.
5. **💬 Interactive Codebase Q&A Chat**: Ask conversational questions about system design, Docker setup, and dependencies grounded strictly in verified repository data.
6. **📝 Content Studio**: Converts complex codebases into viral, educational content drafts with interactive in-dashboard editing and one-click Markdown/Text export.
7. **📱 Telegram Auto-Alerts**: Dispatches real-time cards to your Telegram channel when high-momentum or elite opportunity repositories are scouted.

---

## 📋 System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version `3.11` or higher (Tested on `3.11` and `3.12`)
- **Git**: Installed on your system
- **GitHub Account & Token**: Free GitHub Personal Access Token (PAT) for 5,000 requests/hour (unauthenticated rate limit is 60 req/hr)
- **(Optional) AI API Key**: OpenAI (`sk-...`), OpenRouter (`sk-or-v1-...`), or Google Gemini (`AIza...`) for AI dossiers and scripts

---

## 🚀 Quick Start (Installation Guide)

### Step 1: Clone the Repository
```bash
git clone https://github.com/parvezrepository/opensource-radar.git
cd opensource-radar
```

### Step 2: Set Up Virtual Environment & Dependencies

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**On macOS / Linux (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the template file `.env.example` to `.env`:

**Windows:**
```powershell
copy .env.example .env
```
**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your keys:
```ini
# GitHub Token (Required for 5,000 req/hr quota)
# Get a free token at: https://github.com/settings/tokens (classic, no special scopes needed)
GITHUB_TOKEN=github_pat_your_token_here

# AI Provider (Optional: openai or gemini. Works completely even without AI keys!)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-or-openrouter-key
OPENAI_MODEL=gpt-4o-mini

# Database (Defaults to local SQLite WAL database in data/ directory)
DATABASE_URL=sqlite:///data/opensource_radar.db
```

### Step 4: Launch the Dashboard!
```bash
streamlit run app.py
```
Open your browser and navigate to: **`http://localhost:8501`**

---

## 🖥️ Platform Modules Walkthrough

| # | Page | What It Does |
|---|---|---|
| **01** | **Overview** | System telemetry, discovered repos count, active jobs, and database health. |
| **02** | **Discover** | Multi-filter search engine across 500,000+ repos by stars, language, dates, and topics. |
| **03** | **Trending** | Daily and weekly fast-moving repositories with star momentum. |
| **04** | **Hidden Gems** | High-utility, under-the-radar repositories with low stars but rapid acceleration. |
| **05** | **AI & Agents** | Curated radar tracking autonomous agents, MCP servers, and LLM tooling. |
| **06** | **Trading & FinTech** | Algorithmic trading bots, quant finance frameworks, and backtesters. |
| **07** | **Repository Analyzer** | Static file-tree audit, dependency parsing, 0–100 scoring, AI Dossier, and interactive AI Q&A Chat. |
| **08** | **Compare** | Side-by-side matrix comparing 2 to 5 repositories with dependency overlap. |
| **09** | **Content Studio** | Generates video scripts, Shorts hooks, and tutorials in English, Bengali (`বাংলা`), and Banglish. |
| **10** | **Saved Projects** | Personal project bookmarks with custom research tags and notes. |
| **11** | **Analytics** | Historical star trajectories, velocity sparklines, and language distribution charts. |
| **12** | **Settings & Diagnostics**| Live GitHub API quota counter, database health check, AI testing, and Telegram bot diagnostics. |

---

## ⏱️ Running Background Automation (Optional)

To enable automatic scheduled scans and star snapshot recording every hour/day:
```bash
python scheduler.py
```
- Runs in the background independently of the Streamlit dashboard.
- Check scheduler status anytime: `python scheduler.py --status`
- Run an immediate single scan pass: `python scheduler.py --once`

---

## 🧪 Running Automated Tests

Run the full end-to-end test suite (all 70 unit and integration tests):
```bash
pytest
```

---

## 🔒 Security & Privacy Guarantees

- **Strict Zero Code Execution**: Repository code is **NEVER** imported, installed, or executed. Source inspection is strictly static (text/regex parsing).
- **File Safety Guard**: Binary files (`.exe`, `.dll`, `.bin`, `.pyc`) are strictly rejected, and files over 100KB are capped.
- **Prompt Injection Defense**: All repository content sent to AI providers is isolated inside `<untrusted_repository_content>` XML fences.
- **Token Security**: Tokens are masked in UI and logs. Never commit your active `.env` file!

---

## 📜 License
Distributed under the MIT License. Built with ❤️ for the open-source community.
