# GitNova

> **Stop searching. Start contributing.** > An AI-powered engine that hunts for beginner-friendly Open Source issues so you don't have to.

##⚡Enough Thinking.
Most developers fail at Open Source because they get stuck in "Analysis Paralysis."  
**GitNova** solves this by automating the hunt. It scans thousands of GitHub issues, filters out the noise using **DeBERTa**, and uses **Llama 3** to generate step-by-step solution guides.

**🔴 Live Demo:** [gitnova-dev.vercel.app](https://gitnova-dev.vercel.app)

---

## 🛠️ Tech Stack
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React + Vite | Fast, responsive UI |
| **Styling** | Tailwind CSS | Clean, mobile-first design |
| **Database** | Supabase (PostgreSQL) | Stores curated issues |
| **AI Engine** | DeBERTa v3 | Zero-shot classification (Noise Filter) |
| **LLM Agent** | Llama 3 (via Groq) | Difficulty scoring & "Golden Response" generation |
| **Automation** | GitHub Actions | Cron jobs (Runs every 6 hours) |

---

## 🧠 How It Works (The Pipeline)
GitNova isn't just a scraper. It's an intelligent filtering system.

1.  **The Hunt:** A Python script runs on GitHub Actions every 6 hours.
2.  **The Filter (DeBERTa):** It scans ~4,000 raw issues/day. It discards 90% of them (Spam, Advanced C++ bugs, Feature requests).
3.  **The Analyst (Llama 3):** The remaining issues are read by an LLM agent. It:
    * Assigns a **Difficulty Score** (Novice vs. Apprentice).
    * Generates a **"How to Fix"** plan (Files to change + Logic).
4.  **The Display:** The React frontend fetches the "Gold Nuggets" from Supabase and displays them as cards.

---

## ✨ Features
* **🎯 AI Difficulty Scoring:** Know exactly if an issue is for beginners or pros.
* **🤖 Smart Hints:** Don't know where to start? The AI tells you which file to edit.
* **📱 Mobile Ready:** Fully responsive "Card Layout" for hunting on the go.
* **🏷️ Auto-Categorization:** Issues are sorted into ML, Web Dev, DevOps, and Mobile.

---

## 🚀 Local Setup

### 1. Clone the Repo
```bash
git clone [https://github.com/yourusername/gitnova.git](https://github.com/yourusername/gitnova.git)
cd gitnova
