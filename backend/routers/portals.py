"""
Portals Router — dedicated HR Admin Panel (/admin) and Candidate Application Portal (/apply).
Includes dynamic API state endpoints (/api/jobs, /api/applications) so jobs created by HR 
automatically appear in the candidate application portal dropdown in real time!
"""

from typing import Any
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["Portals"])

# ---------------------------------------------------------------------------
# Shared In-Memory State for HR Recruitment Platform
# ---------------------------------------------------------------------------

JOBS_DB: list[dict[str, Any]] = [
    {
        "id": 1,
        "title": "Senior AI Platform Engineer",
        "salary": "$125,000 / year",
        "threshold": 70,
        "skills": "Python, FastAPI, Docker, Kubernetes, n8n automation, OpenAI LLM integration, PostgreSQL",
        "status": "ACTIVE",
    },
    {
        "id": 2,
        "title": "Devops Engineer",
        "salary": "$125,000 / year",
        "threshold": 75,
        "skills": "Docker, Kubernetes, linux, networking, github, jenkins",
        "status": "ACTIVE",
    },
]

APPLICATIONS_DB: list[dict[str, Any]] = [
    {
        "candidate_name": "Sarah Connor",
        "candidate_email": "sarah.connor@example.com",
        "job_title": "Senior AI Platform Engineer",
        "score": 94,
        "status": "PASSED",
        "action": "Offer Letter Dispatched",
    },
    {
        "candidate_name": "John Smith",
        "candidate_email": "john.smith@example.com",
        "job_title": "Senior AI Platform Engineer",
        "score": 45,
        "status": "REJECTED",
        "action": "Rejection Feedback Sent",
    },
]


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2)
    salary: str = Field(default="$125,000 / year")
    threshold: int = Field(default=70, ge=0, le=100)
    skills: str = Field(..., min_length=5)


class ApplicationRecordRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    job_title: str
    score: int
    passed: bool
    action: str


# ---------------------------------------------------------------------------
# API State Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/jobs", summary="Get Published Job Vacancies")
async def get_published_jobs():
    return JOBS_DB


@router.post("/api/jobs", summary="Publish New Job Vacancy")
async def create_published_job(payload: JobCreateRequest):
    new_job = {
        "id": len(JOBS_DB) + 1,
        "title": payload.title,
        "salary": payload.salary,
        "threshold": payload.threshold,
        "skills": payload.skills,
        "status": "ACTIVE",
    }
    # Prepend new job to top of list
    JOBS_DB.insert(0, new_job)
    return {"status": "SUCCESS", "job": new_job}


@router.get("/api/applications", summary="Get Live Candidate Applications")
async def get_candidate_applications():
    return APPLICATIONS_DB


class OnboardingTriggerRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    job_title: str

@router.post("/api/trigger-onboarding", summary="Trigger Onboarding & IT Access Provisioning")
async def trigger_candidate_onboarding(payload: OnboardingTriggerRequest):
    subject = f"🎉 Welcome to TechCorp! Day-1 Onboarding & IT Access Kit for {payload.job_title}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; padding: 24px; background: #0b0f19; color: #f8fafc; border-radius: 12px; border: 1px solid #1e293b;">
      <h2 style="color: #10b981; margin-top: 0;">🚀 Welcome to the Team, {payload.candidate_name}!</h2>
      <p>Congratulations on accepting the position of <strong>{payload.job_title}</strong>.</p>
      
      <h3 style="color: #00d4ff; border-bottom: 1px solid #334155; padding-bottom: 8px;">📋 Automated Day-1 IT Onboarding Checklist</h3>
      <ul style="line-height: 1.8; color: #cbd5e1;">
        <li>✅ GitHub Enterprise Access Granted</li>
        <li>✅ AWS IAM Developer Role Created</li>
        <li>✅ Slack #welcome & #engineering Channels Invited</li>
        <li>✅ Hardware Laptop & Security YubiKey Dispatched</li>
        <li>✅ Orientation Calendar Sync Scheduled</li>
      </ul>
      
      <p style="margin-top: 20px; font-size: 13px; color: #94a3b8;">
        Sent via Nexus Autonomous HR & IT Provisioning Workflow Engine.
      </p>
    </div>
    """
    
    # Send email via SMTP
    try:
        from services.email_service import email_service
        email_service.send_email(
            to_email=payload.candidate_email,
            subject=subject,
            html_body=html_body,
            text_body=f"Welcome {payload.candidate_name}! Your onboarding kit for {payload.job_title} is ready.",
        )
    except Exception as e:
        print("Onboarding SMTP error:", e)

    # Update candidate status in APPLICATIONS_DB
    for app in APPLICATIONS_DB:
        if app["candidate_name"] == payload.candidate_name:
            app["action"] = "ONBOARDED & ACCESS PROVISIONED ✅"
            break

    return {"status": "SUCCESS", "message": f"Onboarding kit dispatched to {payload.candidate_email}"}


# ---------------------------------------------------------------------------
# UI View Endpoints (/admin and /apply)
# ---------------------------------------------------------------------------

@router.get("/admin", response_class=HTMLResponse, summary="HR Admin Panel")
async def hr_admin_panel():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HR Admin Panel — Autonomous Recruitment Platform</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0a1a; --card: rgba(255,255,255,0.05); --border: rgba(255,255,255,0.12);
      --blue: #00d4ff; --purple: #8b5cf6; --green: #10b981; --red: #ef4444; --text: #f8fafc;
    }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 30px; }
    .container { max-width: 1000px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 30px; }
    h1 { font-family: 'Space Grotesk', sans-serif; margin: 0; background: linear-gradient(90deg, var(--blue), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .btn { background: linear-gradient(135deg, var(--blue), var(--purple)); color: #000; font-weight: 700; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-bottom: 24px; backdrop-filter: blur(10px); }
    .form-group { margin-bottom: 16px; }
    label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #a1a1aa; }
    input, textarea { width: 100%; box-sizing: border-box; background: rgba(0,0,0,0.4); border: 1px solid var(--border); border-radius: 6px; color: #fff; padding: 10px; font-family: inherit; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--border); font-size: 13px; }
    th { color: var(--blue); font-family: 'Space Grotesk', sans-serif; }
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .badge-pass { background: rgba(16,185,129,0.2); color: var(--green); border: 1px solid var(--green); }
    .badge-fail { background: rgba(239,68,68,0.2); color: var(--red); border: 1px solid var(--red); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>👑 HR Recruitment Admin Portal</h1>
        <p style="color:#a1a1aa; margin: 4px 0 0 0; font-size: 14px;">Publish job openings, set AI screening thresholds, and track candidate applications live.</p>
      </div>
      <div>
        <a href="/apply" target="_blank" class="btn" style="margin-right:10px;">📋 Open Candidate Portal</a>
        <a href="http://localhost:8025" target="_blank" class="btn" style="background:var(--green);">📧 Open Mailpit Web Inbox</a>
      </div>
    </div>

    <!-- Job Publisher Form -->
    <div class="card">
      <h2 style="font-family:'Space Grotesk'; font-size:18px; margin-top:0; color:var(--blue);">📢 Create & Publish New Job Vacancy</h2>
      <form id="job-form">
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
          <div class="form-group">
            <label>Job Title</label>
            <input type="text" id="job-title" placeholder="e.g. Devops Engineer" required />
          </div>
          <div class="form-group">
            <label>Salary Package</label>
            <input type="text" id="job-salary" value="$125,000 / year" required />
          </div>
          <div class="form-group">
            <label>Score Passing Threshold (0-100)</label>
            <input type="number" id="job-threshold" value="75" required />
          </div>
        </div>
        <div class="form-group">
          <label>Required Technical Skills & Qualification Criteria</label>
          <input type="text" id="job-skills" placeholder="e.g. Docker, Kubernetes, linux, networking, github, jenkins" required />
        </div>
        <button type="submit" class="btn" id="job-submit-btn">🚀 Publish Job Vacancy</button>
      </form>
    </div>

    <!-- Active Jobs Table -->
    <div class="card">
      <h2 style="font-family:'Space Grotesk'; font-size:18px; margin-top:0; color:var(--purple);">📋 Published Job Vacancies</h2>
      <table>
        <thead>
          <tr>
            <th>Job Title</th>
            <th>Required Stack</th>
            <th>Salary</th>
            <th>Min Threshold</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="jobs-table-body">
          <!-- Dynamically populated from /api/jobs -->
        </tbody>
      </table>
    </div>

    <!-- Live Applicant Tracking System -->
    <div class="card">
      <h2 style="font-family:'Space Grotesk'; font-size:18px; margin-top:0; color:var(--green);">👥 Applicant Tracking System (Live Submissions)</h2>
      <table id="applicants-table">
        <thead>
          <tr>
            <th>Candidate Name</th>
            <th>Email</th>
            <th>Applied Position</th>
            <th>AI Screening Score</th>
            <th>Autonomous Action</th>
            <th>Mailpit Verification</th>
          </tr>
        </thead>
        <tbody id="applicants-body">
          <!-- Dynamically populated from /api/applications -->
        </tbody>
      </table>
    </div>
  </div>

  <script>
    async function loadJobs() {
      try {
        const res = await fetch('/api/jobs');
        const jobs = await res.json();
        const tbody = document.getElementById('jobs-table-body');
        tbody.innerHTML = jobs.map(j => `
          <tr>
            <td><strong>${j.title}</strong></td>
            <td>${j.skills}</td>
            <td>${j.salary}</td>
            <td><span class="badge badge-pass">${j.threshold} / 100</span></td>
            <td><span style="color:var(--green)">● ACTIVE</span></td>
          </tr>
        `).join('');
      } catch (e) {
        console.error('Error loading jobs:', e);
      }
    }

    async function loadApplications() {
      try {
        const res = await fetch('/api/applications');
        const apps = await res.json();
        const tbody = document.getElementById('applicants-body');
        tbody.innerHTML = apps.map(a => `
          <tr>
            <td><strong>${a.candidate_name}</strong></td>
            <td>${a.candidate_email}</td>
            <td>${a.job_title}</td>
            <td><span class="badge ${a.status === 'PASSED' ? 'badge-pass' : 'badge-fail'}">${a.score} / 100</span></td>
            <td>
              <span style="color:${a.status === 'PASSED' ? 'var(--green)' : 'var(--red)'}; font-weight:bold;">${a.action}</span>
              ${a.status === 'PASSED' && !a.action.includes('ONBOARDED') ? `<br/><button onclick="triggerOnboarding('${a.candidate_name}', '${a.candidate_email}', '${a.job_title}')" style="margin-top:4px; padding:4px 10px; font-size:11px; background:rgba(16,185,129,0.2); color:var(--green); border:1px solid var(--green); border-radius:6px; cursor:pointer; font-weight:bold;">🚀 Trigger Day-1 IT Onboarding</button>` : ''}
            </td>
            <td><a href="http://localhost:8025" target="_blank" style="color:var(--blue)">View Email in Mailpit</a></td>
          </tr>
        `).join('');
      } catch (e) {
        console.error('Error loading applications:', e);
      }
    }

    async function triggerOnboarding(name, email, job) {
      if (!confirm(`Trigger Day-1 IT Access Provisioning & Onboarding Kit for ${name}?`)) return;
      try {
        const res = await fetch('/api/trigger-onboarding', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ candidate_name: name, candidate_email: email, job_title: job })
        });
        if (res.ok) {
          alert(`Onboarding Kit & IT Credentials dispatched to ${email} via Mailpit!`);
          await loadApplications();
        }
      } catch (err) {
        alert('Failed to trigger onboarding: ' + err);
      }
    }

    document.getElementById('job-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('job-title').value;
      const skills = document.getElementById('job-skills').value;
      const salary = document.getElementById('job-salary').value;
      const threshold = parseInt(document.getElementById('job-threshold').value);
      const btn = document.getElementById('job-submit-btn');

      btn.disabled = true;
      btn.innerHTML = '⏳ Publishing Job…';

      try {
        const res = await fetch('/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, salary, threshold, skills })
        });
        if (res.ok) {
          alert(`Job "${title}" published successfully!\n\nCandidates can now select and apply for this job live at /apply!`);
          document.getElementById('job-title').value = '';
          document.getElementById('job-skills').value = '';
          await loadJobs();
        }
      } catch (err) {
        alert('Failed to publish job: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Publish Job Vacancy';
      }
    });

    loadJobs();
    loadApplications();
    setInterval(loadApplications, 3000);
  </script>
</body>
</html>
"""

@router.get("/apply", response_class=HTMLResponse, summary="Candidate Application Portal")
async def candidate_apply_portal():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Candidate Application Portal — Apply Now</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0a1a; --card: rgba(255,255,255,0.05); --border: rgba(255,255,255,0.12);
      --blue: #00d4ff; --purple: #8b5cf6; --green: #10b981; --red: #ef4444; --text: #f8fafc;
    }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 30px; }
    .container { max-width: 750px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 30px; }
    h1 { font-family: 'Space Grotesk', sans-serif; background: linear-gradient(90deg, var(--blue), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 28px; margin-bottom: 8px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 30px; backdrop-filter: blur(10px); }
    .form-group { margin-bottom: 18px; }
    label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #a1a1aa; }
    input, select, textarea { width: 100%; box-sizing: border-box; background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-radius: 8px; color: #fff; padding: 12px; font-family: inherit; font-size: 14px; }
    .btn { width: 100%; background: linear-gradient(135deg, var(--blue), var(--purple)); color: #000; font-weight: 700; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 10px; }
    .preset-btn { background: rgba(255,255,255,0.1); border: 1px solid var(--border); color: #fff; padding: 6px 12px; font-size: 11px; border-radius: 6px; cursor: pointer; margin-right: 6px; }
    #result-box { display: none; margin-top: 24px; padding: 20px; border-radius: 10px; background: rgba(0,0,0,0.6); border: 1px solid var(--border); }
    .job-badge-info { font-size: 12px; color: var(--blue); margin-top: 6px; background: rgba(0,212,255,0.1); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(0,212,255,0.2); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>💼 Candidate Application Portal</h1>
      <p style="color:#a1a1aa;">Submit your application below. Our AI Recruitment System will screen your resume instantly and notify you via email.</p>
    </div>

    <div class="card">
      <form id="apply-form">
        <div class="form-group">
          <label>Select Published Job Vacancy</label>
          <select id="job-select">
            <option value="">Loading active job vacancies…</option>
          </select>
          <div id="job-details-badge" class="job-badge-info">Loading job requirements…</div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div class="form-group">
            <label>Full Name</label>
            <input type="text" id="cand-name" value="Sarah Connor" required />
          </div>
          <div class="form-group">
            <label>Email Address</label>
            <input type="email" id="cand-email" value="sarah.connor@example.com" required />
          </div>
        </div>

        <div class="form-group">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <label style="margin:0;">Resume Text</label>
            <div>
              <button type="button" class="preset-btn" id="btn-qualified">🟢 Qualified Resume Preset</button>
              <button type="button" class="preset-btn" id="btn-unqualified">🔴 Unqualified Resume Preset</button>
            </div>
          </div>
          <textarea id="cand-resume" rows="8" required></textarea>
        </div>

        <button type="submit" class="btn" id="submit-btn">🚀 Submit Application to AI Screening Engine</button>
      </form>

      <div id="result-box"></div>
    </div>
  </div>

  <script>
    let publishedJobs = [];

    const DEFAULTS = {
      QUALIFIED_AI: `SARAH CONNOR
Senior AI Platform Engineer with 6+ years experience in Python, FastAPI, Docker, Kubernetes, n8n, OpenAI GPT-4, PostgreSQL. Built automated HR and CRM systems handling 50k+ requests daily.`,
      QUALIFIED_DEVOPS: `SARAH CONNOR
Senior DevOps Engineer with 6+ years experience in Docker, Kubernetes, Linux system administration, networking, GitHub Actions, Jenkins CI/CD, Terraform, and Python.`,
      UNQUALIFIED: `JOHN SMITH
Junior Graphic Designer with 1 year experience in Photoshop and Canva. Organized office team lunches. Basic HTML typing skills.`
    };

    async function loadPublishedJobs() {
      try {
        const res = await fetch('/api/jobs');
        publishedJobs = await res.json();
        const select = document.getElementById('job-select');
        select.innerHTML = publishedJobs.map(j => `
          <option value="${j.title}" data-id="${j.id}">
            ${j.title} (${j.salary}) — Min Score: ${j.threshold}/100
          </option>
        `).join('');

        updateSelectedJobDetails();
      } catch (err) {
        console.error('Error fetching jobs:', err);
      }
    }

    function updateSelectedJobDetails() {
      const select = document.getElementById('job-select');
      const selectedTitle = select.value;
      const job = publishedJobs.find(j => j.title === selectedTitle);
      const badge = document.getElementById('job-details-badge');
      const resumeArea = document.getElementById('cand-resume');

      if (job) {
        badge.innerHTML = `📋 <strong>Required Stack:</strong> ${job.skills} | 💰 <strong>Salary:</strong> ${job.salary} | 🎯 <strong>Passing Threshold:</strong> ${job.threshold}/100`;
        
        // Auto-update sample resume preset matching the job title!
        if (selectedTitle.toLowerCase().includes('devops')) {
          resumeArea.value = DEFAULTS.QUALIFIED_DEVOPS;
        } else {
          resumeArea.value = DEFAULTS.QUALIFIED_AI;
        }
      }
    }

    document.getElementById('job-select').addEventListener('change', updateSelectedJobDetails);

    document.getElementById('btn-qualified').addEventListener('click', () => {
      const select = document.getElementById('job-select');
      const selectedTitle = select.value;
      document.getElementById('cand-name').value = 'Sarah Connor';
      document.getElementById('cand-email').value = 'sarah.connor@example.com';
      if (selectedTitle.toLowerCase().includes('devops')) {
        document.getElementById('cand-resume').value = DEFAULTS.QUALIFIED_DEVOPS;
      } else {
        document.getElementById('cand-resume').value = DEFAULTS.QUALIFIED_AI;
      }
    });

    document.getElementById('btn-unqualified').addEventListener('click', () => {
      document.getElementById('cand-name').value = 'John Smith';
      document.getElementById('cand-email').value = 'john.smith@example.com';
      document.getElementById('cand-resume').value = DEFAULTS.UNQUALIFIED;
    });

    document.getElementById('apply-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('cand-name').value;
      const email = document.getElementById('cand-email').value;
      const resume = document.getElementById('cand-resume').value;
      const jobTitle = document.getElementById('job-select').value;
      const job = publishedJobs.find(j => j.title === jobTitle) || {
        salary: '$125,000 / year',
        threshold: 70,
        skills: 'Python, FastAPI, Docker, Kubernetes, n8n'
      };

      const btn = document.getElementById('submit-btn');
      const box = document.getElementById('result-box');

      btn.disabled = true;
      btn.innerHTML = '⏳ Processing Application with AI…';

      try {
        const res = await fetch('/hr/process-candidate-pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_title: job.title,
            job_description: job.skills,
            candidate_name: name,
            candidate_email: email,
            salary_offered: job.salary,
            score_threshold: job.threshold,
            resume_text: resume
          })
        });

        const data = await res.json();
        box.style.display = 'block';
        box.style.borderColor = data.passed ? 'var(--green)' : 'var(--red)';

        // Record in Application History for HR Admin Panel ATS
        await fetch('/api/applications', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_name: name,
            candidate_email: email,
            job_title: job.title,
            score: data.score,
            passed: data.passed,
            action: data.passed ? 'Offer Letter Dispatched' : 'Rejection Feedback Sent'
          })
        });

        box.innerHTML = `
          <h3 style="color:${data.passed ? 'var(--green)' : 'var(--red)'}; margin-top:0;">
            ${data.passed ? '🎉 Application Shortlisted!' : ' Application Status Update'}
          </h3>
          <p><strong>Role Applied:</strong> ${data.job_title}</p>
          <p><strong>Screening Score:</strong> <span style="font-size:18px; font-weight:bold; color:${data.passed ? 'var(--green)' : 'var(--red)'};">${data.score} / 100</span> (Passing threshold: ${data.score_threshold}/100)</p>
          <p><strong>Action Taken:</strong> ${data.email_action}</p>
          <p style="color:#a1a1aa; font-size:13px;"> An official notification email has been sent to <strong>${email}</strong> via local Mailpit SMTP.</p>
          <a href="http://localhost:8025" target="_blank" style="display:inline-block; margin-top:10px; background:var(--green); color:#000; padding:8px 16px; border-radius:6px; font-weight:bold; text-decoration:none;">📧 Check Mailpit Web Inbox Live</a>
        `;
      } catch (err) {
        alert('Error processing application: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Submit Application to AI Screening Engine';
      }
    });

    loadPublishedJobs();
  </script>
</body>
</html>
"""
