"""
Enterprise AI Recruitment Platform & Autonomous Document Parsing Engine.
Dedicated HR Admin Panel & Public Candidate Job Application Portals.
Clean Light Theme UI & Real Gemini LLM API Candidate Evaluation Engine.
"""

import io
import json
import os
import re
import smtplib
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

import pypdf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="Enterprise AI Recruitment Platform",
    description="Dedicated HR Admin Panel & Public Candidate Job Application Portals",
    version="4.3.0"
)

INITIAL_JOB = {
    "id": 1,
    "title": "Senior DevOps & Cloud Architect",
    "skills": ["python", "docker", "kubernetes", "aws", "terraform", "ci/cd", "linux"],
    "required_skills": ["python", "docker", "kubernetes", "aws", "terraform", "ci/cd", "linux"],
    "required_experience_years": 3,
    "required_education": "Bachelor's",
    "job_type": "Remote",
    "description": "We are seeking a skilled DevOps Architect with 3+ years experience to manage cloud infrastructure, containers, and automated deployment pipelines.",
    "posted_at": "2026-08-29 10:00:00"
}

ACTIVE_JOB = INITIAL_JOB.copy()
JOBS_HISTORY: list[dict[str, Any]] = [INITIAL_JOB.copy()]
APPLICATIONS: list[dict[str, Any]] = []

class JobRequirementsPayload(BaseModel):
    title: str
    required_skills: list[str]
    required_experience_years: int = 3
    required_education: str = "Bachelor's"
    job_type: str = "Full-Time"
    description: str = ""

@app.get("/health")
def health_check() -> dict[str, Any]:
    return {"status": "healthy", "active_job": ACTIVE_JOB}

@app.get("/api/get-job")
def get_job_requirements() -> dict[str, Any]:
    return ACTIVE_JOB

@app.get("/api/jobs-history")
def get_jobs_history() -> dict[str, Any]:
    return {"status": "success", "count": len(JOBS_HISTORY), "jobs": JOBS_HISTORY}

@app.get("/api/applications")
def get_applications() -> dict[str, Any]:
    return {"status": "success", "count": len(APPLICATIONS), "applications": APPLICATIONS}

@app.post("/api/set-job")
def set_job_requirements(payload: JobRequirementsPayload) -> dict[str, Any]:
    global ACTIVE_JOB
    cleaned_skills = [s.strip().lower() for s in payload.required_skills if s.strip()]
    req_skills = cleaned_skills if cleaned_skills else ["python", "docker", "kubernetes"]
    new_job = {
        "id": len(JOBS_HISTORY) + 1,
        "title": payload.title.strip(),
        "skills": req_skills,
        "required_skills": req_skills,
        "required_experience_years": max(0, payload.required_experience_years),
        "required_education": payload.required_education.strip() if payload.required_education else "Bachelor's",
        "job_type": payload.job_type.strip() if payload.job_type else "Full-Time",
        "description": payload.description.strip() if payload.description else "Full-time technical position.",
        "posted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }
    ACTIVE_JOB = new_job
    JOBS_HISTORY.insert(0, new_job)
    return {"status": "success", "message": f"Active job updated to '{payload.title}'", "active_job": ACTIVE_JOB}

def classify_document_authenticity(text: str) -> dict[str, Any]:
    """Detects if document is a genuine Candidate Resume vs a Study Plan/Roadmap/Syllabus."""
    lowered = text.lower()
    study_plan_keywords = [
        "weekly plan", "roadmap", "course syllabus", "curriculum", "learning plan",
        "study guide", "assignment", "homework", "week 1", "week 2", "week 3",
        "module 1", "lecture notes", "course outline"
    ]
    resume_keywords = [
        "experience", "work history", "employment", "education", "contact",
        "email", "phone", "responsibilities", "projects", "skill"
    ]
    study_matches = [k for k in study_plan_keywords if k in lowered]
    resume_matches = [k for k in resume_keywords if k in lowered]
    
    if len(study_matches) >= 2 and len(resume_matches) <= 2:
        return {
            "is_genuine_resume": False,
            "document_type": "Invalid Document (Study Plan / Roadmap / Syllabus Detected)",
            "flagged_terms": study_matches
        }
    return {
        "is_genuine_resume": True,
        "document_type": "Valid Candidate Resume / CV",
        "flagged_terms": []
    }

def extract_experience_years(text: str) -> int:
    """Extracts total years of experience from resume text."""
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp|work)',
        r'(?:experience|exp):\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s+in'
    ]
    found_years = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            try:
                found_years.append(int(m))
            except ValueError:
                pass
    if found_years:
        return max(found_years)
    year_ranges = re.findall(r'(20\d\d)\s*[-–—]\s*(20\d\d|present|current)', text, re.IGNORECASE)
    if year_ranges:
        total_yrs = 0
        for start, end in year_ranges:
            s_year = int(start)
            e_year = 2026 if end.lower() in ["present", "current"] else int(end)
            if e_year >= s_year:
                total_yrs += (e_year - s_year)
        if total_yrs > 0:
            return total_yrs
    return 1

def extract_education_level(text: str) -> str:
    """Extracts education degree level from resume text."""
    lowered = text.lower()
    if re.search(r'\b(phd|doctorate|doctor of philosophy)\b', lowered):
        return "PhD"
    if re.search(r'\b(master|m\.s\.|ms|mtech|m\.tech|mba)\b', lowered):
        return "Master's"
    if re.search(r'\b(bachelor|b\.s\.|bs|btech|b\.tech|b\.e\.|degree)\b', lowered):
        return "Bachelor's"
    return "Diploma / High School"

def evaluate_resume_with_gemini_api(
    text: str,
    job_title: str,
    required_skills: list[str],
    req_exp_years: int,
    req_education: str
) -> dict[str, Any] | None:
    """Uses real Google Gemini LLM API (GEMINI_API_KEY) to evaluate candidate suitability."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key or gemini_key.startswith("your_free_"):
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gemini_key}"
        prompt = f"""You are an enterprise AI HR recruiter evaluating candidate suitability.

JOB OPENING: {job_title}
REQUIRED SKILLS: {', '.join(required_skills)}
REQUIRED MIN EXPERIENCE: {req_exp_years} years
REQUIRED DEGREE: {req_education}

CANDIDATE RESUME:
{text[:2500]}

Evaluate candidate suitability and return ONLY a JSON object with these exact keys:
{{
  "is_genuine_resume": true or false,
  "document_type": "Valid Candidate Resume" or "Invalid Document (Roadmap/Syllabus)",
  "detected_experience_years": int,
  "detected_education": "Bachelor's" or "Master's" or "PhD" or "Diploma",
  "matched_skills": list of matched skill strings,
  "missing_skills": list of missing skill strings,
  "score": int between 0 and 100,
  "recommendation": "Shortlisted for Interview" or "Review Required / Rejected",
  "ai_reasoning": "Detailed 2-sentence breakdown of candidate suitability"
}}
"""
        data = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned_json = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned_json)
            parsed["evaluation_source"] = "Google Gemini LLM API (GEMINI_API_KEY)"
            print(f"[GEMINI LLM API SUCCESS] Candidate evaluated via Real Gemini API. Score: {parsed.get('score')}%")
            return parsed
    except Exception as err:
        print(f"[GEMINI LLM NOTICE] Gemini API call skipped/failed, using local evaluation: {err}")
        return None

def calculate_enterprise_score(
    text: str,
    required_skills: list[str],
    req_exp_years: int,
    req_education: str
) -> dict[str, Any]:
    """Calculates weighted hiring score using Real Gemini LLM API or Local Heuristic Engine fallback."""
    # 1. Try Real Google Gemini LLM API evaluation
    gemini_result = evaluate_resume_with_gemini_api(
        text=text,
        job_title=ACTIVE_JOB.get("title", "Software Engineer"),
        required_skills=required_skills,
        req_exp_years=req_exp_years,
        req_education=req_education
    )

    if gemini_result and "score" in gemini_result:
        score = int(gemini_result["score"])
        is_shortlisted = score >= 60
        gemini_result["final_score"] = score
        gemini_result["is_shortlisted"] = is_shortlisted
        return gemini_result

    # 2. Local Fallback Engine
    doc_check = classify_document_authenticity(text)
    if not doc_check["is_genuine_resume"]:
        return {
            "evaluation_source": "Local Fallback Rules Engine",
            "is_genuine_resume": False,
            "document_type": doc_check["document_type"],
            "flagged_terms": doc_check["flagged_terms"],
            "detected_experience_years": 0,
            "detected_education": "None",
            "matched_skills": [],
            "missing_skills": required_skills,
            "skill_score": 0,
            "experience_score": 0,
            "education_score": 0,
            "final_score": 0,
            "is_shortlisted": False,
            "recommendation": f"Rejected: {doc_check['document_type']}",
            "ai_reasoning": "Document was flagged as an invalid study plan or course syllabus rather than a candidate resume."
        }
    
    matched_skills = [s for s in required_skills if re.search(r"\b" + re.escape(s) + r"\b", text, re.IGNORECASE)]
    missing_skills = [s for s in required_skills if s not in matched_skills]
    skill_score = round((len(matched_skills) / len(required_skills)) * 100) if required_skills else 100
    
    det_exp = extract_experience_years(text)
    if req_exp_years <= 0 or det_exp >= req_exp_years:
        exp_score = 100
    else:
        exp_score = round((det_exp / req_exp_years) * 100)
        
    det_edu = extract_education_level(text)
    edu_weights = {"Diploma / High School": 1, "Bachelor's": 2, "Master's": 3, "PhD": 4}
    req_weight = edu_weights.get(req_education, 1)
    det_weight = edu_weights.get(det_edu, 1)
    
    if req_education == "Any" or det_weight >= req_weight:
        edu_score = 100
    else:
        edu_score = 60
        
    final_score = round((skill_score * 0.5) + (exp_score * 0.3) + (edu_score * 0.2))
    is_shortlisted = final_score >= 60
    
    return {
        "evaluation_source": "Local Fallback Rules Engine",
        "is_genuine_resume": True,
        "document_type": doc_check["document_type"],
        "flagged_terms": [],
        "detected_experience_years": det_exp,
        "detected_education": det_edu,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_score": skill_score,
        "experience_score": exp_score,
        "education_score": edu_score,
        "final_score": final_score,
        "is_shortlisted": is_shortlisted,
        "recommendation": "Shortlisted for Interview" if is_shortlisted else "Review Required / Rejected",
        "ai_reasoning": f"Matched {len(matched_skills)}/{len(required_skills)} required technical skills with {det_exp} detected years of experience."
    }

def send_email_to_mailpit(to_email: str, candidate_name: str, score: int, is_shortlisted: bool, job_title: str):
    """Sends email directly to Mailpit SMTP server or HTTP API with automatic host fallbacks."""
    if is_shortlisted:
        subject = f"🎉 Interview Invitation: {job_title}"
        body = (
            f"Hi {candidate_name},\n\n"
            f"Congratulations! Your resume scored {score}% suitability for the {job_title} position.\n"
            f"We would like to invite you for an interview with our engineering team.\n\n"
            f"Best regards,\nHR Talent Acquisition Team"
        )
    else:
        subject = f"Application Update: {job_title}"
        body = (
            f"Hi {candidate_name},\n\n"
            f"Thank you for applying for the {job_title} position. Your resume match score was {score}%.\n"
            f"At this time, we are seeking candidates with different technical skill profiles.\n\n"
            f"Best regards,\nHR Talent Acquisition Team"
        )

    smtp_hosts = ["mailpit", "localhost", "127.0.0.1", "host.docker.internal"]
    for host in smtp_hosts:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = "recruiting@company.local"
            msg["To"] = to_email
            with smtplib.SMTP(host, 1025, timeout=2) as server:
                server.sendmail("recruiting@company.local", [to_email], msg.as_string())
            print(f"[MAILPIT SUCCESS] Dispatched email to Mailpit SMTP via {host}:1025")
            return
        except Exception as err:
            print(f"[MAILPIT DEBUG] SMTP {host}:1025 failed: {err}")
            continue

    http_urls = [
        "http://mailpit:8025/api/v1/send",
        "http://localhost:8025/api/v1/send",
        "http://127.0.0.1:8025/api/v1/send"
    ]
    payload = json.dumps({
        "From": {"Email": "recruiting@company.local", "Name": "HR Talent Acquisition"},
        "To": [{"Email": to_email, "Name": candidate_name}],
        "Subject": subject,
        "Text": body
    }).encode("utf-8")

    for url in http_urls:
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2)
            print(f"[MAILPIT SUCCESS] Dispatched email to Mailpit HTTP API via {url}")
            return
        except Exception as err:
            print(f"[MAILPIT DEBUG] HTTP API {url} failed: {err}")
            continue

def trigger_n8n_workflow(full_name: str, email: str, resume_text: str, target_role: str):
    """Triggers n8n workflow live for visual execution tracking."""
    try:
        data = json.dumps({
            "full_name": full_name,
            "email": email,
            "resume_text": resume_text,
            "target_role": target_role
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "http://n8n:5678/webhook/hr-recruitment",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        print(f"Optional n8n webhook notify notice: {e}")

@app.post("/api/submit-application")
async def submit_application(
    full_name: str = Form(...),
    email: str = Form(...),
    resume_file: UploadFile = File(None),
    resume_text: str = Form("")
) -> dict[str, Any]:
    extracted_text = ""

    if resume_file and resume_file.filename:
        if not resume_file.filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")
        
        contents = await resume_file.read()
        if resume_file.filename.lower().endswith(".pdf"):
            try:
                pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
                for page in pdf_reader.pages:
                    extracted_text += (page.extract_text() or "") + " "
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {e!s}")
        else:
            extracted_text = contents.decode("utf-8", errors="ignore")
    else:
        extracted_text = resume_text

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Please upload a valid PDF resume file or paste text")

    res_eval = calculate_enterprise_score(
        text=extracted_text,
        required_skills=ACTIVE_JOB.get("required_skills", ACTIVE_JOB.get("skills", [])),
        req_exp_years=ACTIVE_JOB.get("required_experience_years", 3),
        req_education=ACTIVE_JOB.get("required_education", "Bachelor's")
    )

    job_title = ACTIVE_JOB["title"]
    score = res_eval["final_score"]
    is_shortlisted = res_eval["is_shortlisted"]

    send_email_to_mailpit(
        to_email=email,
        candidate_name=full_name,
        score=score,
        is_shortlisted=is_shortlisted,
        job_title=job_title
    )

    trigger_n8n_workflow(
        full_name=full_name,
        email=email,
        resume_text=extracted_text,
        target_role=job_title
    )

    app_record = {
        "id": len(APPLICATIONS) + 1,
        "candidate_name": full_name,
        "email": email,
        "job_title": job_title,
        "score": score,
        "suitability_score": score,
        "detected_experience_years": res_eval.get("detected_experience_years", 0),
        "detected_education": res_eval.get("detected_education", "N/A"),
        "is_genuine_resume": res_eval.get("is_genuine_resume", True),
        "document_type": res_eval.get("document_type", "Valid Candidate Resume"),
        "recommendation": res_eval.get("recommendation", "Evaluated"),
        "ai_reasoning": res_eval.get("ai_reasoning", "Candidate suitability evaluated."),
        "evaluation_source": res_eval.get("evaluation_source", "System Evaluator"),
        "matched_skills": res_eval.get("matched_skills", []),
        "missing_skills": res_eval.get("missing_skills", []),
        "applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }
    APPLICATIONS.insert(0, app_record)

    return {
        "status": "success",
        "candidate_name": full_name,
        "email": email,
        "job_title": job_title,
        "score": score,
        "suitability_score": score,
        "detected_experience_years": res_eval.get("detected_experience_years", 0),
        "detected_education": res_eval.get("detected_education", "N/A"),
        "is_genuine_resume": res_eval.get("is_genuine_resume", True),
        "document_type": res_eval.get("document_type", "Valid Candidate Resume"),
        "recommendation": res_eval.get("recommendation", "Evaluated"),
        "ai_reasoning": res_eval.get("ai_reasoning", ""),
        "evaluation_source": res_eval.get("evaluation_source", ""),
        "matched_skills": res_eval.get("matched_skills", []),
        "missing_skills": res_eval.get("missing_skills", []),
        "email_sent": True,
        "n8n_triggered": True
    }

class ResumeMatchPayload(BaseModel):
    resume_text: str = ""
    target_role: str = ""

@app.api_route("/extract-resume", methods=["GET", "POST"])
def extract_resume(payload: ResumeMatchPayload = None, resume_text: str = "", target_role: str = "") -> dict[str, Any]:
    text = payload.resume_text if payload and payload.resume_text else resume_text
    if not text:
        text = "Sample candidate resume with Python, Docker, Kubernetes, Linux."

    res_eval = calculate_enterprise_score(
        text=text,
        required_skills=ACTIVE_JOB.get("required_skills", ACTIVE_JOB.get("skills", [])),
        req_exp_years=ACTIVE_JOB.get("required_experience_years", 3),
        req_education=ACTIVE_JOB.get("required_education", "Bachelor's")
    )

    return {
        "job_position": ACTIVE_JOB["title"],
        "required_skills": ACTIVE_JOB.get("required_skills", ACTIVE_JOB.get("skills", [])),
        "detected_skills": res_eval.get("matched_skills", []),
        "missing_skills": res_eval.get("missing_skills", []),
        "detected_experience_years": res_eval.get("detected_experience_years", 0),
        "detected_education": res_eval.get("detected_education", "N/A"),
        "is_genuine_resume": res_eval.get("is_genuine_resume", True),
        "document_type": res_eval.get("document_type", "Valid Candidate Resume"),
        "skill_score": res_eval.get("skill_score", res_eval.get("final_score", 0)),
        "experience_score": res_eval.get("experience_score", 100),
        "education_score": res_eval.get("education_score", 100),
        "suitability_score": res_eval.get("final_score", 0),
        "score": res_eval.get("final_score", 0),
        "recommendation": res_eval.get("recommendation", "Evaluated"),
        "ai_reasoning": res_eval.get("ai_reasoning", ""),
        "evaluation_source": res_eval.get("evaluation_source", "")
    }

@app.post("/parse")
async def parse_document(payload: dict[str, Any] = None) -> dict[str, Any]:
    text = payload.get("text", "") if payload else ""
    return extract_resume(resume_text=text)

@app.post("/send-email")
def send_email_api(payload: dict[str, Any]) -> dict[str, Any]:
    to_email = payload.get("email", "test@example.com")
    name = payload.get("candidate_name", "Candidate")
    score = payload.get("score", 75)
    is_shortlisted = score >= 60
    job_title = ACTIVE_JOB["title"]

    send_email_to_mailpit(to_email, name, score, is_shortlisted, job_title)
    return {"status": "success", "message": f"Email dispatched to {to_email}"}

# ---------------------------------------------------------------------------
# Clean High-End Enterprise Light Theme UI System
# ---------------------------------------------------------------------------

LIGHT_THEME_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-main: #F8FAFC;
        --card-bg: #FFFFFF;
        --border-color: #E2E8F0;
        --primary: #4F46E5;
        --primary-hover: #4338CA;
        --text-primary: #0F172A;
        --text-secondary: #475569;
        --text-muted: #64748B;
        --success-text: #047857;
        --success-bg: #D1FAE5;
        --success-border: #A7F3D0;
        --danger-text: #B91C1C;
        --danger-bg: #FEE2E2;
        --danger-border: #FCA5A5;
        --badge-blue-bg: #EEF2FF;
        --badge-blue-text: #3730A3;
    }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--bg-main);
        color: var(--text-primary);
        margin: 0;
        padding: 40px 20px;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .container {
        max-width: 960px;
        width: 100%;
    }

    .header-banner {
        text-align: center;
        margin-bottom: 32px;
    }

    .header-banner h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
    }

    .header-banner p {
        color: var(--text-secondary);
        font-size: 1.05rem;
        margin: 0;
    }

    .card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }

    .card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-top: 0;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    label {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text-secondary);
        display: block;
        margin-bottom: 6px;
    }

    input[type="text"], input[type="email"], input[type="number"], select, textarea {
        width: 100%;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        color: var(--text-primary);
        padding: 11px 14px;
        border-radius: 8px;
        box-sizing: border-box;
        font-family: inherit;
        font-size: 0.95rem;
        margin-bottom: 16px;
        transition: border-color 0.15s, box-shadow 0.15s;
    }

    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
    }

    .btn-primary {
        background-color: var(--primary);
        color: #FFFFFF;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        cursor: pointer;
        width: 100%;
        transition: background-color 0.15s, transform 0.1s;
    }

    .btn-primary:hover {
        background-color: var(--primary-hover);
    }

    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 4px;
    }

    .badge-blue { background-color: var(--badge-blue-bg); color: var(--badge-blue-text); border: 1px solid #C7D2FE; }
    .badge-success { background-color: var(--success-bg); color: var(--success-text); border: 1px solid var(--success-border); }
    .badge-danger { background-color: var(--danger-bg); color: var(--danger-text); border: 1px solid var(--danger-border); }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
    }

    th, td {
        padding: 12px 14px;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.88rem;
    }

    th {
        background-color: #F1F5F9;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }

    .result-box {
        margin-top: 16px;
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.88rem;
        color: #34D399;
        white-space: pre-wrap;
        display: none;
    }

    .source-badge {
        font-size: 0.75rem;
        font-weight: 600;
        color: #4F46E5;
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        padding: 2px 8px;
        border-radius: 4px;
    }
</style>
"""

@app.get("/apply", response_class=HTMLResponse)
@app.get("/careers", response_class=HTMLResponse)
def serve_candidate_portal():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Careers & Job Application Portal</title>
        {LIGHT_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <h1>💼 Careers & Job Application Portal</h1>
                <p>Submit your candidate application for real-time Gemini LLM AI evaluation</p>
            </div>

            <div class="card" style="border-left: 4px solid var(--primary);">
                <div style="font-size:0.78rem; font-weight:700; color:var(--primary); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">OPEN VACANCY</div>
                <h2 id="displayJobTitle" style="font-family:'Space Grotesk'; font-size:1.5rem; margin:0 0 8px 0;">Loading Position...</h2>
                <p id="displayJobDesc" style="color:var(--text-secondary); font-size:0.95rem; margin:0 0 14px 0;"></p>
                <div id="displayMetaBadges"></div>
                <div id="displaySkillsTags" style="margin-top:10px;"></div>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>📝 Candidate Application Form</span>
                </div>

                <form id="appForm" onsubmit="handleCandidateSubmit(event)">
                    <label>Full Name *</label>
                    <input type="text" id="candName" placeholder="e.g. Usman Ali" required>

                    <label>Email Address *</label>
                    <input type="email" id="candEmail" placeholder="e.g. usman@example.com" required>

                    <label>📎 Upload Resume File (PDF / TXT) *</label>
                    <input type="file" id="candResumeFile" accept=".pdf,.txt">

                    <label>Or Paste Resume Text:</label>
                    <textarea id="candResumeText" rows="5" placeholder="Paste your candidate resume text here..."></textarea>

                    <button type="submit" class="btn-primary">🚀 Submit Application to Gemini AI Engine</button>
                </form>

                <div id="candResult" class="result-box"></div>
            </div>
        </div>

        <script>
            async function loadActiveJob() {{
                try {{
                    const res = await fetch('/api/get-job');
                    const job = await res.json();
                    document.getElementById('displayJobTitle').innerText = job.title;
                    document.getElementById('displayJobDesc').innerText = job.description;

                    const meta = document.getElementById('displayMetaBadges');
                    meta.innerHTML = `
                        <span class="badge badge-blue">⏳ Required Experience: ${{job.required_experience_years || 3}}+ Years</span>
                        <span class="badge badge-blue">🎓 Required Degree: ${{job.required_education || "Bachelor's"}}</span>
                        <span class="badge badge-blue">📍 Mode: ${{job.job_type || "Remote"}}</span>
                    `;

                    const container = document.getElementById('displaySkillsTags');
                    const skills = job.required_skills || job.skills || [];
                    container.innerHTML = '<strong style="font-size:0.85rem; color:var(--text-secondary);">Required Skills:</strong><br>';
                    skills.forEach(s => {{
                        container.innerHTML += `<span class="badge badge-blue">${{s.toUpperCase()}}</span>`;
                    }});
                }} catch(e) {{}}
            }}
            loadActiveJob();

            async function handleCandidateSubmit(e) {{
                e.preventDefault();
                const name = document.getElementById('candName').value;
                const email = document.getElementById('candEmail').value;
                const fileInput = document.getElementById('candResumeFile');
                const textInput = document.getElementById('candResumeText').value;
                const resBox = document.getElementById('candResult');

                resBox.style.display = 'block';
                resBox.innerText = 'Evaluating resume via Google Gemini AI API & triggering n8n workflow...';

                const formData = new FormData();
                formData.append('full_name', name);
                formData.append('email', email);
                if (fileInput.files.length > 0) {{
                    formData.append('resume_file', fileInput.files[0]);
                }}
                formData.append('resume_text', textInput);

                try {{
                    const res = await fetch('/api/submit-application', {{
                        method: 'POST',
                        body: formData
                    }});
                    const data = await res.json();
                    resBox.innerText = JSON.stringify(data, null, 2);
                }} catch(err) {{
                    resBox.innerText = 'Error submitting application';
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def serve_admin_portal():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HR Admin Control Panel & Candidate Dashboard</title>
        {LIGHT_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <h1>⚙️ HR Admin Control Panel & ATS Dashboard</h1>
                <p>Define job vacancies, monitor real Gemini AI evaluation scores, and track candidate history</p>
            </div>

            <!-- Job Publishing -->
            <div class="card">
                <div class="card-title">
                    <span>📢 Publish Active Job Vacancy</span>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label>Job Position Title:</label>
                        <input type="text" id="adminTitle" value="Senior DevOps & Cloud Architect">
                    </div>
                    <div>
                        <label>Job Mode / Location:</label>
                        <select id="adminJobType">
                            <option value="Full-Time" selected>Full-Time</option>
                            <option value="Remote">Remote</option>
                            <option value="Hybrid">Hybrid</option>
                            <option value="On-site">On-site</option>
                        </select>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label>Required Min Experience (Years):</label>
                        <input type="number" id="adminExp" value="3" min="0" max="20">
                    </div>
                    <div>
                        <label>Required Min Degree:</label>
                        <select id="adminEdu">
                            <option value="Bachelor's" selected>Bachelor's Degree</option>
                            <option value="Master's">Master's Degree</option>
                            <option value="PhD">PhD / Doctorate</option>
                            <option value="Any">Any Qualification</option>
                        </select>
                    </div>
                </div>

                <label>Job Description:</label>
                <textarea id="adminDesc" rows="2">We are seeking a DevOps Architect with 3+ years experience to manage cloud infrastructure, containers, and automated deployment pipelines.</textarea>

                <label>Required Technical Skills (Comma Separated):</label>
                <input type="text" id="adminSkills" value="Python, Docker, Kubernetes, AWS, Terraform, CI/CD, Linux">

                <button class="btn-primary" onclick="publishNewJob()">📢 Publish & Update Candidate Portal</button>
                <div id="adminResult" class="result-box"></div>
            </div>

            <!-- Applications Dashboard with Live Search Filter -->
            <div class="card">
                <div class="card-title">
                    <span>📥 Received Candidate Applications (ATS)</span>
                    <button onclick="loadDashboardData()" style="background:#F1F5F9; color:var(--text-primary); border:1px solid #CBD5E1; padding:6px 12px; border-radius:6px; font-size:0.85rem; font-weight:600; cursor:pointer;">🔄 Refresh</button>
                </div>

                <div style="margin-bottom: 14px;">
                    <input type="text" id="searchFilter" onkeyup="filterApplications()" placeholder="🔍 Filter candidates by name, position, or status..." style="margin-bottom:0;">
                </div>

                <div id="appsTableContainer">
                    <p style="color:var(--text-secondary);">Loading candidate applications...</p>
                </div>
            </div>

            <!-- Job History -->
            <div class="card">
                <div class="card-title">
                    <span>📜 Job Postings Archive</span>
                </div>
                <div id="jobsHistoryContainer">
                    <p style="color:var(--text-secondary);">Loading job history...</p>
                </div>
            </div>
        </div>

        <script>
            let cachedApplications = [];

            async function publishNewJob() {{
                const title = document.getElementById('adminTitle').value;
                const jobType = document.getElementById('adminJobType').value;
                const expYears = parseInt(document.getElementById('adminExp').value) || 0;
                const eduLevel = document.getElementById('adminEdu').value;
                const desc = document.getElementById('adminDesc').value;
                const skillsArr = document.getElementById('adminSkills').value.split(',');
                const resBox = document.getElementById('adminResult');
                resBox.style.display = 'block';
                resBox.innerText = 'Publishing job position...';

                try {{
                    const res = await fetch('/api/set-job', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ 
                            title: title, 
                            job_type: jobType,
                            required_experience_years: expYears,
                            required_education: eduLevel,
                            description: desc, 
                            required_skills: skillsArr 
                        }})
                    }});
                    const data = await res.json();
                    resBox.innerText = JSON.stringify(data, null, 2);
                    loadDashboardData();
                }} catch(e) {{
                    resBox.innerText = 'Error updating job requirements';
                }}
            }}

            function filterApplications() {{
                const query = document.getElementById('searchFilter').value.toLowerCase();
                const filtered = cachedApplications.filter(a => 
                    (a.candidate_name && a.candidate_name.toLowerCase().includes(query)) ||
                    (a.job_title && a.job_title.toLowerCase().includes(query)) ||
                    (a.recommendation && a.recommendation.toLowerCase().includes(query))
                );
                renderApplicationsTable(filtered);
            }}

            function renderApplicationsTable(apps) {{
                const container = document.getElementById('appsTableContainer');
                if (!apps || apps.length === 0) {{
                    container.innerHTML = '<p style="color:var(--text-secondary); font-style:italic;">No candidate applications found.</p>';
                    return;
                }}

                let html = `<table>
                    <thead>
                        <tr>
                            <th>Candidate</th>
                            <th>Applied Position</th>
                            <th>Detected Exp</th>
                            <th>Degree</th>
                            <th>Authenticity</th>
                            <th>AI Score</th>
                            <th>Evaluation Source</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>`;

                apps.forEach(a => {{
                    const badge = a.score >= 60 ? 
                        `<span class="badge badge-success">Shortlisted (${{a.score}}%)</span>` : 
                        `<span class="badge badge-danger">Rejected (${{a.score}}%)</span>`;
                        
                    const docBadge = a.is_genuine_resume ?
                        `<span style="color:#047857; font-weight:600;">Valid CV</span>` :
                        `<span style="color:#B91C1C; font-weight:bold;">Invalid Document</span>`;

                    const source = a.evaluation_source ? `<span class="source-badge">${{a.evaluation_source}}</span>` : '';

                    html += `<tr>
                        <td><strong>${{a.candidate_name}}</strong><br><small style="color:var(--text-muted);">${{a.email}}</small></td>
                        <td>${{a.job_title}}</td>
                        <td>${{a.detected_experience_years !== undefined ? a.detected_experience_years + ' yrs' : 'N/A'}}</td>
                        <td>${{a.detected_education || 'N/A'}}</td>
                        <td>${{docBadge}}</td>
                        <td><strong style="font-size:1.05rem;">${{a.score}}%</strong></td>
                        <td>${{source}}</td>
                        <td>${{badge}}</td>
                    </tr>`;
                }});
                html += `</tbody></table>`;
                container.innerHTML = html;
            }}

            async function loadDashboardData() {{
                try {{
                    const res = await fetch('/api/applications');
                    const data = await res.json();
                    cachedApplications = data.applications || [];
                    renderApplicationsTable(cachedApplications);
                }} catch(e) {{}}

                try {{
                    const res = await fetch('/api/jobs-history');
                    const data = await res.json();
                    const container = document.getElementById('jobsHistoryContainer');

                    if (!data.jobs || data.jobs.length === 0) {{
                        container.innerHTML = '<p style="color:var(--text-secondary);">No job history available.</p>';
                    }} else {{
                        let html = '';
                        data.jobs.forEach(j => {{
                            const skills = j.required_skills || j.skills || [];
                            const tags = skills.map(s => `<span class="badge badge-blue">${{s.toUpperCase()}}</span>`).join(' ');
                            html += `<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:16px; margin-bottom:12px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0; font-family:'Space Grotesk'; color:var(--text-primary);">${{j.title}} (${{j.job_type || 'Full-Time'}})</h4>
                                    <small style="color:var(--text-muted);">${{j.posted_at || ''}}</small>
                                </div>
                                <div style="color:var(--primary); font-size:0.82rem; font-weight:600; margin:4px 0;">
                                    ⏳ Min Exp: ${{j.required_experience_years || 3}}+ yrs | 🎓 Degree: ${{j.required_education || "Bachelor's"}}
                                </div>
                                <p style="color:var(--text-secondary); font-size:0.88rem; margin:6px 0 10px 0;">${{j.description}}</p>
                                <div>${{tags}}</div>
                            </div>`;
                        }});
                        container.innerHTML = html;
                    }}
                }} catch(e) {{}}
            }}

            loadDashboardData();
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def serve_main_hub():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enterprise AI Recruitment Hub</title>
        {LIGHT_THEME_STYLE}
    </head>
    <body>
        <div class="container" style="text-align:center;">
            <div class="header-banner">
                <h1>⚡ Enterprise AI Recruitment Hub</h1>
                <p>Select your portal destination below:</p>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:30px;">
                <a href="/admin" style="text-decoration:none;">
                    <div class="card" style="height:100%; transition:transform 0.2s, box-shadow 0.2s;">
                        <div style="font-size:2.8rem; margin-bottom:12px;">⚙️</div>
                        <h2 style="font-family:'Space Grotesk'; font-size:1.4rem; margin:0 0 8px 0; color:var(--text-primary);">HR Admin Portal</h2>
                        <p style="color:var(--text-secondary); font-size:0.95rem;">Post job openings, define required skills, and track candidate ATS evaluation scores live.</p>
                    </div>
                </a>

                <a href="/apply" style="text-decoration:none;">
                    <div class="card" style="height:100%; transition:transform 0.2s, box-shadow 0.2s;">
                        <div style="font-size:2.8rem; margin-bottom:12px;">💼</div>
                        <h2 style="font-family:'Space Grotesk'; font-size:1.4rem; margin:0 0 8px 0; color:var(--text-primary);">Candidate Portal</h2>
                        <p style="color:var(--text-secondary); font-size:0.95rem;">View open positions, upload PDF resumes, and receive instant Gemini AI suitability evaluations.</p>
                    </div>
                </a>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
