# InterviewAI — Adaptive AI Technical Interviewer

InterviewAI is an intelligent, context-aware technical interviewing platform powered by Google Gemini API and FastAPI. It conducts real-time adaptive interviews based on candidate profiles and curriculum requirements, evaluating candidate responses and outputting recruiter-ready feedback reports.

---

## 🌟 Key Features

- **Adaptive Question Generation**: Dynamically tailors technical questions based on candidate experience, background, and previous answers.
- **Context Memory**: Tracks conversation history using `sessionId` state.
- **Structured Feedback & Scoring**: Generates executive performance summaries, key strengths, growth areas, and actionable next steps.
- **Interactive Web Interface**: Single-page dark-mode web application built with Outfit / Plus Jakarta Sans typography, real-time timer, typing indicators, and assessment dashboards.
- **RESTful API Endpoint**: Standardized `POST /api/interview` endpoint compliant with Vercel serverless deployment specs.

---

## 🚀 Quick Start

### 1. Environment Setup
Copy `.env.example` to `.env` and insert your Google Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-flash-latest
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Backend Server
```bash
python main.py
```
The server starts at `http://127.0.0.1:8000`.

* **Interactive API Docs**: `http://127.0.0.1:8000/docs`
* **Web UI**: Open `index.html` in your web browser.

---

## 🛠️ API Specification

### `POST /api/interview`

#### Start Interview Request
```json
{
  "sessionId": "session-123",
  "candidate": {
    "member": {
      "name": "Sarah Johnson",
      "jobRole": "Senior Data Engineer",
      "yearsExperience": 9
    }
  }
}
```

#### Conversation Turn Request
```json
{
  "sessionId": "session-123",
  "message": "I have extensive experience with HNSW indexing and Pinecone vector search."
}
```

#### Final Turn Response (Complete)
```json
{
  "reply": "Thank you for completing the interview!",
  "done": true,
  "feedback": {
    "summary": "Candidate demonstrated exceptional knowledge of vector indexing...",
    "strengths": ["Clear communication", "HNSW vs IVF trade-off mastery"],
    "gaps": ["Edge case handling in dynamic chunking"],
    "next": ["Practice cross-encoder re-ranking implementation"]
  }
}
```

---

## 📁 Repository Structure

```
├── api/
│   └── index.py            # FastAPI application & Gemini client handler
├── main.py                 # Server entry point (Uvicorn runner)
├── index.html              # Modern glassmorphism web interface
├── candidates.json         # Sample candidate profiles
├── curriculum.json         # Interview curriculum data
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel serverless config
├── .env.example            # Environment variable template
└── README.md               # Project documentation
```
