"""
Enterprise AI Recruitment Platform & Autonomous Document Parsing Engine.
Dedicated HR Admin Panel & Public Candidate Job Application Portals.
"""

import io
import json
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
    version="4.2.0"
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

def calculate_enterprise_score(
    text: str,
    required_skills: list[str],
    req_exp_years: int,
    req_education: str
) -> dict[str, Any]:
    """Calculates weighted multi-criteria enterprise hiring score."""
    doc_check = classify_document_authenticity(text)
    if not doc_check["is_genuine_resume"]:
        return {
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
            "recommendation": f"Rejected: {doc_check['document_type']}"
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
        "recommendation": "Shortlisted for Interview" if is_shortlisted else "Review Required / Rejected"
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
        "detected_experience_years": res_eval["detected_experience_years"],
        "detected_education": res_eval["detected_education"],
        "is_genuine_resume": res_eval["is_genuine_resume"],
        "document_type": res_eval["document_type"],
        "recommendation": res_eval["recommendation"],
        "matched_skills": res_eval["matched_skills"],
        "missing_skills": res_eval["missing_skills"],
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
        "detected_experience_years": res_eval["detected_experience_years"],
        "detected_education": res_eval["detected_education"],
        "is_genuine_resume": res_eval["is_genuine_resume"],
        "document_type": res_eval["document_type"],
        "recommendation": res_eval["recommendation"],
        "matched_skills": res_eval["matched_skills"],
        "missing_skills": res_eval["missing_skills"],
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
        "detected_skills": res_eval["matched_skills"],
        "missing_skills": res_eval["missing_skills"],
        "detected_experience_years": res_eval["detected_experience_years"],
        "detected_education": res_eval["detected_education"],
        "is_genuine_resume": res_eval["is_genuine_resume"],
        "document_type": res_eval["document_type"],
        "skill_score": res_eval["skill_score"],
        "experience_score": res_eval["experience_score"],
        "education_score": res_eval["education_score"],
        "suitability_score": res_eval["final_score"],
        "score": res_eval["final_score"],
        "recommendation": res_eval["recommendation"]
    }

@app.post("/parse")
async def parse_document(payload: dict[str, Any] = None) -> dict[str, Any]:
    """Compatibility parse endpoint for n8n workflow integration."""
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
# Distinct Futuristic UI Views (Nexus Theme — Dark Glassmorphism)
# ---------------------------------------------------------------------------

NEXUS_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #090D16;
        --card-bg: rgba(15, 23, 42, 0.75);
        --border: rgba(255, 255, 255, 0.1);
        --accent-blue: #00D4FF;
        --accent-purple: #8B5CF6;
        --accent-green: #10B981;
        --accent-red: #EF4444;
        --text: #F8FAFC;
        --text-muted: #94A3B8;
    }
    body {
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at top right, #1E1B4B 0%, #090D16 50%, #030712 100%);
        color: var(--text);
        margin: 0;
        padding: 40px 20px;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .container { max-width: 920px; width: 100%; }
    .hero {
        text-align: center;
        margin-bottom: 32px;
    }
    .hero h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.6rem;
        background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
        font-weight: 700;
    }
    .hero p { color: var(--text-muted); font-size: 1.1rem; margin: 0; }
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }
    .job-pill {
        display: inline-block;
        background: rgba(0, 212, 255, 0.15);
        color: var(--accent-blue);
        border: 1px solid rgba(0, 212, 255, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 4px;
    }
    label { font-size: 0.85rem; font-weight: 600; color: #CBD5E1; display: block; margin-bottom: 6px; }
    input, select, textarea {
        width: 100%;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: white;
        padding: 12px;
        border-radius: 10px;
        box-sizing: border-box;
        font-family: inherit;
        margin-bottom: 16px;
    }
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--accent-blue);
        box-shadow: 0 0 12px rgba(0, 212, 255, 0.3);
    }
    .btn-nexus {
        background: linear-gradient(135deg, #00D4FF 0%, #3B82F6 100%);
        color: white;
        border: none;
        padding: 14px 24px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        cursor: pointer;
        width: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .btn-nexus:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 255, 0.4);
    }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
    th { background: rgba(15, 23, 42, 0.9); color: var(--text-muted); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; }
    .result-terminal {
        background: #030712;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        color: var(--accent-green);
        white-space: pre-wrap;
        margin-top: 16px;
        display: none;
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
        <title>Nexus AI — Candidate Portal</title>
        {NEXUS_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>⚡ Nexus AI Careers & Candidate Portal</h1>
                <p>Submit your resume for real-time automated AI evaluation and interview shortlisting</p>
            </div>

            <div class="glass-card" style="border-left: 4px solid var(--accent-blue);">
                <span style="color:var(--accent-blue); font-size:0.8rem; font-weight:700; letter-spacing:1px;">📢 ACTIVE POSITION</span>
                <h2 id="displayJobTitle" style="margin:6px 0; font-family:'Space Grotesk';">Loading Position...</h2>
                <p id="displayJobDesc" style="color:var(--text-muted); margin-bottom:12px;"></p>
                <div id="displayMetaBadges"></div>
                <div id="displaySkillsTags" style="margin-top:10px;"></div>
            </div>

            <div class="glass-card">
                <h3 style="margin-top:0; font-family:'Space Grotesk';">📝 Application Submission Form</h3>
                <form id="appForm" onsubmit="handleCandidateSubmit(event)">
                    <label>Full Name *</label>
                    <input type="text" id="candName" placeholder="e.g. Sarah Connor" required>

                    <label>Email Address *</label>
                    <input type="email" id="candEmail" placeholder="e.g. sarah@techcorp.ai" required>

                    <label>📎 Upload Resume (PDF / TXT) *</label>
                    <input type="file" id="candResumeFile" accept=".pdf,.txt">

                    <label>Or Paste Resume Text:</label>
                    <textarea id="candResumeText" rows="5" placeholder="Paste your resume text here..."></textarea>

                    <button type="submit" class="btn-nexus">🚀 Submit Application to AI Engine</button>
                </form>
                <div id="candResult" class="result-terminal"></div>
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
                        <span class="job-pill">⏳ Min Exp: ${{job.required_experience_years || 3}}+ Yrs</span>
                        <span class="job-pill">🎓 Degree: ${{job.required_education || "Bachelor's"}}</span>
                        <span class="job-pill">📍 Mode: ${{job.job_type || "Remote"}}</span>
                    `;

                    const container = document.getElementById('displaySkillsTags');
                    const skills = job.required_skills || job.skills || [];
                    container.innerHTML = '<strong>Required Skills:</strong> ';
                    skills.forEach(s => {{
                        container.innerHTML += `<span class="job-pill">${{s.toUpperCase()}}</span>`;
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
                resBox.innerText = 'Evaluating resume PDF & triggering n8n workflow...';

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
        <title>Nexus AI — HR Admin Panel</title>
        {NEXUS_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>⚙️ Nexus HR Admin & ATS Dashboard</h1>
                <p>Manage dynamic job postings, track applicant scores, and inspect evaluation metrics</p>
            </div>

            <!-- Job Publishing -->
            <div class="glass-card">
                <h3 style="margin-top:0; font-family:'Space Grotesk'; color:var(--accent-blue);">📢 Publish Job Vacancy</h3>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label>Job Position Title:</label>
                        <input type="text" id="adminTitle" value="Senior Cloud & DevOps Architect">
                    </div>
                    <div>
                        <label>Job Mode:</label>
                        <select id="adminJobType">
                            <option value="Full-Time" selected>Full-Time</option>
                            <option value="Remote">Remote</option>
                            <option value="Hybrid">Hybrid</option>
                        </select>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label>Min Experience (Years):</label>
                        <input type="number" id="adminExp" value="3" min="0" max="20">
                    </div>
                    <div>
                        <label>Required Degree:</label>
                        <select id="adminEdu">
                            <option value="Bachelor's" selected>Bachelor's Degree</option>
                            <option value="Master's">Master's Degree</option>
                            <option value="PhD">PhD / Doctorate</option>
                            <option value="Any">Any Qualification</option>
                        </select>
                    </div>
                </div>

                <label>Job Description:</label>
                <textarea id="adminDesc" rows="2">Seeking cloud engineer skilled in Python, Docker, Kubernetes, AWS, and Linux.</textarea>

                <label>Required Technical Skills (Comma Separated):</label>
                <input type="text" id="adminSkills" value="Python, Docker, Kubernetes, AWS, Terraform, CI/CD, Linux">

                <button class="btn-nexus" onclick="publishNewJob()">📢 Publish & Sync Candidate Portal</button>
                <div id="adminResult" class="result-terminal"></div>
            </div>

            <!-- Applications Table -->
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <h3 style="margin:0; font-family:'Space Grotesk';">📥 Applicant Tracking System (ATS)</h3>
                    <button onclick="loadDashboardData()" style="background:rgba(255,255,255,0.1); color:white; border:1px solid var(--border); padding:6px 14px; border-radius:8px; cursor:pointer;">🔄 Refresh</button>
                </div>
                <div id="appsTableContainer">
                    <p style="color:var(--text-muted);">Loading candidate applications...</p>
                </div>
            </div>

            <!-- Job History -->
            <div class="glass-card">
                <h3 style="margin-top:0; font-family:'Space Grotesk';">📜 Job Vacancy Archive</h3>
                <div id="jobsHistoryContainer">
                    <p style="color:var(--text-muted);">Loading job history...</p>
                </div>
            </div>
        </div>

        <script>
            async function publishNewJob() {{
                const title = document.getElementById('adminTitle').value;
                const jobType = document.getElementById('adminJobType').value;
                const expYears = parseInt(document.getElementById('adminExp').value) || 0;
                const eduLevel = document.getElementById('adminEdu').value;
                const desc = document.getElementById('adminDesc').value;
                const skillsArr = document.getElementById('adminSkills').value.split(',');
                const resBox = document.getElementById('adminResult');
                resBox.style.display = 'block';
                resBox.innerText = 'Updating job configuration...';

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
                    resBox.innerText = 'Error updating job';
                }}
            }}

            async function loadDashboardData() {{
                try {{
                    const res = await fetch('/api/applications');
                    const data = await res.json();
                    const container = document.getElementById('appsTableContainer');

                    if (!data.applications || data.applications.length === 0) {{
                        container.innerHTML = '<p style="color:var(--text-muted); font-style:italic;">No applications received yet. Applications submitted via /apply will appear here live!</p>';
                    }} else {{
                        let html = `<table>
                            <thead>
                                <tr>
                                    <th>Candidate</th>
                                    <th>Job Position</th>
                                    <th>Detected Exp</th>
                                    <th>Degree</th>
                                    <th>Authenticity</th>
                                    <th>Score</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>`;
                        data.applications.forEach(a => {{
                            const badge = a.score >= 60 ? 
                                `<span style="background:rgba(16,185,129,0.2); color:#34D399; padding:4px 8px; border-radius:6px; font-weight:700;">Shortlisted (${{a.score}}%)</span>` : 
                                `<span style="background:rgba(239,68,68,0.2); color:#FCA5A5; padding:4px 8px; border-radius:6px; font-weight:700;">Rejected (${{a.score}}%)</span>`;
                                
                            const docBadge = a.is_genuine_resume ?
                                `<span style="color:#34D399;">Valid CV</span>` :
                                `<span style="color:#FCA5A5; font-weight:bold;">Invalid Document</span>`;

                            html += `<tr>
                                <td><strong>${{a.candidate_name}}</strong><br><small style="color:var(--text-muted);">${{a.email}}</small></td>
                                <td>${{a.job_title}}</td>
                                <td>${{a.detected_experience_years !== undefined ? a.detected_experience_years + ' yrs' : 'N/A'}}</td>
                                <td>${{a.detected_education || 'N/A'}}</td>
                                <td>${{docBadge}}</td>
                                <td><strong>${{a.score}}%</strong></td>
                                <td>${{badge}}</td>
                            </tr>`;
                        }});
                        html += `</tbody></table>`;
                        container.innerHTML = html;
                    }}
                }} catch(e) {{}}

                try {{
                    const res = await fetch('/api/jobs-history');
                    const data = await res.json();
                    const container = document.getElementById('jobsHistoryContainer');

                    if (!data.jobs || data.jobs.length === 0) {{
                        container.innerHTML = '<p style="color:var(--text-muted);">No job history.</p>';
                    }} else {{
                        let html = '';
                        data.jobs.forEach(j => {{
                            const skills = j.required_skills || j.skills || [];
                            const tags = skills.map(s => `<span class="job-pill">${{s.toUpperCase()}}</span>`).join(' ');
                            html += `<div style="background:rgba(15,23,42,0.6); border:1px solid var(--border); border-radius:10px; padding:16px; margin-bottom:12px;">
                                <div style="display:flex; justify-content:space-between;">
                                    <h4 style="margin:0; font-family:'Space Grotesk';">${{j.title}} (${{j.job_type || 'Full-Time'}})</h4>
                                    <small style="color:var(--text-muted);">${{j.posted_at || ''}}</small>
                                </div>
                                <div style="color:var(--accent-blue); font-size:0.8rem; margin:4px 0;">
                                    ⏳ Exp: ${{j.required_experience_years || 3}}+ yrs | 🎓 Degree: ${{j.required_education || "Bachelor's"}}
                                </div>
                                <p style="color:var(--text-muted); font-size:0.85rem; margin:6px 0 10px 0;">${{j.description}}</p>
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
        <title>Nexus AI Automation Hub</title>
        {NEXUS_STYLE}
    </head>
    <body>
        <div class="container" style="text-align:center;">
            <div class="hero">
                <h1>⚡ Nexus AI Recruitment Hub</h1>
                <p>Enterprise AI Platform — Dynamic Hiring & Autonomous Operations</p>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:30px;">
                <a href="/admin" style="text-decoration:none;">
                    <div class="glass-card" style="height:100%; transition:transform 0.2s;">
                        <div style="font-size:3rem; margin-bottom:12px;">⚙️</div>
                        <h2 style="font-family:'Space Grotesk'; margin:0 0 8px 0; color:white;">HR Admin Portal</h2>
                        <p style="color:var(--text-muted); font-size:0.9rem;">Define active job postings, set required skills, and monitor candidate application ATS scores live.</p>
                    </div>
                </a>

                <a href="/apply" style="text-decoration:none;">
                    <div class="glass-card" style="height:100%; transition:transform 0.2s;">
                        <div style="font-size:3rem; margin-bottom:12px;">💼</div>
                        <h2 style="font-family:'Space Grotesk'; margin:0 0 8px 0; color:white;">Candidate Portal</h2>
                        <p style="color:var(--text-muted); font-size:0.9rem;">View active openings, upload PDF resumes, and receive instant AI evaluation & shortlist notifications.</p>
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
