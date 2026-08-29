"""
Portals Router — dedicated HR Admin Panel (/admin) and Candidate Application Portal (/apply).
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Portals"])

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
            <input type="text" id="job-title" value="Senior AI Platform Engineer" required />
          </div>
          <div class="form-group">
            <label>Salary Package</label>
            <input type="text" id="job-salary" value="$125,000 / year" required />
          </div>
          <div class="form-group">
            <label>Score Passing Threshold (0-100)</label>
            <input type="number" id="job-threshold" value="70" required />
          </div>
        </div>
        <div class="form-group">
          <label>Required Technical Skills & Qualification Criteria</label>
          <input type="text" id="job-skills" value="Python, FastAPI, Docker, Kubernetes, n8n automation, OpenAI LLM integration, PostgreSQL" required />
        </div>
        <button type="submit" class="btn">🚀 Publish Job Vacancy</button>
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
          <tr>
            <td><strong>Senior AI Platform Engineer</strong></td>
            <td>Python, FastAPI, Docker, Kubernetes, n8n, OpenAI</td>
            <td>$125,000 / yr</td>
            <td><span class="badge badge-pass">70 / 100</span></td>
            <td><span style="color:var(--green)">● ACTIVE</span></td>
          </tr>
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
          <tr>
            <td><strong>Sarah Connor</strong></td>
            <td>sarah.connor@example.com</td>
            <td>Senior AI Platform Engineer</td>
            <td><span class="badge badge-pass">94 / 100</span></td>
            <td><span style="color:var(--green); font-weight:bold;">Offer Letter Dispatched</span></td>
            <td><a href="http://localhost:8025" target="_blank" style="color:var(--blue)">View Email in Mailpit</a></td>
          </tr>
          <tr>
            <td><strong>John Smith</strong></td>
            <td>john.smith@example.com</td>
            <td>Senior AI Platform Engineer</td>
            <td><span class="badge badge-fail">45 / 100</span></td>
            <td><span style="color:var(--red); font-weight:bold;">Rejection Feedback Sent</span></td>
            <td><a href="http://localhost:8025" target="_blank" style="color:var(--blue)">View Email in Mailpit</a></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    document.getElementById('job-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const title = document.getElementById('job-title').value;
      const skills = document.getElementById('job-skills').value;
      const salary = document.getElementById('job-salary').value;
      const threshold = document.getElementById('job-threshold').value;

      const tbody = document.getElementById('jobs-table-body');
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><strong>${title}</strong></td><td>${skills}</td><td>${salary}</td><td><span class="badge badge-pass">${threshold} / 100</span></td><td><span style="color:var(--green)">● ACTIVE</span></td>`;
      tbody.prepend(tr);
      alert(`Job "${title}" published successfully! Candidates can now apply at /apply`);
    });
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
          <label>Select Job Vacancy</label>
          <select id="job-select">
            <option value="Senior AI Platform Engineer">Senior AI Platform Engineer ($125,000/yr)</option>
          </select>
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
              <button type="button" class="preset-btn" id="btn-qualified">🟢 Preset: Qualified Candidate</button>
              <button type="button" class="preset-btn" id="btn-unqualified">🔴 Preset: Unqualified Candidate</button>
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
    const QUALIFIED = `SARAH CONNOR
Senior AI Platform Engineer with 6+ years experience in Python, FastAPI, Docker, Kubernetes, n8n, OpenAI GPT-4, PostgreSQL. Built automated HR and CRM systems handling 50k+ requests daily.`;

    const UNQUALIFIED = `JOHN SMITH
Junior Graphic Designer with 1 year experience in Photoshop and Canva. Organized office team lunches. Basic HTML typing skills.`;

    document.getElementById('cand-resume').value = QUALIFIED;

    document.getElementById('btn-qualified').addEventListener('click', () => {
      document.getElementById('cand-name').value = 'Sarah Connor';
      document.getElementById('cand-email').value = 'sarah.connor@example.com';
      document.getElementById('cand-resume').value = QUALIFIED;
    });

    document.getElementById('btn-unqualified').addEventListener('click', () => {
      document.getElementById('cand-name').value = 'John Smith';
      document.getElementById('cand-email').value = 'john.smith@example.com';
      document.getElementById('cand-resume').value = UNQUALIFIED;
    });

    document.getElementById('apply-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('cand-name').value;
      const email = document.getElementById('cand-email').value;
      const resume = document.getElementById('cand-resume').value;
      const job = document.getElementById('job-select').value;
      const btn = document.getElementById('submit-btn');
      const box = document.getElementById('result-box');

      btn.disabled = true;
      btn.innerHTML = '⏳ Processing Application with AI…';

      try {
        const res = await fetch('/hr/process-candidate-pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_title: job,
            job_description: 'Python, FastAPI, Docker, Kubernetes, n8n, OpenAI',
            candidate_name: name,
            candidate_email: email,
            salary_offered: '$125,000 / year',
            score_threshold: 70,
            resume_text: resume
          })
        });

        const data = await res.json();
        box.style.display = 'block';
        box.style.borderColor = data.passed ? 'var(--green)' : 'var(--red)';

        box.innerHTML = `
          <h3 style="color:${data.passed ? 'var(--green)' : 'var(--red)'}; margin-top:0;">
            ${data.passed ? '🎉 Application Shortlisted!' : ' Application Status Update'}
          </h3>
          <p><strong>Screening Score:</strong> <span style="font-size:18px; font-weight:bold; color:${data.passed ? 'var(--green)' : 'var(--red)'};">${data.score} / 100</span> (Passing threshold: 70/100)</p>
          <p><strong>Action Taken:</strong> ${data.email_action}</p>
          <p style="color:#a1a1aa; font-size:13px;"> An official email has been sent to <strong>${email}</strong> via local Mailpit SMTP.</p>
          <a href="http://localhost:8025" target="_blank" style="display:inline-block; margin-top:10px; background:var(--green); color:#000; padding:8px 16px; border-radius:6px; font-weight:bold; text-decoration:none;">📧 Check Mailpit Web Inbox Live</a>
        `;
      } catch (err) {
        alert('Error connecting to backend: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Submit Application to AI Screening Engine';
      }
    });
  </script>
</body>
</html>
"""
