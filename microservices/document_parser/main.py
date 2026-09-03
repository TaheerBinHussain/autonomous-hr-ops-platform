"""
Enterprise AI Recruitment Platform & Autonomous Document Parsing Engine.
Corporate Slate & Emerald Precision Architecture (Zero Emojis, Dedicated File Upload Portal, Multi-Vacancy Selection).
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
    version="5.0.0"
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
    return {"status": "healthy", "active_job": ACTIVE_JOB, "jobs_count": len(JOBS_HISTORY)}

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
    return {"status": "success", "message": f"Active job updated to '{payload.title}'", "active_job": ACTIVE_JOB, "jobs": JOBS_HISTORY}

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
  "ai_reasoning": "Detailed 2-sentence breakdown explaining exact reasons for acceptance or rejection"
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
    req_education: str,
    job_title: str = "Software Engineer"
) -> dict[str, Any]:
    """Calculates weighted hiring score using Real Gemini LLM API or Local Heuristic Engine fallback."""
    # 1. Try Real Google Gemini LLM API evaluation
    gemini_result = evaluate_resume_with_gemini_api(
        text=text,
        job_title=job_title,
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
            "ai_reasoning": "Application was rejected because the uploaded document was flagged as an invalid course syllabus or study roadmap rather than a authentic candidate resume."
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

    if is_shortlisted:
        reasoning = f"Accepted: Candidate matched {len(matched_skills)}/{len(required_skills)} required technical skills ({', '.join(matched_skills)}) and meets the {req_exp_years}-year experience requirement with {det_exp} detected years."
    else:
        missing_fmt = ', '.join(missing_skills) if missing_skills else 'core stack depth'
        reasoning = f"Rejected: Candidate missing key required skills ({missing_fmt}) or detected experience ({det_exp} years) fell below the required {req_exp_years} years threshold."
    
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
        "ai_reasoning": reasoning
    }

def send_email_to_mailpit(
    to_email: str,
    candidate_name: str,
    score: int,
    is_shortlisted: bool,
    job_title: str,
    ai_reasoning: str = "",
    matched_skills: list[str] = None,
    missing_skills: list[str] = None
):
    """Sends email directly to Mailpit SMTP server or HTTP API with detailed acceptance/rejection reasons (Zero Emojis)."""
    matched_str = ", ".join(matched_skills) if matched_skills else "None"
    missing_str = ", ".join(missing_skills) if missing_skills else "None"

    if is_shortlisted:
        subject = f"Interview Invitation: {job_title}"
        body = (
            f"Dear {candidate_name},\n\n"
            f"Thank you for applying for the {job_title} position. Your application scored {score}% suitability.\n\n"
            f"EVALUATION SUMMARY & QUALIFICATION REASONS:\n"
            f"- Match Score: {score}%\n"
            f"- Matched Required Skills: {matched_str}\n"
            f"- AI Evaluation Feedback: {ai_reasoning}\n\n"
            f"We would like to invite you for an interview with our technical panel.\n\n"
            f"Best regards,\nTalent Acquisition Team"
        )
    else:
        subject = f"Application Update: {job_title}"
        body = (
            f"Dear {candidate_name},\n\n"
            f"Thank you for applying for the {job_title} position. Your resume match score was {score}%.\n\n"
            f"EVALUATION SUMMARY & SPECIFIC REASONS FOR REJECTION:\n"
            f"- Match Score: {score}%\n"
            f"- Missing Core Skills: {missing_str}\n"
            f"- AI Evaluation Feedback: {ai_reasoning}\n\n"
            f"We are seeking candidates with higher alignment in our specific required technical stack.\n\n"
            f"Best regards,\nTalent Acquisition Team"
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
        "From": {"Email": "recruiting@company.local", "Name": "Talent Acquisition"},
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
    job_id: int = Form(0),
    job_title_input: str = Form(""),
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
        raise HTTPException(status_code=400, detail="Please select and upload a valid PDF or TXT candidate resume file.")

    # Resolve target job vacancy from selection
    target_job = ACTIVE_JOB
    if job_id > 0:
        found = next((j for j in JOBS_HISTORY if j.get("id") == job_id), None)
        if found:
            target_job = found
    elif job_title_input.strip():
        found = next((j for j in JOBS_HISTORY if j.get("title").lower() == job_title_input.strip().lower()), None)
        if found:
            target_job = found

    job_title = target_job["title"]
    req_skills = target_job.get("required_skills", target_job.get("skills", []))
    req_exp = target_job.get("required_experience_years", 3)
    req_edu = target_job.get("required_education", "Bachelor's")

    res_eval = calculate_enterprise_score(
        text=extracted_text,
        required_skills=req_skills,
        req_exp_years=req_exp,
        req_education=req_edu,
        job_title=job_title
    )

    score = res_eval["final_score"]
    is_shortlisted = res_eval["is_shortlisted"]
    reasoning = res_eval.get("ai_reasoning", "")
    matched = res_eval.get("matched_skills", [])
    missing = res_eval.get("missing_skills", [])

    send_email_to_mailpit(
        to_email=email,
        candidate_name=full_name,
        score=score,
        is_shortlisted=is_shortlisted,
        job_title=job_title,
        ai_reasoning=reasoning,
        matched_skills=matched,
        missing_skills=missing
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
        "ai_reasoning": reasoning,
        "evaluation_source": res_eval.get("evaluation_source", "System Evaluator"),
        "matched_skills": matched,
        "missing_skills": missing,
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
        "ai_reasoning": reasoning,
        "evaluation_source": res_eval.get("evaluation_source", ""),
        "matched_skills": matched,
        "missing_skills": missing,
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
        text = "Candidate resume with Python, Docker, Kubernetes, Linux."

    res_eval = calculate_enterprise_score(
        text=text,
        required_skills=ACTIVE_JOB.get("required_skills", ACTIVE_JOB.get("skills", [])),
        req_exp_years=ACTIVE_JOB.get("required_experience_years", 3),
        req_education=ACTIVE_JOB.get("required_education", "Bachelor's"),
        job_title=ACTIVE_JOB["title"]
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
    name = payload.get("candidate_name", "Taheer Bin Hussain")
    score = payload.get("score", 75)
    is_shortlisted = score >= 60
    job_title = ACTIVE_JOB["title"]
    reasoning = payload.get("ai_reasoning", "Evaluated suitability.")

    send_email_to_mailpit(to_email, name, score, is_shortlisted, job_title, reasoning)
    return {"status": "success", "message": f"Email dispatched to {to_email}"}

# ---------------------------------------------------------------------------
# Slate & Emerald Corporate Precision Architecture (Zero Emojis)
# ---------------------------------------------------------------------------

CORPORATE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-slate: #F8FAFC;
        --card-bg: #FFFFFF;
        --border-slate: #E2E8F0;
        --text-main: #0F172A;
        --text-muted: #64748B;
        --emerald-primary: #059669;
        --emerald-hover: #047857;
        --emerald-light: #ECFDF5;
        --emerald-border: #A7F3D0;
        --navy-dark: #1E293B;
        --rose-alert: #991B1B;
        --rose-bg: #FEF2F2;
        --rose-border: #FECACA;
        --blue-badge-bg: #EFF6FF;
        --blue-badge-text: #1E40AF;
        --blue-badge-border: #BFDBFE;
    }

    * { box-sizing: border-box; }

    body {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
        background-color: var(--bg-slate);
        color: var(--text-main);
        margin: 0;
        padding: 0;
        min-height: 100vh;
    }

    /* Top Navigation Bar */
    .navbar {
        background-color: #FFFFFF;
        border-bottom: 1px solid var(--border-slate);
        padding: 16px 36px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }

    .navbar-brand {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-main);
        letter-spacing: -0.3px;
        text-decoration: none;
    }

    .navbar-brand span {
        color: var(--emerald-primary);
    }

    .nav-links {
        display: flex;
        gap: 16px;
    }

    .nav-link {
        color: var(--text-muted);
        text-decoration: none;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 8px 14px;
        border-radius: 6px;
        transition: all 0.15s ease;
    }

    .nav-link:hover, .nav-link.active {
        color: var(--emerald-primary);
        background-color: var(--emerald-light);
    }

    .main-wrapper {
        max-width: 1040px;
        margin: 36px auto;
        padding: 0 20px;
    }

    .page-header {
        margin-bottom: 24px;
    }

    .page-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-main);
        margin: 0 0 6px 0;
        letter-spacing: -0.4px;
    }

    .page-header p {
        color: var(--text-muted);
        font-size: 0.98rem;
        margin: 0;
    }

    /* Metric Cards Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid var(--border-slate);
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }

    .metric-card .label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        margin-bottom: 4px;
    }

    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-main);
    }

    .card {
        background: var(--card-bg);
        border: 1px solid var(--border-slate);
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    }

    .card-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-main);
        margin-top: 0;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-slate);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    label {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-main);
        display: block;
        margin-bottom: 6px;
    }

    input[type="text"], input[type="email"], input[type="number"], select {
        width: 100%;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        color: var(--text-main);
        padding: 10px 12px;
        border-radius: 6px;
        font-family: inherit;
        font-size: 0.92rem;
        margin-bottom: 16px;
        transition: border-color 0.15s;
    }

    input:focus, select:focus {
        outline: none;
        border-color: var(--emerald-primary);
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.12);
    }

    /* File Drop Zone Area */
    .file-upload-box {
        border: 2px dashed #CBD5E1;
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        cursor: pointer;
        margin-bottom: 18px;
        transition: border-color 0.2s, background-color 0.2s;
    }

    .file-upload-box:hover {
        border-color: var(--emerald-primary);
        background-color: var(--emerald-light);
    }

    .file-upload-box input[type="file"] {
        display: none;
    }

    .file-upload-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text-main);
    }

    .file-upload-sub {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 4px;
    }

    .btn-emerald {
        background-color: var(--emerald-primary);
        color: #FFFFFF;
        border: none;
        padding: 11px 20px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.92rem;
        cursor: pointer;
        width: 100%;
        transition: background-color 0.15s;
    }

    .btn-emerald:hover {
        background-color: var(--emerald-hover);
    }

    .tag-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 4px;
    }

    .tag-blue { background-color: var(--blue-badge-bg); color: var(--blue-badge-text); border: 1px solid var(--blue-badge-border); }
    .tag-success { background-color: var(--emerald-light); color: var(--emerald-primary); border: 1px solid var(--emerald-border); }
    .tag-danger { background-color: var(--rose-bg); color: var(--rose-alert); border: 1px solid var(--rose-border); }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th, td {
        padding: 12px 14px;
        text-align: left;
        border-bottom: 1px solid var(--border-slate);
        font-size: 0.86rem;
    }

    th {
        background-color: #F8FAFC;
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.5px;
    }

    .response-box {
        margin-top: 16px;
        background-color: #0F172A;
        color: #34D399;
        border-radius: 6px;
        padding: 14px;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.84rem;
        white-space: pre-wrap;
        display: none;
    }

    .source-tag {
        font-size: 0.72rem;
        font-weight: 600;
        color: #059669;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        padding: 2px 6px;
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
        <title>Candidate Application Portal</title>
        {CORPORATE_STYLE}
    </head>
    <body>
        <div class="navbar">
            <a href="/" class="navbar-brand">Enterprise AI <span>Recruitment</span></a>
            <div class="nav-links">
                <a href="/admin" class="nav-link">HR Administration</a>
                <a href="/apply" class="nav-link active">Candidate Application</a>
                <a href="/docs" class="nav-link" target="_blank">API Documentation</a>
            </div>
        </div>

        <div class="main-wrapper">
            <div class="page-header">
                <h1>Candidate Job Application Portal</h1>
                <p>Select a job vacancy, upload your candidate resume file (PDF or TXT), and submit for automated AI evaluation.</p>
            </div>

            <!-- Position Specification Box -->
            <div class="card" style="border-left: 4px solid var(--emerald-primary);">
                <label>Target Job Vacancy:</label>
                <select id="jobSelector" onchange="onJobSelectChange()" style="font-size:1rem; font-weight:600; padding:10px; margin-bottom:16px;">
                    <option value="">Loading active job vacancies...</option>
                </select>

                <div id="displayJobTitle" style="font-size:1.35rem; font-weight:700; color:var(--text-main); margin-bottom:6px;">Loading Position...</div>
                <div id="displayJobDesc" style="color:var(--text-muted); font-size:0.92rem; margin-bottom:12px;"></div>
                <div id="displayMetaBadges"></div>
                <div id="displaySkillsTags" style="margin-top:10px;"></div>
            </div>

            <!-- Application Form -->
            <div class="card">
                <div class="card-header">
                    <span>Application Form</span>
                </div>

                <form id="appForm" onsubmit="handleCandidateSubmit(event)">
                    <label>Full Name *</label>
                    <input type="text" id="candName" value="Taheer Bin Hussain" placeholder="e.g. Taheer Bin Hussain" required>

                    <label>Email Address *</label>
                    <input type="email" id="candEmail" value="taheer@example.com" placeholder="e.g. taheer@example.com" required>

                    <label>Upload Candidate Resume File (PDF or TXT) *</label>
                    <div class="file-upload-box" onclick="triggerFileInput()">
                        <input type="file" id="candResumeFile" accept=".pdf,.txt" onchange="updateFileName(this)">
                        <div class="file-upload-title" id="fileUploadLabel">Click or Drag PDF / TXT Resume File Here</div>
                        <div class="file-upload-sub">Accepted Formats: PDF or Plain Text (.txt)</div>
                    </div>

                    <button type="submit" class="btn-emerald">Submit Candidate Application</button>
                </form>

                <div id="candResult" class="response-box"></div>
            </div>
        </div>

        <script>
            let allJobsList = [];
            let currentSelectedJob = null;

            function triggerFileInput() {{
                document.getElementById('candResumeFile').click();
            }}

            function updateFileName(input) {{
                const label = document.getElementById('fileUploadLabel');
                if (input.files && input.files.length > 0) {{
                    label.textContent = "Selected File: " + input.files[0].name;
                }} else {{
                    label.textContent = "Click or Drag PDF / TXT Resume File Here";
                }}
            }}

            async function loadJobsDropdown() {{
                try {{
                    const res = await fetch('/api/jobs-history');
                    const data = await res.json();
                    allJobsList = data.jobs || [];

                    const selector = document.getElementById('jobSelector');
                    selector.innerHTML = '';

                    allJobsList.forEach(j => {{
                        const opt = document.createElement('option');
                        opt.value = j.id;
                        opt.textContent = `${{j.title}} (${{j.job_type || 'Full-Time'}}) - Posted ${{j.posted_at || ''}}`;
                        selector.appendChild(opt);
                    }});

                    if (allJobsList.length > 0) {{
                        currentSelectedJob = allJobsList[0];
                        renderSelectedJobDetails(currentSelectedJob);
                    }}
                }} catch(e) {{}}
            }}

            function onJobSelectChange() {{
                const selectedId = parseInt(document.getElementById('jobSelector').value);
                const found = allJobsList.find(j => j.id === selectedId);
                if (found) {{
                    currentSelectedJob = found;
                    renderSelectedJobDetails(found);
                }}
            }}

            function renderSelectedJobDetails(job) {{
                document.getElementById('displayJobTitle').innerText = job.title;
                document.getElementById('displayJobDesc').innerText = job.description;

                const meta = document.getElementById('displayMetaBadges');
                meta.innerHTML = `
                    <span class="tag-badge tag-blue">Min Experience: ${{job.required_experience_years || 3}}+ Years</span>
                    <span class="tag-badge tag-blue">Required Degree: ${{job.required_education || "Bachelor's"}}</span>
                    <span class="tag-badge tag-blue">Employment Mode: ${{job.job_type || "Remote"}}</span>
                `;

                const container = document.getElementById('displaySkillsTags');
                const skills = job.required_skills || job.skills || [];
                container.innerHTML = '<strong style="font-size:0.82rem; color:var(--text-muted);">Required Skills:</strong><br>';
                skills.forEach(s => {{
                    container.innerHTML += `<span class="tag-badge tag-blue">${{s.toUpperCase()}}</span>`;
                }});
            }}

            loadJobsDropdown();

            async function handleCandidateSubmit(e) {{
                e.preventDefault();
                const name = document.getElementById('candName').value;
                const email = document.getElementById('candEmail').value;
                const fileInput = document.getElementById('candResumeFile');
                const resBox = document.getElementById('candResult');

                if (!fileInput.files || fileInput.files.length === 0) {{
                    alert('Please select a PDF or TXT resume file to upload.');
                    return;
                }}

                resBox.style.display = 'block';
                resBox.innerText = 'Uploading resume PDF and evaluating candidate via Gemini AI...';

                const formData = new FormData();
                formData.append('full_name', name);
                formData.append('email', email);
                if (currentSelectedJob) {{
                    formData.append('job_id', currentSelectedJob.id);
                    formData.append('job_title_input', currentSelectedJob.title);
                }}
                formData.append('resume_file', fileInput.files[0]);

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
        <title>HR Administration Panel & ATS Dashboard</title>
        {CORPORATE_STYLE}
    </head>
    <body>
        <div class="navbar">
            <a href="/" class="navbar-brand">Enterprise AI <span>Recruitment</span></a>
            <div class="nav-links">
                <a href="/admin" class="nav-link active">HR Administration</a>
                <a href="/apply" class="nav-link">Candidate Application</a>
                <a href="/docs" class="nav-link" target="_blank">API Documentation</a>
            </div>
        </div>

        <div class="main-wrapper">
            <div class="page-header">
                <h1>HR Administration Panel & ATS Dashboard</h1>
                <p>Manage job vacancies, track candidate application scores, and review AI evaluation reasons.</p>
            </div>

            <!-- Metrics Row -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="label">Total Job Vacancies</div>
                    <div class="value" id="statVacancies">1</div>
                </div>
                <div class="metric-card">
                    <div class="label">Received Applications</div>
                    <div class="value" id="statApps">0</div>
                </div>
                <div class="metric-card">
                    <div class="label">Shortlisted Candidates</div>
                    <div class="value" id="statShortlisted">0</div>
                </div>
                <div class="metric-card">
                    <div class="label">Gemini AI Engine</div>
                    <div class="value" style="font-size:1.15rem; color:var(--emerald-primary); margin-top:6px;">Active</div>
                </div>
            </div>

            <!-- Publish Vacancy -->
            <div class="card">
                <div class="card-header">
                    <span>Create & Publish Job Vacancy</span>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label>Job Position Title:</label>
                        <input type="text" id="adminTitle" value="Senior DevOps & Cloud Architect">
                    </div>
                    <div>
                        <label>Employment Mode / Location:</label>
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
                <input type="text" id="adminDesc" value="We are seeking a DevOps Architect with 3+ years experience to manage cloud infrastructure, containers, and automated deployment pipelines.">

                <label>Required Technical Stack (Comma Separated):</label>
                <input type="text" id="adminSkills" value="Python, Docker, Kubernetes, AWS, Terraform, CI/CD, Linux">

                <button class="btn-emerald" onclick="publishNewJob()">Publish Job Vacancy</button>
                <div id="adminResult" class="response-box"></div>
            </div>

            <!-- Applications ATS Table -->
            <div class="card">
                <div class="card-header">
                    <span>Applicant Tracking System (ATS)</span>
                    <button onclick="loadDashboardData()" style="background:#F1F5F9; color:var(--text-main); border:1px solid #CBD5E1; padding:6px 12px; border-radius:6px; font-size:0.82rem; font-weight:600; cursor:pointer;">Refresh List</button>
                </div>

                <div style="margin-bottom:14px;">
                    <input type="text" id="searchFilter" onkeyup="filterApplications()" placeholder="Filter candidate applications by name, position, or reasons..." style="margin-bottom:0;">
                </div>

                <div id="appsTableContainer">
                    <p style="color:var(--text-muted);">Loading applications...</p>
                </div>
            </div>

            <!-- Job History Archive -->
            <div class="card">
                <div class="card-header">
                    <span>Active & Past Job Vacancies Archive</span>
                </div>
                <div id="jobsHistoryContainer">
                    <p style="color:var(--text-muted);">Loading job postings...</p>
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
                resBox.innerText = 'Publishing job vacancy...';

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
                    resBox.innerText = 'Error publishing job requirements';
                }}
            }}

            function filterApplications() {{
                const query = document.getElementById('searchFilter').value.toLowerCase();
                const filtered = cachedApplications.filter(a => 
                    (a.candidate_name && a.candidate_name.toLowerCase().includes(query)) ||
                    (a.job_title && a.job_title.toLowerCase().includes(query)) ||
                    (a.ai_reasoning && a.ai_reasoning.toLowerCase().includes(query))
                );
                renderApplicationsTable(filtered);
            }}

            function renderApplicationsTable(apps) {{
                const container = document.getElementById('appsTableContainer');
                if (!apps || apps.length === 0) {{
                    container.innerHTML = '<p style="color:var(--text-muted); font-style:italic;">No candidate applications received yet.</p>';
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
                            <th>Evaluation Reasons</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>`;

                apps.forEach(a => {{
                    const badge = a.score >= 60 ? 
                        `<span class="tag-badge tag-success">Shortlisted (${{a.score}}%)</span>` : 
                        `<span class="tag-badge tag-danger">Rejected (${{a.score}}%)</span>`;
                        
                    const docBadge = a.is_genuine_resume ?
                        `<span style="color:#059669; font-weight:600;">Valid CV</span>` :
                        `<span style="color:#991B1B; font-weight:bold;">Invalid Document</span>`;

                    const reasoningText = a.ai_reasoning || 'Evaluated suitability based on requirements.';

                    html += `<tr>
                        <td><strong>${{a.candidate_name}}</strong><br><small style="color:var(--text-muted);">${{a.email}}</small></td>
                        <td><strong>${{a.job_title}}</strong></td>
                        <td>${{a.detected_experience_years !== undefined ? a.detected_experience_years + ' yrs' : 'N/A'}}</td>
                        <td>${{a.detected_education || 'N/A'}}</td>
                        <td>${{docBadge}}</td>
                        <td><strong style="font-size:1.05rem;">${{a.score}}%</strong></td>
                        <td style="max-width:280px; font-size:0.83rem; color:var(--text-muted);">${{reasoningText}}</td>
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
                    document.getElementById('statApps').innerText = cachedApplications.length;
                    const shortlisted = cachedApplications.filter(a => a.score >= 60).length;
                    document.getElementById('statShortlisted').innerText = shortlisted;
                    renderApplicationsTable(cachedApplications);
                }} catch(e) {{}}

                try {{
                    const res = await fetch('/api/jobs-history');
                    const data = await res.json();
                    const jobs = data.jobs || [];
                    document.getElementById('statVacancies').innerText = jobs.length;
                    const container = document.getElementById('jobsHistoryContainer');

                    if (jobs.length === 0) {{
                        container.innerHTML = '<p style="color:var(--text-muted);">No job history available.</p>';
                    }} else {{
                        let html = '';
                        jobs.forEach(j => {{
                            const skills = j.required_skills || j.skills || [];
                            const tags = skills.map(s => `<span class="tag-badge tag-blue">${{s.toUpperCase()}}</span>`).join(' ');
                            html += `<div style="background:#FFFFFF; border:1px solid var(--border-slate); border-radius:8px; padding:16px; margin-bottom:12px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0; font-family:'Plus Jakarta Sans'; color:var(--text-main);">${{j.title}} (${{j.job_type || 'Full-Time'}})</h4>
                                    <small style="color:var(--text-muted);">${{j.posted_at || ''}}</small>
                                </div>
                                <div style="color:var(--emerald-primary); font-size:0.82rem; font-weight:600; margin:4px 0;">
                                    Min Experience: ${{j.required_experience_years || 3}}+ Years | Required Degree: ${{j.required_education || "Bachelor's"}}
                                </div>
                                <p style="color:var(--text-muted); font-size:0.88rem; margin:6px 0 10px 0;">${{j.description}}</p>
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
        {CORPORATE_STYLE}
    </head>
    <body>
        <div class="navbar">
            <a href="/" class="navbar-brand">Enterprise AI <span>Recruitment</span></a>
            <div class="nav-links">
                <a href="/admin" class="nav-link">HR Administration</a>
                <a href="/apply" class="nav-link">Candidate Application</a>
                <a href="/docs" class="nav-link" target="_blank">API Documentation</a>
            </div>
        </div>

        <div class="main-wrapper" style="text-align:center;">
            <div class="page-header" style="margin-top:20px;">
                <h1>Enterprise AI Recruitment Platform</h1>
                <p>Select your operational destination below to manage vacancies or submit candidate applications.</p>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:32px;">
                <a href="/admin" style="text-decoration:none;">
                    <div class="card" style="height:100%; text-align:left; transition:transform 0.2s;">
                        <h2 style="font-size:1.3rem; margin:0 0 8px 0; color:var(--text-main);">HR Administration Panel</h2>
                        <p style="color:var(--text-muted); font-size:0.92rem; margin:0 0 16px 0;">Publish job openings, set technical requirements, and monitor real Gemini AI candidate ATS evaluation scores.</p>
                        <span class="tag-badge tag-success">Access Admin Panel &rarr;</span>
                    </div>
                </a>

                <a href="/apply" style="text-decoration:none;">
                    <div class="card" style="height:100%; text-align:left; transition:transform 0.2s;">
                        <h2 style="font-size:1.3rem; margin:0 0 8px 0; color:var(--text-main);">Candidate Application Portal</h2>
                        <p style="color:var(--text-muted); font-size:0.92rem; margin:0 0 16px 0;">Browse open vacancies, attach your candidate resume file (PDF or TXT), and submit for automated AI suitability analysis.</p>
                        <span class="tag-badge tag-blue">Access Candidate Portal &rarr;</span>
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
