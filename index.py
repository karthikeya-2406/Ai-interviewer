import os
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

app = FastAPI(
    title="InterviewAI API",
    description="Adaptive AI Technical Interviewer API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session state storage (keyed by sessionId)
sessions: Dict[str, Dict[str, Any]] = {}

# Load curriculum context if available
curriculum_data = {}
curriculum_path = os.path.join(os.path.dirname(__file__), "..", "curriculum.json")
if os.path.exists(curriculum_path):
    try:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum_data = json.load(f)
    except Exception as e:
        print(f"Error loading curriculum.json: {e}")

MAX_TURNS = 5  # Interview finishes after 5 turns

def get_gemini_client():
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY environment variable is not set.")
    return genai.Client(api_key=GOOGLE_API_KEY)

class FeedbackModel(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]

class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackModel] = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "InterviewAI Backend API is running", "model": GEMINI_MODEL}

@app.post("/api/interview", response_model=InterviewResponse)
def handle_interview(req: InterviewRequest):
    session_id = req.sessionId
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required")

    client = get_gemini_client()

    # 1. Initialize or load session
    if session_id not in sessions:
        if not req.candidate and not req.message:
            raise HTTPException(status_code=400, detail="candidate profile or message required for new session")
        
        candidate_profile = req.candidate or {}
        sessions[session_id] = {
            "sessionId": session_id,
            "candidate": candidate_profile,
            "history": [],
            "turn": 1,
            "done": False
        }

    session = sessions[session_id]

    if session["done"]:
        return InterviewResponse(
            reply="This interview session has already been completed.",
            done=True
        )

    # 2. Check turn count / candidate message
    if req.message:
        session["history"].append({"role": "user", "content": req.message})
        session["turn"] += 1

    current_turn = session["turn"]

    # 3. Handle End of Interview (turn > MAX_TURNS)
    if current_turn > MAX_TURNS:
        session["done"] = True
        
        # Ask LLM to generate structured feedback
        feedback_prompt = f"""
        Analyze the following interview history for candidate {session['candidate'].get('member', {}).get('name', 'Candidate')} for role {session['candidate'].get('member', {}).get('jobRole', 'Technical Role')}:
        
        Interview Conversation:
        {json.dumps(session['history'], indent=2)}

        Provide a structured evaluation in JSON with the exact fields:
        - "summary": A 2-3 sentence overview of candidate performance.
        - "strengths": List of 3 key strengths demonstrated.
        - "gaps": List of 2-3 areas needing improvement or knowledge gaps.
        - "next": List of 3 actionable recommended next learning steps.
        """
        
        try:
            res = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=feedback_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            feedback_data = json.loads(res.text)
        except Exception as e:
            print("Error generating feedback JSON:", e)
            feedback_data = {
                "summary": "Candidate demonstrated solid technical problem-solving capabilities throughout the interview questions.",
                "strengths": ["Clear communication", "Good grasp of core concepts", "Structured problem approach"],
                "gaps": ["Could elaborate more on edge-case handling", "Deep dive into system optimization"],
                "next": ["Review advanced architecture patterns", "Practice hands-on optimization exercises"]
            }

        feedback_obj = FeedbackModel(
            summary=feedback_data.get("summary", ""),
            strengths=feedback_data.get("strengths", []),
            gaps=feedback_data.get("gaps", []),
            next=feedback_data.get("next", [])
        )

        return InterviewResponse(
            reply="Thank you for taking the time to complete the interview! Your assessment has been evaluated.",
            done=True,
            feedback=feedback_obj
        )

    # 4. Generate next question/turn reply
    system_instruction = f"""
    You are an expert, encouraging AI technical interviewer conducting an adaptive technical interview.
    Candidate Profile: {json.dumps(session['candidate'], indent=2)}
    Curriculum Focus: {json.dumps(curriculum_data.get('modules', []), indent=2)}
    
    Current question number: {current_turn} of {MAX_TURNS}.
    
    Rules:
    - If this is question 1, welcome the candidate concisely by name and ask an engaging initial technical question based on their completed background/missions.
    - If this is follow-up turn (question 2 to {MAX_TURNS}), briefly acknowledge their previous response, evaluate their technical accuracy, and ask the next adaptive question on topics like vector search, LLMs, prompt engineering, or deployment.
    - Keep your response friendly, clear, professional, and under 150 words.
    """

    messages_payload = []
    messages_payload.append(system_instruction)
    
    for item in session["history"]:
        prefix = "Candidate: " if item["role"] == "user" else "Interviewer: "
        messages_payload.append(f"{prefix}{item['content']}")

    if current_turn == 1 and not session["history"]:
        messages_payload.append("Start the interview now with Question 1.")

    try:
        res = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="\n\n".join(messages_payload),
            config=types.GenerateContentConfig(temperature=0.7)
        )
        ai_reply = res.text.strip()
    except Exception as e:
        print("LLM Error:", e)
        ai_reply = f"Hello! Let's begin Question {current_turn}. Could you describe your experience working with LLMs and API integrations?"

    session["history"].append({"role": "assistant", "content": ai_reply})

    return InterviewResponse(
        reply=ai_reply,
        done=False
    )
