#!/usr/bin/env python3
"""Generate 100 n8n workflow JSON files for Company AI Automation Platform."""

import json
import os

BASE = "/home/taheer-bin-hussain/Desktop/WEEK_5/workflows"

# ─────────────────────────────────────────────────────────────────────────────
# Helper builders
# ─────────────────────────────────────────────────────────────────────────────

def node(id_, name, type_, type_version, position, parameters, credentials=None):
    n = {
        "id": id_,
        "name": name,
        "type": type_,
        "typeVersion": type_version,
        "position": position,
        "parameters": parameters,
    }
    if credentials:
        n["credentials"] = credentials
    return n


def webhook_node(id_, name, path, x=0, y=300):
    return node(id_, name, "n8n-nodes-base.webhook", 1, [x, y], {
        "httpMethod": "POST",
        "path": path,
        "responseMode": "responseNode",
    })


def schedule_node(id_, name, rule, x=0, y=300):
    return node(id_, name, "n8n-nodes-base.scheduleTrigger", 1, [x, y], {
        "rule": rule,
    })


def http_node(id_, name, url, method="POST", x=250, y=300, body_params=None):
    params = {
        "url": url,
        "method": method,
        "options": {},
    }
    if body_params:
        params["bodyParameters"] = {"parameters": body_params}
    return node(id_, name, "n8n-nodes-base.httpRequest", 4, [x, y], params)


def postgres_node(id_, name, operation, query, x=500, y=300):
    return node(id_, name, "n8n-nodes-base.postgres", 2, [x, y], {
        "operation": operation,
        "query": query,
    }, credentials={"postgres": {"id": "pg-cred-1", "name": "Postgres DB"}})


def email_node(id_, name, to_expr, subject_expr, msg_expr, x=750, y=300):
    return node(id_, name, "n8n-nodes-base.emailSend", 2, [x, y], {
        "toEmail": to_expr,
        "subject": subject_expr,
        "message": msg_expr,
        "options": {},
    }, credentials={"smtp": {"id": "smtp-cred-1", "name": "SMTP Account"}})


def slack_node(id_, name, channel, text_expr, x=750, y=300):
    return node(id_, name, "n8n-nodes-base.slack", 2, [x, y], {
        "operation": "postMessage",
        "channel": channel,
        "text": text_expr,
    }, credentials={"slackApi": {"id": "slack-cred-1", "name": "Slack API"}})


def set_node(id_, name, values, x=500, y=300):
    return node(id_, name, "n8n-nodes-base.set", 3, [x, y], {
        "mode": "manual",
        "assignments": {"assignments": [
            {"id": f"assign-{i}", "name": k, "value": v, "type": "string"}
            for i, (k, v) in enumerate(values.items())
        ]},
        "options": {},
    })


def code_node(id_, name, code_str, x=500, y=300):
    return node(id_, name, "n8n-nodes-base.code", 2, [x, y], {
        "jsCode": code_str,
    })


def if_node(id_, name, left, op, right, x=500, y=300):
    return node(id_, name, "n8n-nodes-base.if", 2, [x, y], {
        "conditions": {
            "options": {"caseSensitive": True},
            "conditions": [{
                "leftValue": left,
                "rightValue": right,
                "operator": {"type": "string", "operation": op},
            }],
        },
    })


def noop_node(id_, name, x=750, y=300):
    return node(id_, name, "n8n-nodes-base.noOp", 1, [x, y], {})


def merge_node(id_, name, x=750, y=300):
    return node(id_, name, "n8n-nodes-base.merge", 2, [x, y], {"mode": "append"})


def form_node(id_, name, title, fields, x=0, y=300):
    return node(id_, name, "n8n-nodes-base.form", 1, [x, y], {
        "formTitle": title,
        "formDescription": f"Submit {title}",
        "formFields": {"values": fields},
    })


def workflow(id_, name, tags, nodes_list, connections_map):
    return {
        "name": name,
        "nodes": nodes_list,
        "connections": connections_map,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "id": id_,
        "tags": tags,
    }


def conn(from_node, to_node, from_output=0, to_input=0):
    """Return a single connection entry."""
    return (from_node, from_output, to_node, to_input)


def build_connections(pairs):
    """Build n8n connections dict from list of (from_node, from_out, to_node, to_in) tuples."""
    result = {}
    for (fn, fo, tn, ti) in pairs:
        result.setdefault(fn, {"main": []})
        while len(result[fn]["main"]) <= fo:
            result[fn]["main"].append([])
        result[fn]["main"][fo].append({"node": tn, "type": "main", "index": ti})
    return result


def save(folder, filename, wf):
    path = os.path.join(BASE, folder, filename)
    with open(path, "w") as f:
        json.dump(wf, f, indent=2)
    print(f"  ✓ {folder}/{filename}")


# ─────────────────────────────────────────────────────────────────────────────
# HR WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_hr_workflows():
    folder = "hr"

    # 01 - Job Posting Auto-publish
    nodes = [
        webhook_node("n1", "Job Posting Webhook", "job-posting", 0, 300),
        http_node("n2", "Post to LinkedIn", "https://api.linkedin.com/v2/jobs", "POST", 250, 200,
                  [{"name": "title", "value": "={{ $json.title }}"}, {"name": "description", "value": "={{ $json.description }}"}]),
        http_node("n3", "Post to Indeed", "https://api.indeed.com/v1/jobs", "POST", 250, 400,
                  [{"name": "title", "value": "={{ $json.title }}"}, {"name": "description", "value": "={{ $json.description }}"}]),
        merge_node("n4", "Merge Results", 500, 300),
        postgres_node("n5", "Save Job to DB", "executeQuery",
                      "INSERT INTO jobs (title, description, status, posted_at) VALUES ('{{ $json.title }}', '{{ $json.description }}', 'active', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Job Posting Webhook", "Post to LinkedIn"),
        conn("Job Posting Webhook", "Post to Indeed"),
        conn("Post to LinkedIn", "Merge Results"),
        conn("Post to Indeed", "Merge Results", 0, 1),
        conn("Merge Results", "Save Job to DB"),
    ])
    save(folder, "01-job-posting-autopublish.json",
         workflow("wf-hr-01", "Job Posting Auto-Publish", ["hr", "recruiting"], nodes, connections))

    # 02 - Resume Screening
    nodes = [
        webhook_node("n1", "Resume Webhook", "resume-screening", 0, 300),
        http_node("n2", "AI Screen Resume", "http://ai-backend:8000/hr/screen-resume", "POST", 250, 300,
                  [{"name": "resume_text", "value": "={{ $json.resume_text }}"}, {"name": "job_id", "value": "={{ $json.job_id }}"}]),
        postgres_node("n3", "Save Screening Result", "executeQuery",
                      "INSERT INTO resume_screenings (candidate_id, job_id, score, summary, screened_at) VALUES ('{{ $json.candidate_id }}', '{{ $json.job_id }}', {{ $json.score }}, '{{ $json.summary }}', NOW())",
                      500, 300),
        slack_node("n4", "Notify HR Team", "#hr-recruiting",
                   "New resume screened for {{ $json.job_id }} — Score: {{ $json.score }}/100. Candidate: {{ $json.candidate_name }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Resume Webhook", "AI Screen Resume"),
        conn("AI Screen Resume", "Save Screening Result"),
        conn("Save Screening Result", "Notify HR Team"),
    ])
    save(folder, "02-resume-screening.json",
         workflow("wf-hr-02", "Resume Screening", ["hr", "ai", "recruiting"], nodes, connections))

    # 03 - Candidate Ranking
    nodes = [
        schedule_node("n1", "Daily Schedule", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Candidates", "executeQuery",
                      "SELECT c.*, rs.score FROM candidates c JOIN resume_screenings rs ON c.id = rs.candidate_id WHERE c.status = 'active' ORDER BY rs.score DESC",
                      250, 300),
        code_node("n3", "Rank Candidates",
                  "const items = $input.all();\nconst ranked = items.map((item, idx) => ({\n  ...item.json,\n  rank: idx + 1,\n  tier: idx < 5 ? 'A' : idx < 15 ? 'B' : 'C'\n}));\nreturn ranked.map(r => ({json: r}));",
                  500, 300),
        postgres_node("n4", "Update Rankings", "executeQuery",
                      "UPDATE candidates SET rank = {{ $json.rank }}, tier = '{{ $json.tier }}' WHERE id = {{ $json.id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Daily Schedule", "Fetch Candidates"),
        conn("Fetch Candidates", "Rank Candidates"),
        conn("Rank Candidates", "Update Rankings"),
    ])
    save(folder, "03-candidate-ranking.json",
         workflow("wf-hr-03", "Candidate Ranking", ["hr", "recruiting"], nodes, connections))

    # 04 - Interview Scheduling
    nodes = [
        webhook_node("n1", "Interview Request Webhook", "interview-schedule", 0, 300),
        http_node("n2", "AI Schedule Interview", "http://ai-backend:8000/hr/interview-schedule", "POST", 250, 300,
                  [{"name": "candidate_id", "value": "={{ $json.candidate_id }}"}, {"name": "interviewer_id", "value": "={{ $json.interviewer_id }}"}]),
        set_node("n3", "Prepare Confirmation", {
            "candidate_email": "={{ $json.candidate_email }}",
            "interview_time": "={{ $json.scheduled_time }}",
            "meeting_link": "={{ $json.meeting_link }}",
        }, 500, 300),
        email_node("n4", "Send Confirmation Email",
                   "={{ $json.candidate_email }}",
                   "Interview Scheduled — {{ $json.job_title }}",
                   "Dear {{ $json.candidate_name }},\n\nYour interview has been scheduled for {{ $json.interview_time }}.\nJoin here: {{ $json.meeting_link }}\n\nBest regards,\nHR Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Interview Request Webhook", "AI Schedule Interview"),
        conn("AI Schedule Interview", "Prepare Confirmation"),
        conn("Prepare Confirmation", "Send Confirmation Email"),
    ])
    save(folder, "04-interview-scheduling.json",
         workflow("wf-hr-04", "Interview Scheduling", ["hr", "recruiting"], nodes, connections))

    # 05 - Interview Reminder
    nodes = [
        schedule_node("n1", "Daily Morning Schedule", {"interval": [{"field": "hours", "hoursInterval": 24}]}, 0, 300),
        postgres_node("n2", "Fetch Upcoming Interviews", "executeQuery",
                      "SELECT i.*, c.email, c.name FROM interviews i JOIN candidates c ON i.candidate_id = c.id WHERE i.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '24 hours' AND i.status = 'confirmed'",
                      250, 300),
        email_node("n3", "Send Reminder Email",
                   "={{ $json.email }}",
                   "Reminder: Interview Tomorrow — {{ $json.job_title }}",
                   "Hi {{ $json.name }},\n\nThis is a reminder that your interview is scheduled for tomorrow at {{ $json.scheduled_at }}.\nMeeting link: {{ $json.meeting_link }}\n\nGood luck!\nHR Team",
                   500, 300),
        slack_node("n4", "Notify Interviewer", "#hr-interviews",
                   "Reminder: Interview with {{ $json.name }} tomorrow at {{ $json.scheduled_at }}. Position: {{ $json.job_title }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily Morning Schedule", "Fetch Upcoming Interviews"),
        conn("Fetch Upcoming Interviews", "Send Reminder Email"),
        conn("Send Reminder Email", "Notify Interviewer"),
    ])
    save(folder, "05-interview-reminder.json",
         workflow("wf-hr-05", "Interview Reminder", ["hr", "recruiting"], nodes, connections))

    # 06 - Rejection Email
    nodes = [
        webhook_node("n1", "Rejection Webhook", "rejection-email", 0, 300),
        http_node("n2", "Generate Rejection Email", "http://ai-backend:8000/hr/generate-rejection-email", "POST", 250, 300,
                  [{"name": "candidate_id", "value": "={{ $json.candidate_id }}"}, {"name": "job_title", "value": "={{ $json.job_title }}"}]),
        postgres_node("n3", "Update Candidate Status", "executeQuery",
                      "UPDATE candidates SET status = 'rejected', rejection_sent_at = NOW() WHERE id = {{ $json.candidate_id }}",
                      500, 300),
        email_node("n4", "Send Rejection Email",
                   "={{ $json.candidate_email }}",
                   "Update on Your Application — {{ $json.job_title }}",
                   "={{ $json.email_body }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Rejection Webhook", "Generate Rejection Email"),
        conn("Generate Rejection Email", "Update Candidate Status"),
        conn("Update Candidate Status", "Send Rejection Email"),
    ])
    save(folder, "06-rejection-email.json",
         workflow("wf-hr-06", "Rejection Email", ["hr", "recruiting"], nodes, connections))

    # 07 - Offer Letter
    nodes = [
        webhook_node("n1", "Offer Letter Webhook", "offer-letter", 0, 300),
        http_node("n2", "Generate Offer Letter", "http://ai-backend:8000/hr/generate-offer-letter", "POST", 250, 300,
                  [{"name": "candidate_id", "value": "={{ $json.candidate_id }}"}, {"name": "salary", "value": "={{ $json.salary }}"}, {"name": "start_date", "value": "={{ $json.start_date }}"}]),
        http_node("n3", "Save to MinIO", "http://minio:9000/hr-docs/offer-letters", "PUT", 500, 300,
                  [{"name": "filename", "value": "={{ $json.candidate_id }}-offer.pdf"}, {"name": "content", "value": "={{ $json.pdf_content }}"}]),
        email_node("n4", "Send Offer Email",
                   "={{ $json.candidate_email }}",
                   "Congratulations — Job Offer from {{ $json.company_name }}",
                   "Dear {{ $json.candidate_name }},\n\nWe are delighted to offer you the position of {{ $json.job_title }}.\nPlease find your offer letter attached and accessible at: {{ $json.document_url }}\n\nStart Date: {{ $json.start_date }}\nSalary: {{ $json.salary }}\n\nBest regards,\nHR Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Offer Letter Webhook", "Generate Offer Letter"),
        conn("Generate Offer Letter", "Save to MinIO"),
        conn("Save to MinIO", "Send Offer Email"),
    ])
    save(folder, "07-offer-letter.json",
         workflow("wf-hr-07", "Offer Letter Generation", ["hr", "recruiting"], nodes, connections))

    # 08 - Onboarding Checklist
    nodes = [
        webhook_node("n1", "Hire Webhook", "employee-onboarding", 0, 300),
        http_node("n2", "Generate Onboarding Checklist", "http://ai-backend:8000/hr/onboarding-checklist", "POST", 250, 300,
                  [{"name": "employee_id", "value": "={{ $json.employee_id }}"}, {"name": "role", "value": "={{ $json.role }}"}, {"name": "department", "value": "={{ $json.department }}"}]),
        postgres_node("n3", "Create Onboarding Tasks", "executeQuery",
                      "INSERT INTO onboarding_tasks (employee_id, task_name, due_date, status) SELECT {{ $json.employee_id }}, task, NOW() + INTERVAL '{{ $json.days }} days', 'pending' FROM json_array_elements_text('{{ $json.tasks }}'::json) AS task",
                      500, 300),
        slack_node("n4", "Notify HR & Manager", "#hr-onboarding",
                   ":wave: New hire onboarding started for *{{ $json.employee_name }}* ({{ $json.role }}).\n{{ $json.task_count }} tasks created. Start date: {{ $json.start_date }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Hire Webhook", "Generate Onboarding Checklist"),
        conn("Generate Onboarding Checklist", "Create Onboarding Tasks"),
        conn("Create Onboarding Tasks", "Notify HR & Manager"),
    ])
    save(folder, "08-onboarding-checklist.json",
         workflow("wf-hr-08", "Employee Onboarding Checklist", ["hr", "onboarding"], nodes, connections))

    # 09 - Employee Welcome
    nodes = [
        webhook_node("n1", "New Employee Webhook", "employee-welcome", 0, 300),
        set_node("n2", "Prepare Welcome Data", {
            "employee_name": "={{ $json.first_name }} {{ $json.last_name }}",
            "start_date": "={{ $json.start_date }}",
            "team_channel": "={{ $json.team_slack_channel }}",
        }, 250, 300),
        email_node("n3", "Send Welcome Email",
                   "={{ $json.personal_email }}",
                   "Welcome to {{ $json.company_name }}, {{ $json.first_name }}!",
                   "Hi {{ $json.first_name }},\n\nWelcome aboard! We're thrilled to have you join the {{ $json.department }} team.\n\nYour start date is {{ $json.start_date }}. You'll receive your IT setup instructions separately.\n\nLooking forward to working with you!\n\nThe Team",
                   500, 300),
        slack_node("n4", "Post Welcome to General", "#general",
                   ":tada: Please welcome our newest team member, *{{ $json.employee_name }}*, joining as *{{ $json.role }}* in {{ $json.department }}! Starting {{ $json.start_date }}.",
                   750, 300),
    ]
    connections = build_connections([
        conn("New Employee Webhook", "Prepare Welcome Data"),
        conn("Prepare Welcome Data", "Send Welcome Email"),
        conn("Send Welcome Email", "Post Welcome to General"),
    ])
    save(folder, "09-employee-welcome.json",
         workflow("wf-hr-09", "Employee Welcome", ["hr", "onboarding"], nodes, connections))

    # 10 - IT Access Provisioning
    nodes = [
        webhook_node("n1", "IT Access Webhook", "it-access-provisioning", 0, 300),
        http_node("n2", "Create IT Ticket", "http://jira-api:8080/rest/api/2/issue", "POST", 250, 300,
                  [{"name": "summary", "value": "IT Access Setup for {{ $json.employee_name }}"}, {"name": "description", "value": "New employee {{ $json.employee_name }} requires: {{ $json.required_access }}"}, {"name": "priority", "value": "High"}]),
        set_node("n3", "Prepare Confirmation", {
            "ticket_id": "={{ $json.id }}",
            "employee_email": "={{ $json.employee_email }}",
            "access_list": "={{ $json.required_access }}",
        }, 500, 300),
        email_node("n4", "Send IT Confirmation",
                   "={{ $json.employee_email }}",
                   "IT Access Setup Initiated — Ticket #{{ $json.ticket_id }}",
                   "Hi {{ $json.employee_name }},\n\nYour IT access setup has been initiated (Ticket #{{ $json.ticket_id }}).\nAccess being configured: {{ $json.access_list }}\n\nExpected completion: 1 business day.\n\nIT Support Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("IT Access Webhook", "Create IT Ticket"),
        conn("Create IT Ticket", "Prepare Confirmation"),
        conn("Prepare Confirmation", "Send IT Confirmation"),
    ])
    save(folder, "10-it-access-provisioning.json",
         workflow("wf-hr-10", "IT Access Provisioning", ["hr", "it", "onboarding"], nodes, connections))

    # 11 - Employee Offboarding
    nodes = [
        webhook_node("n1", "Offboarding Webhook", "employee-offboarding", 0, 300),
        http_node("n2", "Revoke SSO Access", "http://sso-api:8080/api/users/disable", "POST", 250, 200,
                  [{"name": "user_id", "value": "={{ $json.employee_id }}"}, {"name": "reason", "value": "employee_offboarding"}]),
        http_node("n3", "Create IT Offboarding Ticket", "http://jira-api:8080/rest/api/2/issue", "POST", 250, 400,
                  [{"name": "summary", "value": "Offboarding: Revoke all access for {{ $json.employee_name }}"}, {"name": "priority", "value": "High"}]),
        merge_node("n4", "Merge Offboarding Actions", 500, 300),
        postgres_node("n5", "Update Employee Status", "executeQuery",
                      "UPDATE employees SET status = 'offboarded', last_day = '{{ $json.last_day }}', offboarded_at = NOW() WHERE id = {{ $json.employee_id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Offboarding Webhook", "Revoke SSO Access"),
        conn("Offboarding Webhook", "Create IT Offboarding Ticket"),
        conn("Revoke SSO Access", "Merge Offboarding Actions"),
        conn("Create IT Offboarding Ticket", "Merge Offboarding Actions", 0, 1),
        conn("Merge Offboarding Actions", "Update Employee Status"),
    ])
    save(folder, "11-employee-offboarding.json",
         workflow("wf-hr-11", "Employee Offboarding", ["hr", "offboarding"], nodes, connections))

    # 12 - Leave Request
    nodes = [
        form_node("n1", "Leave Request Form", "Employee Leave Request", [
            {"fieldLabel": "Employee ID", "fieldType": "text", "requiredField": True},
            {"fieldLabel": "Leave Type", "fieldType": "dropdown", "fieldOptions": {"values": [{"option": "Annual"}, {"option": "Sick"}, {"option": "Unpaid"}]}, "requiredField": True},
            {"fieldLabel": "Start Date", "fieldType": "date", "requiredField": True},
            {"fieldLabel": "End Date", "fieldType": "date", "requiredField": True},
            {"fieldLabel": "Reason", "fieldType": "textarea", "requiredField": False},
        ], 0, 300),
        postgres_node("n2", "Save Leave Request", "executeQuery",
                      "INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status) VALUES ('{{ $json[\"Employee ID\"] }}', '{{ $json[\"Leave Type\"] }}', '{{ $json[\"Start Date\"] }}', '{{ $json[\"End Date\"] }}', '{{ $json.Reason }}', 'pending') RETURNING id, (end_date - start_date) AS days",
                      250, 300),
        if_node("n3", "Auto-Approve Check", "={{ $json.days }}", "smallerEqual", "2", 500, 300),
        postgres_node("n4", "Auto-Approve Short Leave", "executeQuery",
                      "UPDATE leave_requests SET status = 'approved', approved_at = NOW() WHERE id = {{ $json.id }}",
                      750, 200),
        slack_node("n5", "Notify Manager for Approval", "#hr-leaves",
                   ":calendar: Leave request from <@{{ $json.employee_slack_id }}> — {{ $json[\"Leave Type\"] }} from {{ $json[\"Start Date\"] }} to {{ $json[\"End Date\"] }} ({{ $json.days }} days). Approval required.",
                   750, 400),
    ]
    connections = build_connections([
        conn("Leave Request Form", "Save Leave Request"),
        conn("Save Leave Request", "Auto-Approve Check"),
        conn("Auto-Approve Check", "Auto-Approve Short Leave", 0, 0),
        conn("Auto-Approve Check", "Notify Manager for Approval", 1, 0),
    ])
    save(folder, "12-leave-request.json",
         workflow("wf-hr-12", "Leave Request Processing", ["hr", "leave"], nodes, connections))

    # 13 - Performance Review Reminder
    nodes = [
        schedule_node("n1", "Monthly Schedule", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Active Employees", "executeQuery",
                      "SELECT e.*, m.email as manager_email FROM employees e JOIN employees m ON e.manager_id = m.id WHERE e.status = 'active' AND (e.last_review_date IS NULL OR e.last_review_date < NOW() - INTERVAL '3 months')",
                      250, 300),
        email_node("n3", "Send Review Reminder to Manager",
                   "={{ $json.manager_email }}",
                   "Performance Review Due: {{ $json.name }}",
                   "Hi,\n\nIt's time to conduct the quarterly performance review for {{ $json.name }} ({{ $json.role }}).\n\nPlease complete the review by {{ $json.review_due_date }}.\n\nAccess the review form here: https://hr-portal.company.com/reviews/new?employee_id={{ $json.id }}\n\nHR Team",
                   500, 300),
        postgres_node("n4", "Log Review Reminder Sent", "executeQuery",
                      "INSERT INTO review_reminders (employee_id, sent_at) VALUES ({{ $json.id }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Monthly Schedule", "Fetch Active Employees"),
        conn("Fetch Active Employees", "Send Review Reminder to Manager"),
        conn("Send Review Reminder to Manager", "Log Review Reminder Sent"),
    ])
    save(folder, "13-performance-review-reminder.json",
         workflow("wf-hr-13", "Performance Review Reminder", ["hr", "performance"], nodes, connections))

    # 14 - Training Assignment
    nodes = [
        webhook_node("n1", "Training Assignment Webhook", "training-assignment", 0, 300),
        http_node("n2", "Get Role Training Plan", "http://ai-backend:8000/hr/training-plan", "POST", 250, 300,
                  [{"name": "role", "value": "={{ $json.role }}"}, {"name": "department", "value": "={{ $json.department }}"}, {"name": "experience_level", "value": "={{ $json.experience_level }}"}]),
        postgres_node("n3", "Save Training Assignments", "executeQuery",
                      "INSERT INTO training_assignments (employee_id, course_id, course_name, due_date, status) SELECT {{ $json.employee_id }}, course->>'id', course->>'name', NOW() + INTERVAL '30 days', 'assigned' FROM json_array_elements('{{ $json.courses }}'::json) AS course",
                      500, 300),
        email_node("n4", "Send Training Email",
                   "={{ $json.employee_email }}",
                   "Your Training Plan is Ready",
                   "Hi {{ $json.employee_name }},\n\nBased on your role as {{ $json.role }}, we've assigned the following training courses:\n\n{{ $json.course_list }}\n\nPlease complete these within 30 days. Access courses at: https://lms.company.com\n\nHR Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Training Assignment Webhook", "Get Role Training Plan"),
        conn("Get Role Training Plan", "Save Training Assignments"),
        conn("Save Training Assignments", "Send Training Email"),
    ])
    save(folder, "14-training-assignment.json",
         workflow("wf-hr-14", "Training Assignment", ["hr", "training"], nodes, connections))

    # 15 - Payroll Collection
    nodes = [
        schedule_node("n1", "Monthly Payroll Schedule", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Collect Hours & Attendance", "executeQuery",
                      "SELECT e.id, e.name, e.hourly_rate, e.salary_type, SUM(a.hours_worked) as total_hours, COUNT(a.id) as days_worked FROM employees e JOIN attendance a ON e.id = a.employee_id WHERE a.work_date >= date_trunc('month', NOW() - INTERVAL '1 month') AND a.work_date < date_trunc('month', NOW()) GROUP BY e.id, e.name, e.hourly_rate, e.salary_type",
                      250, 300),
        code_node("n3", "Calculate Payroll",
                  "const items = $input.all();\nreturn items.map(item => {\n  const emp = item.json;\n  const gross = emp.salary_type === 'hourly'\n    ? emp.total_hours * emp.hourly_rate\n    : emp.monthly_salary;\n  const tax = gross * 0.25;\n  const net = gross - tax;\n  return { json: { ...emp, gross_pay: gross.toFixed(2), tax: tax.toFixed(2), net_pay: net.toFixed(2) } };\n});",
                  500, 300),
        postgres_node("n4", "Save Payroll Records", "executeQuery",
                      "INSERT INTO payroll (employee_id, period, gross_pay, tax, net_pay, generated_at) VALUES ({{ $json.id }}, date_trunc('month', NOW() - INTERVAL '1 month'), {{ $json.gross_pay }}, {{ $json.tax }}, {{ $json.net_pay }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Monthly Payroll Schedule", "Collect Hours & Attendance"),
        conn("Collect Hours & Attendance", "Calculate Payroll"),
        conn("Calculate Payroll", "Save Payroll Records"),
    ])
    save(folder, "15-payroll-collection.json",
         workflow("wf-hr-15", "Payroll Collection", ["hr", "payroll"], nodes, connections))

    # 16 - Birthday & Anniversary
    nodes = [
        schedule_node("n1", "Daily Birthday Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Birthdays & Anniversaries", "executeQuery",
                      "SELECT name, slack_id, 'birthday' as event_type FROM employees WHERE EXTRACT(MONTH FROM date_of_birth) = EXTRACT(MONTH FROM NOW()) AND EXTRACT(DAY FROM date_of_birth) = EXTRACT(DAY FROM NOW()) AND status = 'active' UNION ALL SELECT name, slack_id, 'anniversary' as event_type FROM employees WHERE EXTRACT(MONTH FROM hire_date) = EXTRACT(MONTH FROM NOW()) AND EXTRACT(DAY FROM hire_date) = EXTRACT(DAY FROM NOW()) AND status = 'active'",
                      250, 300),
        if_node("n3", "Check Event Type", "={{ $json.event_type }}", "equals", "birthday", 500, 300),
        slack_node("n4", "Birthday Message", "#general",
                   ":birthday: Happy Birthday <@{{ $json.slack_id }}>! Wishing you a wonderful day! :cake:",
                   750, 200),
        slack_node("n5", "Anniversary Message", "#general",
                   ":tada: Happy Work Anniversary <@{{ $json.slack_id }}>! Thank you for being part of our team! :star:",
                   750, 400),
    ]
    connections = build_connections([
        conn("Daily Birthday Check", "Find Birthdays & Anniversaries"),
        conn("Find Birthdays & Anniversaries", "Check Event Type"),
        conn("Check Event Type", "Birthday Message", 0, 0),
        conn("Check Event Type", "Anniversary Message", 1, 0),
    ])
    save(folder, "16-birthday-anniversary.json",
         workflow("wf-hr-16", "Birthday & Anniversary Celebration", ["hr", "culture"], nodes, connections))

    # 17 - New Hire Announcement
    nodes = [
        webhook_node("n1", "New Hire Webhook", "new-hire-announcement", 0, 300),
        set_node("n2", "Format Announcement", {
            "announcement": "=:wave: We're excited to announce that *{{ $json.first_name }} {{ $json.last_name }}* is joining us as *{{ $json.role }}* in the *{{ $json.department }}* department starting {{ $json.start_date }}!\n\n{{ $json.bio }}\n\nPlease join us in welcoming them to the team!",
        }, 250, 300),
        slack_node("n3", "Post to General", "#general",
                   "={{ $json.announcement }}",
                   500, 300),
        slack_node("n4", "Post to Department Channel", "={{ $json.team_channel }}",
                   ":handshake: Your new teammate *{{ $json.first_name }}* is joining on {{ $json.start_date }}. Start date is {{ $json.start_date }}. Get ready to welcome them!",
                   750, 300),
    ]
    connections = build_connections([
        conn("New Hire Webhook", "Format Announcement"),
        conn("Format Announcement", "Post to General"),
        conn("Post to General", "Post to Department Channel"),
    ])
    save(folder, "17-new-hire-announcement.json",
         workflow("wf-hr-17", "New Hire Announcement", ["hr", "onboarding"], nodes, connections))

    # 18 - Background Check
    nodes = [
        webhook_node("n1", "Background Check Webhook", "background-check", 0, 300),
        http_node("n2", "Initiate Background Check", "https://api.checkr.com/v1/candidates", "POST", 250, 300,
                  [{"name": "first_name", "value": "={{ $json.first_name }}"}, {"name": "last_name", "value": "={{ $json.last_name }}"}, {"name": "email", "value": "={{ $json.email }}"}, {"name": "dob", "value": "={{ $json.date_of_birth }}"}]),
        postgres_node("n3", "Save Background Check Record", "executeQuery",
                      "INSERT INTO background_checks (candidate_id, check_id, status, initiated_at) VALUES ({{ $json.candidate_id }}, '{{ $json.id }}', 'pending', NOW())",
                      500, 300),
        slack_node("n4", "Notify HR of Initiation", "#hr-compliance",
                   ":shield: Background check initiated for candidate {{ $json.candidate_name }} (ID: {{ $json.candidate_id }}). Check ID: {{ $json.id }}. Results expected in 3-5 business days.",
                   750, 300),
    ]
    connections = build_connections([
        conn("Background Check Webhook", "Initiate Background Check"),
        conn("Initiate Background Check", "Save Background Check Record"),
        conn("Save Background Check Record", "Notify HR of Initiation"),
    ])
    save(folder, "18-background-check.json",
         workflow("wf-hr-18", "Background Check", ["hr", "compliance"], nodes, connections))

    # 19 - Reference Check
    nodes = [
        webhook_node("n1", "Reference Check Webhook", "reference-check", 0, 300),
        postgres_node("n2", "Get Candidate References", "executeQuery",
                      "SELECT r.*, c.name as candidate_name FROM references r JOIN candidates c ON r.candidate_id = c.id WHERE r.candidate_id = {{ $json.candidate_id }}",
                      250, 300),
        email_node("n3", "Send Reference Request Email",
                   "={{ $json.reference_email }}",
                   "Reference Request for {{ $json.candidate_name }}",
                   "Dear {{ $json.reference_name }},\n\nWe are conducting a reference check for {{ $json.candidate_name }}, who has applied for the {{ $json.job_title }} position.\n\nWould you kindly complete this brief reference form: https://hr-portal.company.com/references/{{ $json.reference_token }}\n\nThank you for your time.\n\nHR Team",
                   500, 300),
        postgres_node("n4", "Log Reference Request", "executeQuery",
                      "INSERT INTO reference_requests (candidate_id, reference_id, sent_at, status) VALUES ({{ $json.candidate_id }}, {{ $json.id }}, NOW(), 'pending')",
                      750, 300),
    ]
    connections = build_connections([
        conn("Reference Check Webhook", "Get Candidate References"),
        conn("Get Candidate References", "Send Reference Request Email"),
        conn("Send Reference Request Email", "Log Reference Request"),
    ])
    save(folder, "19-reference-check.json",
         workflow("wf-hr-19", "Reference Check", ["hr", "recruiting"], nodes, connections))

    # 20 - HR Weekly Report
    nodes = [
        schedule_node("n1", "Weekly Friday Schedule", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate HR Metrics", "executeQuery",
                      "SELECT (SELECT COUNT(*) FROM candidates WHERE created_at >= NOW() - INTERVAL '7 days') as new_applications, (SELECT COUNT(*) FROM interviews WHERE scheduled_at >= NOW() - INTERVAL '7 days') as interviews_scheduled, (SELECT COUNT(*) FROM candidates WHERE status = 'hired' AND updated_at >= NOW() - INTERVAL '7 days') as hires, (SELECT COUNT(*) FROM leave_requests WHERE created_at >= NOW() - INTERVAL '7 days') as leave_requests, (SELECT AVG(score) FROM resume_screenings WHERE created_at >= NOW() - INTERVAL '7 days') as avg_ai_score",
                      250, 300),
        code_node("n3", "Format Weekly Report",
                  "const m = $input.first().json;\nconst report = `HR Weekly Report — ${new Date().toLocaleDateString()}\\n\\n` +\n  `📋 New Applications: ${m.new_applications}\\n` +\n  `🗓️ Interviews Scheduled: ${m.interviews_scheduled}\\n` +\n  `🎉 New Hires: ${m.hires}\\n` +\n  `🏖️ Leave Requests: ${m.leave_requests}\\n` +\n  `🤖 Avg AI Score: ${parseFloat(m.avg_ai_score).toFixed(1)}/100`;\nreturn [{ json: { report, ...m } }];",
                  500, 300),
        email_node("n4", "Send HR Weekly Report",
                   "hr-director@company.com",
                   "HR Weekly Report — {{ $now.format('MMM DD, YYYY') }}",
                   "={{ $json.report }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly Friday Schedule", "Aggregate HR Metrics"),
        conn("Aggregate HR Metrics", "Format Weekly Report"),
        conn("Format Weekly Report", "Send HR Weekly Report"),
    ])
    save(folder, "20-hr-weekly-report.json",
         workflow("wf-hr-20", "HR Weekly Report", ["hr", "reporting"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# CRM WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_crm_workflows():
    folder = "crm"

    # 21 - Lead Capture
    nodes = [
        webhook_node("n1", "Lead Capture Webhook", "lead-capture", 0, 300),
        postgres_node("n2", "Save Lead to DB", "executeQuery",
                      "INSERT INTO leads (name, email, phone, company, source, created_at) VALUES ('{{ $json.name }}', '{{ $json.email }}', '{{ $json.phone }}', '{{ $json.company }}', '{{ $json.source }}', NOW()) RETURNING id",
                      250, 300),
        http_node("n3", "Trigger Nurture Sequence", "http://ai-backend:8000/crm/start-nurture", "POST", 500, 300,
                  [{"name": "lead_id", "value": "={{ $json.id }}"}, {"name": "source", "value": "={{ $json.source }}"}]),
        slack_node("n4", "Notify Sales Team", "#crm-leads",
                   ":mega: New lead captured!\nName: *{{ $json.name }}*\nCompany: {{ $json.company }}\nSource: {{ $json.source }}\nEmail: {{ $json.email }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Lead Capture Webhook", "Save Lead to DB"),
        conn("Save Lead to DB", "Trigger Nurture Sequence"),
        conn("Trigger Nurture Sequence", "Notify Sales Team"),
    ])
    save(folder, "21-lead-capture.json",
         workflow("wf-crm-21", "Lead Capture", ["crm", "leads"], nodes, connections))

    # 22 - Lead Scoring
    nodes = [
        webhook_node("n1", "Lead Score Webhook", "lead-scoring", 0, 300),
        http_node("n2", "AI Score Lead", "http://ai-backend:8000/crm/score-lead", "POST", 250, 300,
                  [{"name": "lead_id", "value": "={{ $json.lead_id }}"}, {"name": "behavior_data", "value": "={{ $json.behavior_data }}"}]),
        postgres_node("n3", "Update Lead Score", "executeQuery",
                      "UPDATE leads SET score = {{ $json.score }}, score_updated_at = NOW(), tier = '{{ $json.tier }}' WHERE id = {{ $json.lead_id }}",
                      500, 300),
        if_node("n4", "Hot Lead Check", "={{ $json.score }}", "largerEqual", "80", 750, 300),
        slack_node("n5", "Alert Hot Lead", "#crm-hot-leads",
                   ":fire: HOT LEAD ALERT!\n*{{ $json.lead_name }}* from {{ $json.company }} scored *{{ $json.score }}/100*.\nAssigned to: {{ $json.assigned_rep }}\nAction: Contact within 1 hour!",
                   1000, 200),
        noop_node("n6", "Regular Lead - No Action", 1000, 400),
    ]
    connections = build_connections([
        conn("Lead Score Webhook", "AI Score Lead"),
        conn("AI Score Lead", "Update Lead Score"),
        conn("Update Lead Score", "Hot Lead Check"),
        conn("Hot Lead Check", "Alert Hot Lead", 0, 0),
        conn("Hot Lead Check", "Regular Lead - No Action", 1, 0),
    ])
    save(folder, "22-lead-scoring.json",
         workflow("wf-crm-22", "Lead Scoring", ["crm", "leads", "ai"], nodes, connections))

    # 23 - Lead Nurture Sequence
    nodes = [
        schedule_node("n1", "Daily Nurture Schedule", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Leads by Stage", "executeQuery",
                      "SELECT l.*, ns.sequence_day, ns.email_template FROM leads l JOIN nurture_sequences ns ON l.nurture_stage = ns.stage WHERE l.status = 'nurturing' AND l.last_email_sent < NOW() - INTERVAL '1 day' * ns.interval_days",
                      250, 300),
        http_node("n3", "Personalize Email Content", "http://ai-backend:8000/crm/personalize-email", "POST", 500, 300,
                  [{"name": "lead_id", "value": "={{ $json.id }}"}, {"name": "template", "value": "={{ $json.email_template }}"}, {"name": "stage", "value": "={{ $json.nurture_stage }}"}]),
        email_node("n4", "Send Nurture Email",
                   "={{ $json.email }}",
                   "={{ $json.email_subject }}",
                   "={{ $json.personalized_content }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily Nurture Schedule", "Fetch Leads by Stage"),
        conn("Fetch Leads by Stage", "Personalize Email Content"),
        conn("Personalize Email Content", "Send Nurture Email"),
    ])
    save(folder, "23-lead-nurture-sequence.json",
         workflow("wf-crm-23", "Lead Nurture Sequence", ["crm", "email", "leads"], nodes, connections))

    # 24 - Deal Stage Notification
    nodes = [
        webhook_node("n1", "Deal Update Webhook", "deal-stage-update", 0, 300),
        postgres_node("n2", "Get Deal & Rep Details", "executeQuery",
                      "SELECT d.*, u.name as rep_name, u.slack_id FROM deals d JOIN users u ON d.assigned_to = u.id WHERE d.id = {{ $json.deal_id }}",
                      250, 300),
        set_node("n3", "Format Stage Message", {
            "stage_emoji": "={% if $json.new_stage == 'Closed Won' %}🏆{% elif $json.new_stage == 'Proposal' %}📄{% elif $json.new_stage == 'Negotiation' %}🤝{% else %}📊{% endif %}",
            "message": "={{ $json.stage_emoji }} Deal *{{ $json.deal_name }}* moved to *{{ $json.new_stage }}* (was: {{ $json.old_stage }})\nValue: ${{ $json.value }}\nRep: <@{{ $json.slack_id }}>",
        }, 500, 300),
        slack_node("n4", "Notify Sales Channel", "#crm-deals",
                   "={{ $json.message }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Deal Update Webhook", "Get Deal & Rep Details"),
        conn("Get Deal & Rep Details", "Format Stage Message"),
        conn("Format Stage Message", "Notify Sales Channel"),
    ])
    save(folder, "24-deal-stage-notification.json",
         workflow("wf-crm-24", "Deal Stage Notification", ["crm", "sales"], nodes, connections))

    # 25 - Sales Followup Reminder
    nodes = [
        schedule_node("n1", "Daily Sales Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Inactive Deals", "executeQuery",
                      "SELECT d.*, u.slack_id, u.name as rep_name FROM deals d JOIN users u ON d.assigned_to = u.id WHERE d.status = 'active' AND d.last_activity < NOW() - INTERVAL '3 days' AND d.stage NOT IN ('Closed Won', 'Closed Lost')",
                      250, 300),
        set_node("n3", "Format Reminder Message", {
            "days_inactive": "={{ Math.floor((new Date() - new Date($json.last_activity)) / 86400000) }}",
            "reminder": "=⏰ Deal *{{ $json.deal_name }}* has been inactive for {{ $json.days_inactive }} days. Last stage: {{ $json.stage }}. Value: ${{ $json.value }}",
        }, 500, 300),
        slack_node("n4", "Send Reminder to Rep", "={{ $json.slack_id }}",
                   "={{ $json.reminder }}\n\nPlease follow up or update the deal status.",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily Sales Check", "Find Inactive Deals"),
        conn("Find Inactive Deals", "Format Reminder Message"),
        conn("Format Reminder Message", "Send Reminder to Rep"),
    ])
    save(folder, "25-sales-followup-reminder.json",
         workflow("wf-crm-25", "Sales Follow-up Reminder", ["crm", "sales"], nodes, connections))

    # 26 - Churn Prediction
    nodes = [
        schedule_node("n1", "Weekly Churn Check", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Active Customers", "executeQuery",
                      "SELECT id, name, email, last_login, usage_hours, support_tickets FROM customers WHERE status = 'active'",
                      250, 300),
        http_node("n3", "Predict Churn Risk", "http://ai-backend:8000/crm/churn-prediction", "POST", 500, 300,
                  [{"name": "customer_id", "value": "={{ $json.id }}"}, {"name": "usage_data", "value": "={{ $json }}"}]),
        if_node("n4", "High Churn Risk?", "={{ $json.churn_probability }}", "largerEqual", "0.7", 750, 300),
        slack_node("n5", "Alert Customer Success", "#crm-churn-risk",
                   ":warning: HIGH CHURN RISK!\nCustomer: *{{ $json.customer_name }}*\nChurn Probability: *{{ ($json.churn_probability * 100).toFixed(0) }}%*\nKey Reason: {{ $json.primary_reason }}\nAction: Schedule retention call immediately.",
                   1000, 200),
        noop_node("n6", "Low Risk - Continue", 1000, 400),
    ]
    connections = build_connections([
        conn("Weekly Churn Check", "Fetch Active Customers"),
        conn("Fetch Active Customers", "Predict Churn Risk"),
        conn("Predict Churn Risk", "High Churn Risk?"),
        conn("High Churn Risk?", "Alert Customer Success", 0, 0),
        conn("High Churn Risk?", "Low Risk - Continue", 1, 0),
    ])
    save(folder, "26-churn-prediction.json",
         workflow("wf-crm-26", "Churn Prediction", ["crm", "ai", "retention"], nodes, connections))

    # 27 - Upsell Detection
    nodes = [
        schedule_node("n1", "Weekly Upsell Scan", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Get Customer Usage Data", "executeQuery",
                      "SELECT c.*, s.plan_name, s.plan_limit, c.usage_this_month FROM customers c JOIN subscriptions s ON c.subscription_id = s.id WHERE c.status = 'active' AND c.usage_this_month >= s.plan_limit * 0.8",
                      250, 300),
        http_node("n3", "Identify Upsell Opportunity", "http://ai-backend:8000/crm/upsell-opportunity", "POST", 500, 300,
                  [{"name": "customer_id", "value": "={{ $json.id }}"}, {"name": "current_plan", "value": "={{ $json.plan_name }}"}, {"name": "usage_ratio", "value": "={{ $json.usage_this_month / $json.plan_limit }}"}]),
        postgres_node("n4", "Create Upsell Task", "executeQuery",
                      "INSERT INTO crm_tasks (customer_id, task_type, description, priority, due_date, created_at) VALUES ({{ $json.customer_id }}, 'upsell', '{{ $json.recommendation }}', 'high', NOW() + INTERVAL '3 days', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Weekly Upsell Scan", "Get Customer Usage Data"),
        conn("Get Customer Usage Data", "Identify Upsell Opportunity"),
        conn("Identify Upsell Opportunity", "Create Upsell Task"),
    ])
    save(folder, "27-upsell-detection.json",
         workflow("wf-crm-27", "Upsell Detection", ["crm", "sales", "ai"], nodes, connections))

    # 28 - Contract Renewal
    nodes = [
        schedule_node("n1", "Daily Renewal Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Expiring Contracts", "executeQuery",
                      "SELECT c.*, cu.name as customer_name, cu.email FROM contracts c JOIN customers cu ON c.customer_id = cu.id WHERE c.status = 'active' AND c.end_date BETWEEN NOW() AND NOW() + INTERVAL '90 days' AND c.renewal_email_sent IS NULL",
                      250, 300),
        set_node("n3", "Calculate Days Until Expiry", {
            "days_remaining": "={{ Math.floor((new Date($json.end_date) - new Date()) / 86400000) }}",
            "urgency": "={% if days_remaining <= 30 %}URGENT{% elif days_remaining <= 60 %}SOON{% else %}UPCOMING{% endif %}",
        }, 500, 300),
        email_node("n4", "Send Renewal Email",
                   "={{ $json.email }}",
                   "[{{ $json.urgency }}] Contract Renewal — {{ $json.days_remaining }} Days Remaining",
                   "Dear {{ $json.customer_name }},\n\nYour contract ({{ $json.contract_number }}) expires on {{ $json.end_date }} ({{ $json.days_remaining }} days).\n\nPlease contact your account manager to discuss renewal options.\n\nAccount Manager: {{ $json.account_manager }}\nRenewal Portal: https://portal.company.com/renewals/{{ $json.id }}\n\nBest regards,\nAccount Management Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily Renewal Check", "Find Expiring Contracts"),
        conn("Find Expiring Contracts", "Calculate Days Until Expiry"),
        conn("Calculate Days Until Expiry", "Send Renewal Email"),
    ])
    save(folder, "28-contract-renewal.json",
         workflow("wf-crm-28", "Contract Renewal", ["crm", "sales"], nodes, connections))

    # 29 - CRM Data Enrichment
    nodes = [
        webhook_node("n1", "Enrichment Webhook", "crm-enrich-lead", 0, 300),
        http_node("n2", "Enrich via Clearbit", "https://company.clearbit.com/v2/combined/find", "GET", 250, 300,
                  [{"name": "email", "value": "={{ $json.email }}"}]),
        set_node("n3", "Map Enriched Data", {
            "company_name": "={{ $json.company.name }}",
            "company_size": "={{ $json.company.metrics.employees }}",
            "industry": "={{ $json.company.category.industry }}",
            "linkedin_url": "={{ $json.person.linkedin.handle }}",
            "job_title": "={{ $json.person.employment.title }}",
        }, 500, 300),
        postgres_node("n4", "Update Lead with Enriched Data", "executeQuery",
                      "UPDATE leads SET company_name = '{{ $json.company_name }}', company_size = {{ $json.company_size }}, industry = '{{ $json.industry }}', linkedin_url = '{{ $json.linkedin_url }}', job_title = '{{ $json.job_title }}', enriched_at = NOW() WHERE email = '{{ $json.email }}'",
                      750, 300),
    ]
    connections = build_connections([
        conn("Enrichment Webhook", "Enrich via Clearbit"),
        conn("Enrich via Clearbit", "Map Enriched Data"),
        conn("Map Enriched Data", "Update Lead with Enriched Data"),
    ])
    save(folder, "29-crm-data-enrichment.json",
         workflow("wf-crm-29", "CRM Data Enrichment", ["crm", "data"], nodes, connections))

    # 30 - Sales Pipeline Report
    nodes = [
        schedule_node("n1", "Weekly Pipeline Report", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate Pipeline Data", "executeQuery",
                      "SELECT stage, COUNT(*) as deal_count, SUM(value) as total_value, AVG(value) as avg_value FROM deals WHERE status = 'active' GROUP BY stage ORDER BY CASE stage WHEN 'Prospecting' THEN 1 WHEN 'Qualification' THEN 2 WHEN 'Proposal' THEN 3 WHEN 'Negotiation' THEN 4 WHEN 'Closed Won' THEN 5 ELSE 6 END",
                      250, 300),
        code_node("n3", "Format Pipeline Report",
                  "const items = $input.all();\nconst total = items.reduce((s, i) => s + parseFloat(i.json.total_value || 0), 0);\nconst lines = items.map(i => `${i.json.stage}: ${i.json.deal_count} deals ($${parseFloat(i.json.total_value).toLocaleString()})`);\nconst report = `Sales Pipeline Report\\n${'='.repeat(40)}\\n${lines.join('\\n')}\\n${'='.repeat(40)}\\nTotal Pipeline: $${total.toLocaleString()}`;\nreturn [{json:{report, total_pipeline: total}}];",
                  500, 300),
        email_node("n4", "Send Pipeline Report",
                   "executives@company.com",
                   "Weekly Sales Pipeline Report — {{ $now.format('MMM DD, YYYY') }}",
                   "={{ $json.report }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly Pipeline Report", "Aggregate Pipeline Data"),
        conn("Aggregate Pipeline Data", "Format Pipeline Report"),
        conn("Format Pipeline Report", "Send Pipeline Report"),
    ])
    save(folder, "30-sales-pipeline-report.json",
         workflow("wf-crm-30", "Sales Pipeline Report", ["crm", "reporting"], nodes, connections))

    # 31 - Customer Segmentation
    nodes = [
        schedule_node("n1", "Monthly Segmentation", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Customer Data", "executeQuery",
                      "SELECT id, name, total_revenue, last_purchase_date, purchase_count, avg_order_value FROM customers WHERE status = 'active'",
                      250, 300),
        code_node("n3", "Run Segmentation Logic",
                  "const items = $input.all();\nreturn items.map(item => {\n  const c = item.json;\n  const daysSince = Math.floor((new Date() - new Date(c.last_purchase_date)) / 86400000);\n  let segment;\n  if (c.total_revenue > 50000 && daysSince < 30) segment = 'Champions';\n  else if (c.total_revenue > 20000) segment = 'Loyal Customers';\n  else if (daysSince < 60) segment = 'Recent Customers';\n  else if (daysSince > 180) segment = 'At Risk';\n  else segment = 'Standard';\n  return { json: { ...c, segment, days_since_purchase: daysSince } };\n});",
                  500, 300),
        postgres_node("n4", "Update Customer Segments", "executeQuery",
                      "UPDATE customers SET segment = '{{ $json.segment }}', segmented_at = NOW() WHERE id = {{ $json.id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Monthly Segmentation", "Fetch Customer Data"),
        conn("Fetch Customer Data", "Run Segmentation Logic"),
        conn("Run Segmentation Logic", "Update Customer Segments"),
    ])
    save(folder, "31-customer-segmentation.json",
         workflow("wf-crm-31", "Customer Segmentation", ["crm", "analytics"], nodes, connections))

    # 32 - Lost Deal Analysis
    nodes = [
        webhook_node("n1", "Deal Lost Webhook", "deal-lost", 0, 300),
        http_node("n2", "AI Loss Analysis", "http://ai-backend:8000/crm/analyze-loss", "POST", 250, 300,
                  [{"name": "deal_id", "value": "={{ $json.deal_id }}"}, {"name": "loss_reason", "value": "={{ $json.loss_reason }}"}, {"name": "competitor", "value": "={{ $json.competitor }}"}]),
        postgres_node("n3", "Save Loss Analysis", "executeQuery",
                      "INSERT INTO deal_loss_analysis (deal_id, loss_reason, competitor, ai_insights, recurring_pattern, analyzed_at) VALUES ({{ $json.deal_id }}, '{{ $json.loss_reason }}', '{{ $json.competitor }}', '{{ $json.ai_insights }}', {{ $json.is_recurring_pattern }}, NOW())",
                      500, 300),
        slack_node("n4", "Share Loss Insights", "#crm-sales-insights",
                   ":chart_with_downwards_trend: Deal Lost Analysis\nDeal: *{{ $json.deal_name }}* (${{ $json.deal_value }})\nReason: {{ $json.loss_reason }}\nCompetitor: {{ $json.competitor }}\nInsight: {{ $json.ai_insights }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Deal Lost Webhook", "AI Loss Analysis"),
        conn("AI Loss Analysis", "Save Loss Analysis"),
        conn("Save Loss Analysis", "Share Loss Insights"),
    ])
    save(folder, "32-lost-deal-analysis.json",
         workflow("wf-crm-32", "Lost Deal Analysis", ["crm", "ai", "sales"], nodes, connections))

    # 33 - Sales Performance Report
    nodes = [
        schedule_node("n1", "Monthly Sales Report", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Get Rep Performance Data", "executeQuery",
                      "SELECT u.name, u.email, COUNT(d.id) as total_deals, SUM(CASE WHEN d.status = 'Closed Won' THEN 1 ELSE 0 END) as won, SUM(CASE WHEN d.status = 'Closed Won' THEN d.value ELSE 0 END) as revenue FROM users u LEFT JOIN deals d ON d.assigned_to = u.id AND d.closed_at >= date_trunc('month', NOW() - INTERVAL '1 month') WHERE u.role = 'sales_rep' GROUP BY u.id, u.name, u.email",
                      250, 300),
        code_node("n3", "Calculate Win Rate",
                  "return $input.all().map(item => {\n  const r = item.json;\n  return { json: { ...r, win_rate: r.total_deals > 0 ? ((r.won / r.total_deals) * 100).toFixed(1) : 0 } };\n});",
                  500, 300),
        email_node("n4", "Send Individual Rep Report",
                   "={{ $json.email }}",
                   "Your Monthly Sales Performance Report",
                   "Hi {{ $json.name }},\n\nHere is your performance summary for last month:\n\nTotal Deals: {{ $json.total_deals }}\nDeals Won: {{ $json.won }}\nWin Rate: {{ $json.win_rate }}%\nRevenue Generated: ${{ $json.revenue }}\n\nKeep up the great work!\nSales Operations",
                   750, 300),
    ]
    connections = build_connections([
        conn("Monthly Sales Report", "Get Rep Performance Data"),
        conn("Get Rep Performance Data", "Calculate Win Rate"),
        conn("Calculate Win Rate", "Send Individual Rep Report"),
    ])
    save(folder, "33-sales-performance-report.json",
         workflow("wf-crm-33", "Sales Performance Report", ["crm", "reporting"], nodes, connections))

    # 34 - Demo Scheduling
    nodes = [
        webhook_node("n1", "Demo Request Webhook", "demo-scheduling", 0, 300),
        http_node("n2", "Create Calendar Event", "https://www.googleapis.com/calendar/v3/calendars/primary/events", "POST", 250, 300,
                  [{"name": "summary", "value": "Product Demo — {{ $json.company_name }}"}, {"name": "start", "value": "{{ $json.preferred_time }}"}, {"name": "attendees", "value": "={{ [$json.lead_email, $json.sales_rep_email] }}"}]),
        postgres_node("n3", "Save Demo Record", "executeQuery",
                      "INSERT INTO demos (lead_id, calendar_event_id, scheduled_at, sales_rep_id, status) VALUES ({{ $json.lead_id }}, '{{ $json.id }}', '{{ $json.preferred_time }}', {{ $json.sales_rep_id }}, 'scheduled')",
                      500, 300),
        email_node("n4", "Send Demo Confirmation",
                   "={{ $json.lead_email }}",
                   "Your Product Demo is Confirmed — {{ $json.company_name }}",
                   "Hi {{ $json.lead_name }},\n\nYour product demo has been confirmed!\n\nDate & Time: {{ $json.preferred_time }}\nMeeting Link: {{ $json.meeting_link }}\nYour Host: {{ $json.sales_rep_name }}\n\nLooking forward to showing you what we can do!\n\nBest,\n{{ $json.sales_rep_name }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Demo Request Webhook", "Create Calendar Event"),
        conn("Create Calendar Event", "Save Demo Record"),
        conn("Save Demo Record", "Send Demo Confirmation"),
    ])
    save(folder, "34-demo-scheduling.json",
         workflow("wf-crm-34", "Demo Scheduling", ["crm", "sales"], nodes, connections))

    # 35 - Customer Health Score
    nodes = [
        schedule_node("n1", "Weekly Health Check", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Customer Usage", "executeQuery",
                      "SELECT c.id, c.name, c.email, c.plan_id, AVG(u.daily_active_users) as avg_dau, COUNT(t.id) as support_tickets, MAX(u.date) as last_active FROM customers c LEFT JOIN usage_metrics u ON c.id = u.customer_id AND u.date >= NOW() - INTERVAL '30 days' LEFT JOIN support_tickets t ON c.id = t.customer_id AND t.created_at >= NOW() - INTERVAL '30 days' WHERE c.status = 'active' GROUP BY c.id, c.name, c.email, c.plan_id",
                      250, 300),
        code_node("n3", "Calculate Health Score",
                  "return $input.all().map(item => {\n  const c = item.json;\n  let score = 100;\n  // Penalize for low usage\n  if (c.avg_dau < 5) score -= 30;\n  else if (c.avg_dau < 10) score -= 15;\n  // Penalize for high support tickets\n  if (c.support_tickets > 10) score -= 20;\n  else if (c.support_tickets > 5) score -= 10;\n  // Penalize for inactivity\n  const daysSince = Math.floor((new Date() - new Date(c.last_active)) / 86400000);\n  if (daysSince > 14) score -= 25;\n  const status = score >= 80 ? 'Healthy' : score >= 60 ? 'At Risk' : 'Critical';\n  return { json: { ...c, health_score: Math.max(0, score), health_status: status } };\n});",
                  500, 300),
        postgres_node("n4", "Update Health Scores", "executeQuery",
                      "UPDATE customers SET health_score = {{ $json.health_score }}, health_status = '{{ $json.health_status }}', health_updated_at = NOW() WHERE id = {{ $json.id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Weekly Health Check", "Fetch Customer Usage"),
        conn("Fetch Customer Usage", "Calculate Health Score"),
        conn("Calculate Health Score", "Update Health Scores"),
    ])
    save(folder, "35-customer-health-score.json",
         workflow("wf-crm-35", "Customer Health Score", ["crm", "analytics", "retention"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# INVOICE WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_invoice_workflows():
    folder = "invoice"

    # 36 - Invoice Generation
    nodes = [
        webhook_node("n1", "Deal Close Webhook", "invoice-generate", 0, 300),
        http_node("n2", "Generate Invoice", "http://ai-backend:8000/invoice/generate", "POST", 250, 300,
                  [{"name": "deal_id", "value": "={{ $json.deal_id }}"}, {"name": "customer_id", "value": "={{ $json.customer_id }}"}, {"name": "amount", "value": "={{ $json.amount }}"}]),
        http_node("n3", "Save to MinIO", "http://minio:9000/invoices/{{ $json.invoice_number }}.pdf", "PUT", 500, 300,
                  [{"name": "content", "value": "={{ $json.pdf_base64 }}"}]),
        email_node("n4", "Send Invoice to Client",
                   "={{ $json.client_email }}",
                   "Invoice #{{ $json.invoice_number }} — {{ $json.company_name }}",
                   "Dear {{ $json.client_name }},\n\nPlease find your invoice #{{ $json.invoice_number }} for ${{ $json.amount }}.\n\nDue Date: {{ $json.due_date }}\nDownload: {{ $json.invoice_url }}\nPay Online: {{ $json.payment_link }}\n\nThank you for your business!\nFinance Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Deal Close Webhook", "Generate Invoice"),
        conn("Generate Invoice", "Save to MinIO"),
        conn("Save to MinIO", "Send Invoice to Client"),
    ])
    save(folder, "36-invoice-generation.json",
         workflow("wf-inv-36", "Invoice Generation", ["invoice", "finance"], nodes, connections))

    # 37 - Invoice Approval
    nodes = [
        webhook_node("n1", "Invoice Approval Webhook", "invoice-approval-request", 0, 300),
        postgres_node("n2", "Save Pending Approval", "executeQuery",
                      "INSERT INTO invoice_approvals (invoice_id, amount, requested_by, status, created_at) VALUES ({{ $json.invoice_id }}, {{ $json.amount }}, {{ $json.requested_by }}, 'pending', NOW()) RETURNING approval_token",
                      250, 300),
        slack_node("n3", "Send Approval Request to Finance", "#finance-approvals",
                   ":pencil: Invoice Approval Required!\nInvoice #{{ $json.invoice_number }} — *${{ $json.amount }}*\nClient: {{ $json.client_name }}\nRequested by: {{ $json.requested_by_name }}\n\nApprove: https://portal.company.com/approve/{{ $json.approval_token }}\nReject: https://portal.company.com/reject/{{ $json.approval_token }}",
                   500, 300),
        noop_node("n4", "Await Approval Webhook", 750, 300),
    ]
    connections = build_connections([
        conn("Invoice Approval Webhook", "Save Pending Approval"),
        conn("Save Pending Approval", "Send Approval Request to Finance"),
        conn("Send Approval Request to Finance", "Await Approval Webhook"),
    ])
    save(folder, "37-invoice-approval.json",
         workflow("wf-inv-37", "Invoice Approval", ["invoice", "finance"], nodes, connections))

    def payment_reminder(n, wf_id, filename, days, urgency_msg, extra_action=None):
        nodes_list = [
            schedule_node("n1", "Daily Payment Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
            postgres_node("n2", f"Find {days}-Day Overdue Invoices", "executeQuery",
                          f"SELECT i.*, c.email, c.name as client_name FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.status = 'unpaid' AND i.due_date = (CURRENT_DATE - INTERVAL '{days} days') OR (i.due_date < CURRENT_DATE AND i.overdue_days = {days})",
                          250, 300),
            http_node("n3", "Generate Reminder Email", f"http://ai-backend:8000/invoice/payment-reminder", "POST", 500, 300,
                      [{"name": "invoice_id", "value": "={{ $json.id }}"}, {"name": "days_overdue", "value": str(days)}, {"name": "urgency", "value": urgency_msg}]),
            email_node("n4", "Send Payment Reminder",
                       "={{ $json.email }}",
                       f"[{'URGENT: ' if days >= 14 else ''}Payment Reminder] Invoice #{{{{ $json.invoice_number }}}} — {days} Day{'s' if days != 1 else ''} {'Overdue' if days > 0 else 'Due Today'}",
                       "={{ $json.reminder_email_body }}",
                       750, 300),
        ]
        connections = build_connections([
            conn("Daily Payment Check", f"Find {days}-Day Overdue Invoices"),
            conn(f"Find {days}-Day Overdue Invoices", "Generate Reminder Email"),
            conn("Generate Reminder Email", "Send Payment Reminder"),
        ])
        save(folder, filename,
             workflow(wf_id, f"Payment Reminder — {days} {'Day Overdue' if days > 0 else 'Day Due'}", ["invoice", "finance"], nodes_list, connections))

    payment_reminder(38, "wf-inv-38", "38-payment-reminder-day1.json", 1, "friendly")
    payment_reminder(39, "wf-inv-39", "39-payment-reminder-day7.json", 7, "moderate")
    payment_reminder(40, "wf-inv-40", "40-payment-reminder-day14.json", 14, "firm")
    payment_reminder(41, "wf-inv-41", "41-payment-reminder-day30.json", 30, "final_notice")

    # 42 - Overdue Escalation
    nodes = [
        webhook_node("n1", "Escalation Webhook", "invoice-escalation", 0, 300),
        postgres_node("n2", "Create Legal Task", "executeQuery",
                      "INSERT INTO legal_tasks (invoice_id, task_type, description, priority, created_at) VALUES ({{ $json.invoice_id }}, 'legal_notice', 'Send legal notice for unpaid invoice #{{ $json.invoice_number }} (${{ $json.amount }})', 'urgent', NOW())",
                      250, 300),
        http_node("n3", "Create Jira Escalation Ticket", "http://jira-api:8080/rest/api/2/issue", "POST", 500, 300,
                  [{"name": "summary", "value": "Legal Escalation: Invoice {{ $json.invoice_number }}"}, {"name": "priority", "value": "Urgent"}, {"name": "description", "value": "Invoice {{ $json.invoice_number }} for ${{ $json.amount }} is 30+ days overdue. Client: {{ $json.client_name }}"}]),
        slack_node("n4", "Alert Finance Team", "#finance-escalations",
                   ":rotating_light: *INVOICE ESCALATION*\nInvoice #{{ $json.invoice_number }} — *${{ $json.amount }}* is 30+ days overdue!\nClient: {{ $json.client_name }}\nJira Ticket: {{ $json.key }}\nImmediate action required.",
                   750, 300),
    ]
    connections = build_connections([
        conn("Escalation Webhook", "Create Legal Task"),
        conn("Create Legal Task", "Create Jira Escalation Ticket"),
        conn("Create Jira Escalation Ticket", "Alert Finance Team"),
    ])
    save(folder, "42-overdue-escalation.json",
         workflow("wf-inv-42", "Overdue Invoice Escalation", ["invoice", "finance", "legal"], nodes, connections))

    # 43 - Payment Received
    nodes = [
        webhook_node("n1", "Payment Gateway Webhook", "payment-received", 0, 300),
        postgres_node("n2", "Update Invoice Status", "executeQuery",
                      "UPDATE invoices SET status = 'paid', paid_at = NOW(), payment_method = '{{ $json.payment_method }}', transaction_id = '{{ $json.transaction_id }}' WHERE id = {{ $json.invoice_id }} RETURNING invoice_number, amount, customer_id",
                      250, 300),
        http_node("n3", "Generate Receipt", "http://ai-backend:8000/invoice/generate-receipt", "POST", 500, 300,
                  [{"name": "invoice_id", "value": "={{ $json.invoice_id }}"}, {"name": "amount", "value": "={{ $json.amount }}"}, {"name": "transaction_id", "value": "={{ $json.transaction_id }}"}]),
        email_node("n4", "Send Payment Receipt",
                   "={{ $json.client_email }}",
                   "Payment Confirmed — Receipt #{{ $json.receipt_number }}",
                   "Dear {{ $json.client_name }},\n\nWe have received your payment of ${{ $json.amount }} for Invoice #{{ $json.invoice_number }}.\n\nTransaction ID: {{ $json.transaction_id }}\nPayment Date: {{ $json.paid_at }}\nReceipt: {{ $json.receipt_url }}\n\nThank you!\nFinance Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Payment Gateway Webhook", "Update Invoice Status"),
        conn("Update Invoice Status", "Generate Receipt"),
        conn("Generate Receipt", "Send Payment Receipt"),
    ])
    save(folder, "43-payment-received.json",
         workflow("wf-inv-43", "Payment Received", ["invoice", "finance"], nodes, connections))

    # 44 - Expense Report
    nodes = [
        form_node("n1", "Expense Report Form", "Employee Expense Report", [
            {"fieldLabel": "Employee ID", "fieldType": "text", "requiredField": True},
            {"fieldLabel": "Expense Date", "fieldType": "date", "requiredField": True},
            {"fieldLabel": "Amount", "fieldType": "number", "requiredField": True},
            {"fieldLabel": "Category", "fieldType": "dropdown", "fieldOptions": {"values": [{"option": "Travel"}, {"option": "Meals"}, {"option": "Software"}, {"option": "Office"}, {"option": "Other"}]}, "requiredField": True},
            {"fieldLabel": "Description", "fieldType": "textarea", "requiredField": True},
            {"fieldLabel": "Receipt URL", "fieldType": "text", "requiredField": False},
        ], 0, 300),
        http_node("n2", "AI Categorize Expense", "http://ai-backend:8000/invoice/categorize-expense", "POST", 250, 300,
                  [{"name": "description", "value": "={{ $json.Description }}"}, {"name": "amount", "value": "={{ $json.Amount }}"}, {"name": "category", "value": "={{ $json.Category }}"}]),
        postgres_node("n3", "Save Expense", "executeQuery",
                      "INSERT INTO expenses (employee_id, amount, category, ai_category, description, receipt_url, expense_date, status) VALUES ('{{ $json[\"Employee ID\"] }}', {{ $json.Amount }}, '{{ $json.Category }}', '{{ $json.ai_category }}', '{{ $json.Description }}', '{{ $json[\"Receipt URL\"] }}', '{{ $json[\"Expense Date\"] }}', 'pending_approval')",
                      500, 300),
        slack_node("n4", "Notify Finance for Approval", "#finance-expenses",
                   ":receipt: New expense report submitted!\nEmployee: {{ $json.employee_name }}\nAmount: *${{ $json.Amount }}*\nCategory: {{ $json.ai_category }}\nDescription: {{ $json.Description }}\nApprove: https://portal.company.com/expenses/{{ $json.expense_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Expense Report Form", "AI Categorize Expense"),
        conn("AI Categorize Expense", "Save Expense"),
        conn("Save Expense", "Notify Finance for Approval"),
    ])
    save(folder, "44-expense-report.json",
         workflow("wf-inv-44", "Expense Report", ["invoice", "finance", "hr"], nodes, connections))

    # 45 - Receipt OCR
    nodes = [
        webhook_node("n1", "Receipt Upload Webhook", "receipt-ocr", 0, 300),
        http_node("n2", "Parse Receipt with OCR", "http://ai-backend:8000/documents/parse", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.receipt_url }}"}, {"name": "document_type", "value": "receipt"}, {"name": "extract_fields", "value": "amount,vendor,date,tax,category"}]),
        set_node("n3", "Map Extracted Data", {
            "amount": "={{ $json.extracted.amount }}",
            "vendor": "={{ $json.extracted.vendor }}",
            "date": "={{ $json.extracted.date }}",
            "tax": "={{ $json.extracted.tax }}",
            "category": "={{ $json.extracted.category }}",
        }, 500, 300),
        postgres_node("n4", "Save OCR Result", "executeQuery",
                      "INSERT INTO receipt_ocr_results (employee_id, receipt_url, amount, vendor, expense_date, tax, category, confidence, processed_at) VALUES ({{ $json.employee_id }}, '{{ $json.receipt_url }}', {{ $json.amount }}, '{{ $json.vendor }}', '{{ $json.date }}', {{ $json.tax }}, '{{ $json.category }}', {{ $json.confidence }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Receipt Upload Webhook", "Parse Receipt with OCR"),
        conn("Parse Receipt with OCR", "Map Extracted Data"),
        conn("Map Extracted Data", "Save OCR Result"),
    ])
    save(folder, "45-receipt-ocr.json",
         workflow("wf-inv-45", "Receipt OCR Processing", ["invoice", "documents", "ai"], nodes, connections))

    # 46 - Budget Alert
    nodes = [
        schedule_node("n1", "Daily Budget Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Check Budget Utilization", "executeQuery",
                      "SELECT d.name as department, b.budget_amount, SUM(e.amount) as spent, SUM(e.amount) / b.budget_amount * 100 as utilization_pct FROM budget b JOIN departments d ON b.department_id = d.id LEFT JOIN expenses e ON e.department_id = d.id AND e.expense_date >= date_trunc('month', NOW()) WHERE b.period = date_trunc('month', NOW()) GROUP BY d.name, b.budget_amount HAVING SUM(e.amount) / b.budget_amount >= 0.8",
                      250, 300),
        if_node("n3", "Over Budget?", "={{ $json.utilization_pct }}", "largerEqual", "100", 500, 300),
        slack_node("n4", "Over Budget Alert", "#finance-alerts",
                   ":red_circle: *BUDGET EXCEEDED!*\nDepartment: *{{ $json.department }}*\nBudget: ${{ $json.budget_amount }}\nSpent: ${{ $json.spent }} ({{ $json.utilization_pct.toFixed(1) }}%)\nImmediate review required!",
                   750, 200),
        slack_node("n5", "Budget Warning Alert", "#finance-alerts",
                   ":yellow_circle: *Budget Warning — {{ $json.department }}*\nUtilization: {{ $json.utilization_pct.toFixed(1) }}% (${{ $json.spent }} of ${{ $json.budget_amount }})\nMonitor closely.",
                   750, 400),
    ]
    connections = build_connections([
        conn("Daily Budget Check", "Check Budget Utilization"),
        conn("Check Budget Utilization", "Over Budget?"),
        conn("Over Budget?", "Over Budget Alert", 0, 0),
        conn("Over Budget?", "Budget Warning Alert", 1, 0),
    ])
    save(folder, "46-budget-alert.json",
         workflow("wf-inv-46", "Budget Alert", ["invoice", "finance"], nodes, connections))

    # 47 - Monthly Financial Summary
    nodes = [
        schedule_node("n1", "Monthly Financial Schedule", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate Financial Data", "executeQuery",
                      "SELECT SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as revenue, SUM(CASE WHEN status = 'unpaid' AND due_date < NOW() THEN amount ELSE 0 END) as overdue, COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_count, COUNT(CASE WHEN status = 'unpaid' AND due_date < NOW() THEN 1 END) as overdue_count, (SELECT SUM(amount) FROM expenses WHERE status = 'approved' AND expense_date >= date_trunc('month', NOW() - INTERVAL '1 month')) as total_expenses FROM invoices WHERE created_at >= date_trunc('month', NOW() - INTERVAL '1 month')",
                      250, 300),
        code_node("n3", "Format CFO Report",
                  "const d = $input.first().json;\nconst profit = d.revenue - d.total_expenses;\nconst report = `Monthly Financial Summary\\n${'='.repeat(40)}\\n` +\n  `Revenue: $${parseFloat(d.revenue).toLocaleString()} (${d.paid_count} invoices)\\n` +\n  `Expenses: $${parseFloat(d.total_expenses).toLocaleString()}\\n` +\n  `Net Profit: $${parseFloat(profit).toLocaleString()}\\n` +\n  `Overdue AR: $${parseFloat(d.overdue).toLocaleString()} (${d.overdue_count} invoices)\\n` +\n  `Profit Margin: ${(profit/d.revenue*100).toFixed(1)}%`;\nreturn [{json:{report, profit}}];",
                  500, 300),
        email_node("n4", "Send CFO Report",
                   "cfo@company.com",
                   "Monthly Financial Summary — {{ $now.format('MMMM YYYY') }}",
                   "={{ $json.report }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Monthly Financial Schedule", "Aggregate Financial Data"),
        conn("Aggregate Financial Data", "Format CFO Report"),
        conn("Format CFO Report", "Send CFO Report"),
    ])
    save(folder, "47-monthly-financial-summary.json",
         workflow("wf-inv-47", "Monthly Financial Summary", ["invoice", "finance", "reporting"], nodes, connections))

    # 48 - Tax Document Collection
    nodes = [
        schedule_node("n1", "January Annual Schedule", {"interval": [{"field": "months", "monthsInterval": 12}]}, 0, 300),
        postgres_node("n2", "Get All Active Clients", "executeQuery",
                      "SELECT id, name, email, tax_id, account_manager_email FROM customers WHERE status = 'active' AND billing_type IN ('annual', 'contract')",
                      250, 300),
        set_node("n3", "Prepare Tax Request", {
            "subject": "Annual Tax Document Collection — Action Required",
            "body": "=Dear {{ $json.name }},\n\nAs part of our annual tax preparation, we need the following documents:\n1. W-9 / Tax Identification Form\n2. Previous year financial statements\n3. Updated business registration\n\nPlease submit via: https://portal.company.com/tax-docs/{{ $json.id }}\nDeadline: January 31st\n\nFinance Team",
        }, 500, 300),
        email_node("n4", "Send Tax Request Email",
                   "={{ $json.email }}",
                   "={{ $json.subject }}",
                   "={{ $json.body }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("January Annual Schedule", "Get All Active Clients"),
        conn("Get All Active Clients", "Prepare Tax Request"),
        conn("Prepare Tax Request", "Send Tax Request Email"),
    ])
    save(folder, "48-tax-document-collection.json",
         workflow("wf-inv-48", "Tax Document Collection", ["invoice", "finance", "compliance"], nodes, connections))

    # 49 - Vendor Payment
    nodes = [
        schedule_node("n1", "Weekly Vendor Payment Run", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Approved Vendor Invoices", "executeQuery",
                      "SELECT vi.*, v.name as vendor_name, v.bank_account, v.routing_number FROM vendor_invoices vi JOIN vendors v ON vi.vendor_id = v.id WHERE vi.status = 'approved' AND vi.due_date <= CURRENT_DATE + INTERVAL '7 days'",
                      250, 300),
        http_node("n3", "Initiate Bank Payment", "https://api.banking-provider.com/v1/transfers", "POST", 500, 300,
                  [{"name": "amount", "value": "={{ $json.amount }}"}, {"name": "account_number", "value": "={{ $json.bank_account }}"}, {"name": "routing_number", "value": "={{ $json.routing_number }}"}, {"name": "reference", "value": "={{ $json.invoice_number }}"}]),
        postgres_node("n4", "Update Payment Status", "executeQuery",
                      "UPDATE vendor_invoices SET status = 'paid', paid_at = NOW(), transaction_id = '{{ $json.transaction_id }}' WHERE id = {{ $json.id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Weekly Vendor Payment Run", "Find Approved Vendor Invoices"),
        conn("Find Approved Vendor Invoices", "Initiate Bank Payment"),
        conn("Initiate Bank Payment", "Update Payment Status"),
    ])
    save(folder, "49-vendor-payment.json",
         workflow("wf-inv-49", "Vendor Payment", ["invoice", "finance"], nodes, connections))

    # 50 - Subscription Renewal Billing
    nodes = [
        schedule_node("n1", "Monthly Subscription Billing", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Renewing Subscriptions", "executeQuery",
                      "SELECT s.*, c.name as customer_name, c.email, c.stripe_customer_id FROM subscriptions s JOIN customers c ON s.customer_id = c.id WHERE s.status = 'active' AND s.renewal_date = CURRENT_DATE",
                      250, 300),
        http_node("n3", "Charge Subscription", "https://api.stripe.com/v1/invoices", "POST", 500, 300,
                  [{"name": "customer", "value": "={{ $json.stripe_customer_id }}"}, {"name": "auto_advance", "value": "true"}, {"name": "collection_method", "value": "charge_automatically"}]),
        email_node("n4", "Send Updated Invoice",
                   "={{ $json.email }}",
                   "Subscription Renewed — Invoice #{{ $json.invoice_number }}",
                   "Dear {{ $json.customer_name }},\n\nYour {{ $json.plan_name }} subscription has been renewed.\n\nAmount: ${{ $json.amount }}\nNext Billing Date: {{ $json.next_renewal_date }}\nInvoice: {{ $json.invoice_url }}\n\nThank you for your continued subscription!\nBilling Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Monthly Subscription Billing", "Find Renewing Subscriptions"),
        conn("Find Renewing Subscriptions", "Charge Subscription"),
        conn("Charge Subscription", "Send Updated Invoice"),
    ])
    save(folder, "50-subscription-renewal-billing.json",
         workflow("wf-inv-50", "Subscription Renewal Billing", ["invoice", "finance", "subscriptions"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_email_workflows():
    folder = "email"

    # 51 - Email Triage
    nodes = [
        webhook_node("n1", "Email Inbox Webhook", "email-triage", 0, 300),
        http_node("n2", "AI Classify Email", "http://ai-backend:8000/email/classify", "POST", 250, 300,
                  [{"name": "subject", "value": "={{ $json.subject }}"}, {"name": "body", "value": "={{ $json.body }}"}, {"name": "sender", "value": "={{ $json.from }}"}]),
        if_node("n3", "Is Urgent?", "={{ $json.urgency }}", "equals", "high", 500, 300),
        slack_node("n4", "Alert Responsible Person", "={{ $json.assigned_slack_channel }}",
                   ":rotating_light: URGENT Email!\nFrom: {{ $json.from }}\nSubject: {{ $json.subject }}\nCategory: {{ $json.category }}\nSummary: {{ $json.ai_summary }}",
                   750, 200),
        postgres_node("n5", "Log Email & Route", "executeQuery",
                      "INSERT INTO email_triage_log (sender, subject, urgency, category, assigned_to, received_at) VALUES ('{{ $json.from }}', '{{ $json.subject }}', '{{ $json.urgency }}', '{{ $json.category }}', '{{ $json.assigned_to }}', NOW())",
                      750, 400),
    ]
    connections = build_connections([
        conn("Email Inbox Webhook", "AI Classify Email"),
        conn("AI Classify Email", "Is Urgent?"),
        conn("Is Urgent?", "Alert Responsible Person", 0, 0),
        conn("Is Urgent?", "Log Email & Route", 1, 0),
    ])
    save(folder, "51-email-triage.json",
         workflow("wf-email-51", "Email Triage", ["email", "ai"], nodes, connections))

    # 52 - Auto Reply Common
    nodes = [
        webhook_node("n1", "Incoming Email Webhook", "auto-reply", 0, 300),
        http_node("n2", "Match Common Query", "http://ai-backend:8000/email/match-faq", "POST", 250, 300,
                  [{"name": "subject", "value": "={{ $json.subject }}"}, {"name": "body", "value": "={{ $json.body }}"}]),
        if_node("n3", "FAQ Match Found?", "={{ $json.confidence }}", "largerEqual", "0.85", 500, 300),
        email_node("n4", "Send Auto Reply",
                   "={{ $json.from }}",
                   "Re: {{ $json.subject }}",
                   "={{ $json.faq_answer }}\n\n---\nThis is an automated response. If this doesn't answer your question, a human agent will follow up.\n\nSupport Team",
                   750, 200),
        postgres_node("n5", "Log for Human Review", "executeQuery",
                      "INSERT INTO email_queue (sender, subject, body, status, received_at) VALUES ('{{ $json.from }}', '{{ $json.subject }}', '{{ $json.body }}', 'needs_human', NOW())",
                      750, 400),
    ]
    connections = build_connections([
        conn("Incoming Email Webhook", "Match Common Query"),
        conn("Match Common Query", "FAQ Match Found?"),
        conn("FAQ Match Found?", "Send Auto Reply", 0, 0),
        conn("FAQ Match Found?", "Log for Human Review", 1, 0),
    ])
    save(folder, "52-auto-reply-common.json",
         workflow("wf-email-52", "Auto Reply Common Queries", ["email", "ai", "support"], nodes, connections))

    # 53 - Newsletter Send
    nodes = [
        schedule_node("n1", "Newsletter Schedule", {"interval": [{"field": "weeks", "weeksInterval": 2}]}, 0, 300),
        http_node("n2", "Fetch Newsletter Content", "http://cms-api:3000/api/newsletter/latest", "GET", 250, 300),
        postgres_node("n3", "Get Subscriber List", "executeQuery",
                      "SELECT email, first_name, preferences FROM newsletter_subscribers WHERE status = 'active' AND unsubscribed_at IS NULL",
                      500, 300),
        email_node("n4", "Send Newsletter Batch",
                   "={{ $json.email }}",
                   "={{ $json.newsletter_subject }}",
                   "Hi {{ $json.first_name }},\n\n{{ $json.newsletter_html }}\n\n---\nUnsubscribe: https://newsletter.company.com/unsubscribe?token={{ $json.unsubscribe_token }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Newsletter Schedule", "Fetch Newsletter Content"),
        conn("Fetch Newsletter Content", "Get Subscriber List"),
        conn("Get Subscriber List", "Send Newsletter Batch"),
    ])
    save(folder, "53-newsletter-send.json",
         workflow("wf-email-53", "Newsletter Send", ["email", "marketing"], nodes, connections))

    # 54 - Slack Email Digest
    nodes = [
        schedule_node("n1", "Twice Daily Schedule", {"interval": [{"field": "hours", "hoursInterval": 12}]}, 0, 300),
        http_node("n2", "Fetch Important Emails", "http://email-api:3000/api/important-unread", "GET", 250, 300,
                  [{"name": "limit", "value": "10"}, {"name": "since_hours", "value": "12"}]),
        code_node("n3", "Format Email Digest",
                  "const emails = $input.first().json.emails || [];\nif (emails.length === 0) return [{json:{digest: 'No important emails in the last 12 hours.', count: 0}}];\nconst lines = emails.map((e, i) => `${i+1}. *${e.subject}* — From: ${e.from} (${e.received_at})`);\nconst digest = `📧 *Email Digest* (Last 12h)\\n${lines.join('\\n')}`;\nreturn [{json:{digest, count: emails.length}}];",
                  500, 300),
        slack_node("n4", "Post Digest to Exec Channel", "#executive-updates",
                   "={{ $json.digest }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Twice Daily Schedule", "Fetch Important Emails"),
        conn("Fetch Important Emails", "Format Email Digest"),
        conn("Format Email Digest", "Post Digest to Exec Channel"),
    ])
    save(folder, "54-slack-email-digest.json",
         workflow("wf-email-54", "Slack Email Digest", ["email", "slack"], nodes, connections))

    # 55 - WhatsApp Urgent
    nodes = [
        webhook_node("n1", "High Priority Email Webhook", "whatsapp-urgent", 0, 300),
        if_node("n2", "Is High Priority?", "={{ $json.priority }}", "equals", "urgent", 250, 300),
        http_node("n3", "Send WhatsApp Notification", "https://api.whatsapp-provider.com/v1/messages", "POST", 500, 200,
                  [{"name": "to", "value": "={{ $json.recipient_phone }}"}, {"name": "type", "value": "text"}, {"name": "text", "value": "🚨 URGENT Email: {{ $json.subject }}\nFrom: {{ $json.from }}\nSummary: {{ $json.summary }}\n\nCheck your inbox immediately."}]),
        noop_node("n4", "Non-Urgent Skip", 500, 400),
        postgres_node("n5", "Log WhatsApp Notification", "executeQuery",
                      "INSERT INTO whatsapp_notifications (email_id, recipient, message, sent_at) VALUES ('{{ $json.email_id }}', '{{ $json.recipient_phone }}', '{{ $json.subject }}', NOW())",
                      750, 200),
    ]
    connections = build_connections([
        conn("High Priority Email Webhook", "Is High Priority?"),
        conn("Is High Priority?", "Send WhatsApp Notification", 0, 0),
        conn("Is High Priority?", "Non-Urgent Skip", 1, 0),
        conn("Send WhatsApp Notification", "Log WhatsApp Notification"),
    ])
    save(folder, "55-whatsapp-urgent.json",
         workflow("wf-email-55", "WhatsApp Urgent Notification", ["email", "notifications"], nodes, connections))

    # 56 - Email Sentiment
    nodes = [
        webhook_node("n1", "Email Sentiment Webhook", "email-sentiment", 0, 300),
        http_node("n2", "AI Sentiment Analysis", "http://ai-backend:8000/email/sentiment", "POST", 250, 300,
                  [{"name": "subject", "value": "={{ $json.subject }}"}, {"name": "body", "value": "={{ $json.body }}"}, {"name": "sender", "value": "={{ $json.from }}"}]),
        postgres_node("n3", "Save Sentiment Result", "executeQuery",
                      "INSERT INTO email_sentiment_log (email_id, sender, subject, sentiment, sentiment_score, flags, analyzed_at) VALUES ('{{ $json.email_id }}', '{{ $json.from }}', '{{ $json.subject }}', '{{ $json.sentiment }}', {{ $json.sentiment_score }}, '{{ $json.flags }}', NOW())",
                      500, 300),
        if_node("n4", "Negative Sentiment?", "={{ $json.sentiment }}", "equals", "negative", 750, 300),
        slack_node("n5", "Flag for Immediate Attention", "#customer-success-alerts",
                   ":warning: Negative Email Detected!\nFrom: {{ $json.from }}\nSubject: {{ $json.subject }}\nSentiment Score: {{ $json.sentiment_score }}/10\nFlags: {{ $json.flags }}\nPlease respond within 2 hours.",
                   1000, 200),
        noop_node("n6", "Positive/Neutral Skip", 1000, 400),
    ]
    connections = build_connections([
        conn("Email Sentiment Webhook", "AI Sentiment Analysis"),
        conn("AI Sentiment Analysis", "Save Sentiment Result"),
        conn("Save Sentiment Result", "Negative Sentiment?"),
        conn("Negative Sentiment?", "Flag for Immediate Attention", 0, 0),
        conn("Negative Sentiment?", "Positive/Neutral Skip", 1, 0),
    ])
    save(folder, "56-email-sentiment.json",
         workflow("wf-email-56", "Email Sentiment Analysis", ["email", "ai", "support"], nodes, connections))

    # 57 - Unsubscribe Processing
    nodes = [
        webhook_node("n1", "Unsubscribe Webhook", "email-unsubscribe", 0, 300),
        postgres_node("n2", "Remove from Mailing List", "executeQuery",
                      "UPDATE newsletter_subscribers SET status = 'unsubscribed', unsubscribed_at = NOW(), unsubscribe_reason = '{{ $json.reason }}' WHERE email = '{{ $json.email }}'",
                      250, 300),
        postgres_node("n3", "Log Unsubscribe Event", "executeQuery",
                      "INSERT INTO unsubscribe_log (email, reason, source, unsubscribed_at) VALUES ('{{ $json.email }}', '{{ $json.reason }}', '{{ $json.source }}', NOW())",
                      500, 300),
        email_node("n4", "Send Unsubscribe Confirmation",
                   "={{ $json.email }}",
                   "You've been unsubscribed",
                   "Hi,\n\nYou have been successfully unsubscribed from our mailing list.\n\nIf this was a mistake, you can re-subscribe at: https://newsletter.company.com/subscribe\n\nWe're sorry to see you go!\n\nMarketing Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Unsubscribe Webhook", "Remove from Mailing List"),
        conn("Remove from Mailing List", "Log Unsubscribe Event"),
        conn("Log Unsubscribe Event", "Send Unsubscribe Confirmation"),
    ])
    save(folder, "57-unsubscribe-processing.json",
         workflow("wf-email-57", "Unsubscribe Processing", ["email", "marketing"], nodes, connections))

    # 58 - Email Personalization
    nodes = [
        webhook_node("n1", "Email Personalize Webhook", "email-personalization", 0, 300),
        postgres_node("n2", "Fetch Customer Data", "executeQuery",
                      "SELECT c.*, s.plan_name, c.last_login, c.total_orders FROM customers c LEFT JOIN subscriptions s ON c.subscription_id = s.id WHERE c.id = {{ $json.customer_id }}",
                      250, 300),
        http_node("n3", "Personalize Email Template", "http://ai-backend:8000/email/personalize", "POST", 500, 300,
                  [{"name": "template_id", "value": "={{ $json.template_id }}"}, {"name": "customer_data", "value": "={{ $json }}"}, {"name": "context", "value": "={{ $json.context }}"}]),
        email_node("n4", "Send Personalized Email",
                   "={{ $json.email }}",
                   "={{ $json.personalized_subject }}",
                   "={{ $json.personalized_body }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Email Personalize Webhook", "Fetch Customer Data"),
        conn("Fetch Customer Data", "Personalize Email Template"),
        conn("Personalize Email Template", "Send Personalized Email"),
    ])
    save(folder, "58-email-personalization.json",
         workflow("wf-email-58", "Email Personalization", ["email", "ai", "marketing"], nodes, connections))

    # 59 - Follow-up Sequences
    nodes = [
        schedule_node("n1", "Daily Followup Check", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Due Follow-up Steps", "executeQuery",
                      "SELECT fs.*, c.email, c.name FROM followup_sequence_steps fs JOIN customers c ON fs.customer_id = c.id WHERE fs.status = 'pending' AND fs.scheduled_for <= NOW() ORDER BY fs.scheduled_for ASC LIMIT 100",
                      250, 300),
        set_node("n3", "Prepare Email Data", {
            "to_email": "={{ $json.email }}",
            "subject": "={{ $json.email_subject }}",
            "body": "={{ $json.email_body }}",
            "step_id": "={{ $json.id }}",
        }, 500, 300),
        email_node("n4", "Send Follow-up Email",
                   "={{ $json.to_email }}",
                   "={{ $json.subject }}",
                   "={{ $json.body }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily Followup Check", "Fetch Due Follow-up Steps"),
        conn("Fetch Due Follow-up Steps", "Prepare Email Data"),
        conn("Prepare Email Data", "Send Follow-up Email"),
    ])
    save(folder, "59-followup-sequences.json",
         workflow("wf-email-59", "Follow-up Sequences", ["email", "crm"], nodes, connections))

    # 60 - Executive Email Summary
    nodes = [
        schedule_node("n1", "Daily 8AM Schedule", {"interval": [{"field": "hours", "hoursInterval": 24}]}, 0, 300),
        http_node("n2", "Fetch CEO Important Emails", "http://email-api:3000/api/inbox/ceo/important", "GET", 250, 300,
                  [{"name": "limit", "value": "20"}, {"name": "since", "value": "24h"}]),
        http_node("n3", "Generate AI Summary", "http://ai-backend:8000/email/executive-summary", "POST", 500, 300,
                  [{"name": "emails", "value": "={{ $json.emails }}"}, {"name": "role", "value": "CEO"}, {"name": "focus_areas", "value": "urgent,decisions,opportunities"}]),
        email_node("n4", "Send Executive Summary",
                   "ceo@company.com",
                   "📧 Your Morning Email Summary — {{ $now.format('MMMM DD, YYYY') }}",
                   "Good morning,\n\nHere is your AI-generated email summary for today:\n\n{{ $json.executive_summary }}\n\n---\nImportant emails requiring your attention: {{ $json.action_required_count }}\nTotal emails processed: {{ $json.total_emails }}\n\nYour AI Assistant",
                   750, 300),
    ]
    connections = build_connections([
        conn("Daily 8AM Schedule", "Fetch CEO Important Emails"),
        conn("Fetch CEO Important Emails", "Generate AI Summary"),
        conn("Generate AI Summary", "Send Executive Summary"),
    ])
    save(folder, "60-executive-email-summary.json",
         workflow("wf-email-60", "Executive Email Summary", ["email", "ai", "executive"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_kb_workflows():
    folder = "knowledge_base"

    # 61 - Document Ingestion
    nodes = [
        webhook_node("n1", "Document Upload Webhook", "kb-document-ingest", 0, 300),
        http_node("n2", "Parse Document", "http://ai-backend:8000/documents/parse", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "document_type", "value": "={{ $json.document_type }}"}]),
        http_node("n3", "Store in Qdrant Vector DB", "http://qdrant:6333/collections/knowledge_base/points", "PUT", 500, 300,
                  [{"name": "points", "value": "[{\"id\": \"{{ $json.doc_id }}\", \"vector\": {{ $json.embedding }}, \"payload\": {\"text\": \"{{ $json.content }}\", \"source\": \"{{ $json.document_url }}\", \"type\": \"{{ $json.document_type }}\"}}]"}]),
        postgres_node("n4", "Save Document Metadata", "executeQuery",
                      "INSERT INTO kb_documents (title, source_url, document_type, qdrant_id, indexed_at, created_by) VALUES ('{{ $json.title }}', '{{ $json.document_url }}', '{{ $json.document_type }}', '{{ $json.doc_id }}', NOW(), {{ $json.user_id }})",
                      750, 300),
    ]
    connections = build_connections([
        conn("Document Upload Webhook", "Parse Document"),
        conn("Parse Document", "Store in Qdrant Vector DB"),
        conn("Store in Qdrant Vector DB", "Save Document Metadata"),
    ])
    save(folder, "61-document-ingestion.json",
         workflow("wf-kb-61", "Document Ingestion", ["knowledge_base", "documents"], nodes, connections))

    # 62 - FAQ Generation
    nodes = [
        schedule_node("n1", "Weekly FAQ Generation", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Support Tickets", "executeQuery",
                      "SELECT id, subject, description, resolution FROM support_tickets WHERE status = 'resolved' AND created_at >= NOW() - INTERVAL '7 days' AND faq_generated = false LIMIT 100",
                      250, 300),
        http_node("n3", "Generate FAQs with AI", "http://ai-backend:8000/kb/generate-faqs", "POST", 500, 300,
                  [{"name": "tickets", "value": "={{ $json }}"}, {"name": "format", "value": "qa_pairs"}]),
        postgres_node("n4", "Save FAQs to KB", "executeQuery",
                      "INSERT INTO kb_faqs (question, answer, category, source_ticket_ids, generated_at) SELECT question, answer, category, source_ids, NOW() FROM json_array_elements('{{ $json.faqs }}'::json) AS faq(question text, answer text, category text, source_ids text)",
                      750, 300),
    ]
    connections = build_connections([
        conn("Weekly FAQ Generation", "Fetch Support Tickets"),
        conn("Fetch Support Tickets", "Generate FAQs with AI"),
        conn("Generate FAQs with AI", "Save FAQs to KB"),
    ])
    save(folder, "62-faq-generation.json",
         workflow("wf-kb-62", "FAQ Generation", ["knowledge_base", "ai", "support"], nodes, connections))

    # 63 - Knowledge Search
    nodes = [
        webhook_node("n1", "Knowledge Search Webhook", "kb-search", 0, 300),
        http_node("n2", "Search Qdrant Vector DB", "http://qdrant:6333/collections/knowledge_base/points/search", "POST", 250, 300,
                  [{"name": "vector", "value": "={{ $json.query_embedding }}"}, {"name": "limit", "value": "5"}, {"name": "with_payload", "value": "true"}]),
        set_node("n3", "Format Search Results", {
            "query": "={{ $json.query }}",
            "results": "={{ $json.result.map(r => ({score: r.score, text: r.payload.text, source: r.payload.source})) }}",
            "top_result": "={{ $json.result[0]?.payload?.text || 'No results found' }}",
        }, 500, 300),
        postgres_node("n4", "Log Search Query", "executeQuery",
                      "INSERT INTO kb_search_log (query, results_count, user_id, searched_at) VALUES ('{{ $json.query }}', {{ $json.results.length }}, {{ $json.user_id }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Knowledge Search Webhook", "Search Qdrant Vector DB"),
        conn("Search Qdrant Vector DB", "Format Search Results"),
        conn("Format Search Results", "Log Search Query"),
    ])
    save(folder, "63-knowledge-search.json",
         workflow("wf-kb-63", "Knowledge Search", ["knowledge_base"], nodes, connections))

    # 64 - Outdated Content Flagging
    nodes = [
        schedule_node("n1", "Monthly Content Audit", {"interval": [{"field": "months", "monthsInterval": 1}]}, 0, 300),
        postgres_node("n2", "Find Outdated Documents", "executeQuery",
                      "SELECT d.*, u.email as owner_email, u.name as owner_name FROM kb_documents d JOIN users u ON d.created_by = u.id WHERE d.updated_at < NOW() - INTERVAL '6 months' AND d.status = 'active'",
                      250, 300),
        postgres_node("n3", "Flag as Outdated", "executeQuery",
                      "UPDATE kb_documents SET status = 'review_needed', flagged_at = NOW() WHERE id = {{ $json.id }}",
                      500, 300),
        email_node("n4", "Notify Content Owner",
                   "={{ $json.owner_email }}",
                   "Action Required: Review Outdated Content — {{ $json.title }}",
                   "Hi {{ $json.owner_name }},\n\nThe following knowledge base article needs your review:\n\nTitle: {{ $json.title }}\nLast Updated: {{ $json.updated_at }}\nView: https://kb.company.com/docs/{{ $json.id }}\n\nPlease review and update or archive this content.\n\nKnowledge Base Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Monthly Content Audit", "Find Outdated Documents"),
        conn("Find Outdated Documents", "Flag as Outdated"),
        conn("Flag as Outdated", "Notify Content Owner"),
    ])
    save(folder, "64-outdated-content-flagging.json",
         workflow("wf-kb-64", "Outdated Content Flagging", ["knowledge_base", "content"], nodes, connections))

    # 65 - Content Version Tracking
    nodes = [
        webhook_node("n1", "Document Update Webhook", "kb-doc-update", 0, 300),
        postgres_node("n2", "Save New Version", "executeQuery",
                      "INSERT INTO kb_document_versions (document_id, version_number, content, changed_by, changed_at, change_summary) SELECT id, COALESCE((SELECT MAX(version_number) FROM kb_document_versions WHERE document_id = {{ $json.document_id }}), 0) + 1, '{{ $json.new_content }}', {{ $json.user_id }}, NOW(), '{{ $json.change_summary }}' FROM kb_documents WHERE id = {{ $json.document_id }} RETURNING version_number",
                      250, 300),
        postgres_node("n3", "Update Main Document", "executeQuery",
                      "UPDATE kb_documents SET content = '{{ $json.new_content }}', updated_at = NOW(), updated_by = {{ $json.user_id }} WHERE id = {{ $json.document_id }}",
                      500, 300),
        slack_node("n4", "Notify Subscribers", "#knowledge-base-updates",
                   ":page_facing_up: Document Updated!\n*{{ $json.document_title }}* has been updated (v{{ $json.version_number }})\nBy: {{ $json.editor_name }}\nChanges: {{ $json.change_summary }}\nView: https://kb.company.com/docs/{{ $json.document_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Document Update Webhook", "Save New Version"),
        conn("Save New Version", "Update Main Document"),
        conn("Update Main Document", "Notify Subscribers"),
    ])
    save(folder, "65-content-version-tracking.json",
         workflow("wf-kb-65", "Content Version Tracking", ["knowledge_base", "documents"], nodes, connections))

    # 66 - Auto Tagging
    nodes = [
        webhook_node("n1", "New Document Webhook", "kb-auto-tag", 0, 300),
        http_node("n2", "AI Classify & Tag Document", "http://ai-backend:8000/documents/classify", "POST", 250, 300,
                  [{"name": "content", "value": "={{ $json.content }}"}, {"name": "title", "value": "={{ $json.title }}"}, {"name": "max_tags", "value": "10"}]),
        postgres_node("n3", "Save Tags to DB", "executeQuery",
                      "UPDATE kb_documents SET tags = '{{ $json.tags }}'::jsonb, category = '{{ $json.primary_category }}', auto_tagged_at = NOW() WHERE id = {{ $json.document_id }}",
                      500, 300),
        http_node("n4", "Update Qdrant Payload", "http://qdrant:6333/collections/knowledge_base/points/payload", "POST", 750, 300,
                  [{"name": "points", "value": "[\"{{ $json.qdrant_id }}\"]"}, {"name": "payload", "value": "{\"tags\": {{ $json.tags }}, \"category\": \"{{ $json.primary_category }}\"}"}]),
    ]
    connections = build_connections([
        conn("New Document Webhook", "AI Classify & Tag Document"),
        conn("AI Classify & Tag Document", "Save Tags to DB"),
        conn("Save Tags to DB", "Update Qdrant Payload"),
    ])
    save(folder, "66-auto-tagging.json",
         workflow("wf-kb-66", "Auto Tagging", ["knowledge_base", "ai"], nodes, connections))

    # 67 - Knowledge Gap Detection
    nodes = [
        schedule_node("n1", "Weekly Gap Analysis", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch Unanswered Queries", "executeQuery",
                      "SELECT query, COUNT(*) as frequency FROM kb_search_log WHERE results_count = 0 AND searched_at >= NOW() - INTERVAL '7 days' GROUP BY query ORDER BY frequency DESC LIMIT 50",
                      250, 300),
        http_node("n3", "Identify Knowledge Gaps", "http://ai-backend:8000/kb/detect-gaps", "POST", 500, 300,
                  [{"name": "unanswered_queries", "value": "={{ $json }}"}, {"name": "existing_categories", "value": "={{ $json.categories }}"}]),
        slack_node("n4", "Report Gaps to KB Team", "#knowledge-base-team",
                   ":mag: Weekly Knowledge Gap Report\n{{ $json.gap_count }} gaps identified this week.\n\nTop missing topics:\n{{ $json.top_gaps.map((g, i) => `${i+1}. ${g.topic} (${g.frequency} searches)`).join('\\n') }}\n\nFull report: https://kb.company.com/gaps",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly Gap Analysis", "Fetch Unanswered Queries"),
        conn("Fetch Unanswered Queries", "Identify Knowledge Gaps"),
        conn("Identify Knowledge Gaps", "Report Gaps to KB Team"),
    ])
    save(folder, "67-knowledge-gap-detection.json",
         workflow("wf-kb-67", "Knowledge Gap Detection", ["knowledge_base", "ai", "analytics"], nodes, connections))

    # 68 - Internal Wiki Sync
    nodes = [
        schedule_node("n1", "Daily Wiki Sync", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        http_node("n2", "Fetch Updated Wiki Pages", "http://confluence-api:8080/rest/api/content?expand=body.storage,version&limit=50&start=0", "GET", 250, 300,
                  [{"name": "updatedDate", "value": ">={{ $now.minus(1, 'day').toISO() }}"}]),
        code_node("n3", "Filter & Transform Pages",
                  "const pages = $input.first().json.results || [];\nreturn pages.map(p => ({\n  json: {\n    wiki_id: p.id,\n    title: p.title,\n    content: p.body?.storage?.value || '',\n    last_modified: p.version?.when,\n    author: p.version?.by?.displayName\n  }\n}));",
                  500, 300),
        http_node("n4", "Ingest into KB", "http://ai-backend:8000/documents/parse", "POST", 750, 300,
                  [{"name": "content", "value": "={{ $json.content }}"}, {"name": "title", "value": "={{ $json.title }}"}, {"name": "source", "value": "confluence"}, {"name": "source_id", "value": "={{ $json.wiki_id }}"}]),
    ]
    connections = build_connections([
        conn("Daily Wiki Sync", "Fetch Updated Wiki Pages"),
        conn("Fetch Updated Wiki Pages", "Filter & Transform Pages"),
        conn("Filter & Transform Pages", "Ingest into KB"),
    ])
    save(folder, "68-internal-wiki-sync.json",
         workflow("wf-kb-68", "Internal Wiki Sync", ["knowledge_base", "integration"], nodes, connections))

    # 69 - Policy Update Notification
    nodes = [
        webhook_node("n1", "Policy Update Webhook", "kb-policy-update", 0, 300),
        postgres_node("n2", "Get Affected Employees", "executeQuery",
                      "SELECT e.email, e.name FROM employees e JOIN policy_applicability pa ON pa.department_id = e.department_id OR pa.role_id = e.role_id WHERE pa.policy_id = {{ $json.policy_id }} AND e.status = 'active'",
                      250, 300),
        set_node("n3", "Prepare Policy Notification", {
            "subject": "=Policy Update: {{ $json.policy_name }}",
            "body": "=Hi {{ $json.name }},\n\nAn important policy has been updated that affects your role:\n\nPolicy: {{ $json.policy_name }}\nEffective Date: {{ $json.effective_date }}\nKey Changes: {{ $json.summary }}\n\nPlease review the full policy: https://kb.company.com/policies/{{ $json.policy_id }}\n\nAcknowledge receipt: https://kb.company.com/policies/{{ $json.policy_id }}/acknowledge\n\nHR & Compliance Team",
        }, 500, 300),
        email_node("n4", "Send Policy Update Email",
                   "={{ $json.email }}",
                   "={{ $json.subject }}",
                   "={{ $json.body }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Policy Update Webhook", "Get Affected Employees"),
        conn("Get Affected Employees", "Prepare Policy Notification"),
        conn("Prepare Policy Notification", "Send Policy Update Email"),
    ])
    save(folder, "69-policy-update-notification.json",
         workflow("wf-kb-69", "Policy Update Notification", ["knowledge_base", "hr", "compliance"], nodes, connections))

    # 70 - KB Analytics
    nodes = [
        schedule_node("n1", "Weekly KB Analytics", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate KB Usage", "executeQuery",
                      "SELECT COUNT(*) as total_searches, COUNT(CASE WHEN results_count = 0 THEN 1 END) as zero_results, AVG(results_count) as avg_results, COUNT(DISTINCT user_id) as unique_users, (SELECT title FROM kb_documents d JOIN kb_search_log sl ON sl.results_count > 0 GROUP BY d.id, d.title ORDER BY COUNT(*) DESC LIMIT 1) as top_article FROM kb_search_log WHERE searched_at >= NOW() - INTERVAL '7 days'",
                      250, 300),
        code_node("n3", "Format Analytics Report",
                  "const d = $input.first().json;\nconst hitRate = ((d.total_searches - d.zero_results) / d.total_searches * 100).toFixed(1);\nconst report = `KB Weekly Analytics\\n${'='.repeat(40)}\\n` +\n  `Total Searches: ${d.total_searches}\\n` +\n  `Hit Rate: ${hitRate}%\\n` +\n  `Zero-Result Searches: ${d.zero_results}\\n` +\n  `Unique Users: ${d.unique_users}\\n` +\n  `Avg Results per Search: ${parseFloat(d.avg_results).toFixed(1)}\\n` +\n  `Top Article: ${d.top_article}`;\nreturn [{json:{report, hit_rate: hitRate}}];",
                  500, 300),
        email_node("n4", "Send Analytics to KB Manager",
                   "kb-manager@company.com",
                   "KB Weekly Analytics — {{ $now.format('MMM DD, YYYY') }}",
                   "={{ $json.report }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly KB Analytics", "Aggregate KB Usage"),
        conn("Aggregate KB Usage", "Format Analytics Report"),
        conn("Format Analytics Report", "Send Analytics to KB Manager"),
    ])
    save(folder, "70-kb-analytics.json",
         workflow("wf-kb-70", "KB Analytics Report", ["knowledge_base", "analytics"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT PARSING WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_doc_workflows():
    folder = "document_parsing"

    # 71 - PDF Invoice Extraction
    nodes = [
        webhook_node("n1", "PDF Invoice Webhook", "doc-pdf-invoice", 0, 300),
        http_node("n2", "Download PDF", "={{ $json.pdf_url }}", "GET", 250, 300),
        http_node("n3", "Upload & Extract Invoice Data", "http://ai-backend:8000/documents/upload", "POST", 500, 300,
                  [{"name": "file", "value": "={{ $json.binary_data }}"}, {"name": "document_type", "value": "invoice"}, {"name": "extract_fields", "value": "invoice_number,vendor,amount,due_date,line_items,tax"}]),
        postgres_node("n4", "Save Extracted Invoice", "executeQuery",
                      "INSERT INTO extracted_invoices (source_url, vendor, invoice_number, amount, tax, due_date, line_items, confidence, extracted_at) VALUES ('{{ $json.pdf_url }}', '{{ $json.extracted.vendor }}', '{{ $json.extracted.invoice_number }}', {{ $json.extracted.amount }}, {{ $json.extracted.tax }}, '{{ $json.extracted.due_date }}', '{{ $json.extracted.line_items }}'::jsonb, {{ $json.confidence }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("PDF Invoice Webhook", "Download PDF"),
        conn("Download PDF", "Upload & Extract Invoice Data"),
        conn("Upload & Extract Invoice Data", "Save Extracted Invoice"),
    ])
    save(folder, "71-pdf-invoice-extraction.json",
         workflow("wf-doc-71", "PDF Invoice Extraction", ["document_parsing", "invoice"], nodes, connections))

    # 72 - Contract Key Terms
    nodes = [
        webhook_node("n1", "Contract Text Webhook", "doc-contract-terms", 0, 300),
        http_node("n2", "AI Summarize Contract", "http://ai-backend:8000/documents/summarize", "POST", 250, 300,
                  [{"name": "content", "value": "={{ $json.contract_text }}"}, {"name": "context", "value": "legal_contract"}, {"name": "extract", "value": "parties,dates,obligations,penalties,termination,payment_terms"}]),
        set_node("n3", "Structure Key Terms", {
            "parties": "={{ $json.extracted.parties }}",
            "start_date": "={{ $json.extracted.start_date }}",
            "end_date": "={{ $json.extracted.end_date }}",
            "payment_terms": "={{ $json.extracted.payment_terms }}",
            "penalties": "={{ $json.extracted.penalties }}",
            "termination_clause": "={{ $json.extracted.termination }}",
        }, 500, 300),
        postgres_node("n4", "Save Contract Analysis", "executeQuery",
                      "INSERT INTO contract_analyses (contract_id, parties, start_date, end_date, payment_terms, penalties, termination_clause, summary, analyzed_at) VALUES ({{ $json.contract_id }}, '{{ $json.parties }}', '{{ $json.start_date }}', '{{ $json.end_date }}', '{{ $json.payment_terms }}', '{{ $json.penalties }}', '{{ $json.termination_clause }}', '{{ $json.summary }}', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Contract Text Webhook", "AI Summarize Contract"),
        conn("AI Summarize Contract", "Structure Key Terms"),
        conn("Structure Key Terms", "Save Contract Analysis"),
    ])
    save(folder, "72-contract-key-terms.json",
         workflow("wf-doc-72", "Contract Key Terms Extraction", ["document_parsing", "legal"], nodes, connections))

    # 73 - Resume Parser
    nodes = [
        webhook_node("n1", "Resume File Webhook", "doc-resume-parse", 0, 300),
        http_node("n2", "Upload Resume", "http://ai-backend:8000/documents/upload", "POST", 250, 300,
                  [{"name": "file_url", "value": "={{ $json.resume_url }}"}, {"name": "document_type", "value": "resume"}]),
        http_node("n3", "AI Screen Resume", "http://ai-backend:8000/hr/screen-resume", "POST", 500, 300,
                  [{"name": "parsed_resume", "value": "={{ $json.parsed_content }}"}, {"name": "job_id", "value": "={{ $json.job_id }}"}]),
        postgres_node("n4", "Save Structured Resume", "executeQuery",
                      "INSERT INTO parsed_resumes (candidate_id, job_id, full_name, email, phone, years_experience, skills, education, work_history, ai_score, parsed_at) VALUES ({{ $json.candidate_id }}, {{ $json.job_id }}, '{{ $json.full_name }}', '{{ $json.email }}', '{{ $json.phone }}', {{ $json.years_experience }}, '{{ $json.skills }}'::jsonb, '{{ $json.education }}'::jsonb, '{{ $json.work_history }}'::jsonb, {{ $json.ai_score }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Resume File Webhook", "Upload Resume"),
        conn("Upload Resume", "AI Screen Resume"),
        conn("AI Screen Resume", "Save Structured Resume"),
    ])
    save(folder, "73-resume-parser.json",
         workflow("wf-doc-73", "Resume Parser", ["document_parsing", "hr", "ai"], nodes, connections))

    # 74 - Form Field Extraction
    nodes = [
        webhook_node("n1", "Form Document Webhook", "doc-form-extract", 0, 300),
        http_node("n2", "Parse Form Fields", "http://ai-backend:8000/documents/parse", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "document_type", "value": "form"}, {"name": "type", "value": "form"}]),
        set_node("n3", "Map Form Fields", {
            "extracted_fields": "={{ $json.fields }}",
            "field_count": "={{ Object.keys($json.fields).length }}",
            "confidence": "={{ $json.confidence }}",
            "form_type": "={{ $json.detected_form_type }}",
        }, 500, 300),
        postgres_node("n4", "Save Form Extraction", "executeQuery",
                      "INSERT INTO form_extractions (document_url, form_type, fields, field_count, confidence, extracted_at) VALUES ('{{ $json.document_url }}', '{{ $json.form_type }}', '{{ $json.extracted_fields }}'::jsonb, {{ $json.field_count }}, {{ $json.confidence }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Form Document Webhook", "Parse Form Fields"),
        conn("Parse Form Fields", "Map Form Fields"),
        conn("Map Form Fields", "Save Form Extraction"),
    ])
    save(folder, "74-form-field-extraction.json",
         workflow("wf-doc-74", "Form Field Extraction", ["document_parsing"], nodes, connections))

    # 75 - Table Extraction
    nodes = [
        webhook_node("n1", "Table Document Webhook", "doc-table-extract", 0, 300),
        http_node("n2", "Extract Tables from Document", "http://ai-backend:8000/documents/extract-tables", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "format", "value": "json"}, {"name": "include_headers", "value": "true"}]),
        code_node("n3", "Process Extracted Tables",
                  "const tables = $input.first().json.tables || [];\nreturn tables.map((table, i) => ({\n  json: {\n    table_index: i,\n    headers: table.headers,\n    row_count: table.rows.length,\n    data: table.rows,\n    document_url: $input.first().json.document_url\n  }\n}));",
                  500, 300),
        postgres_node("n4", "Save Structured Table Data", "executeQuery",
                      "INSERT INTO extracted_tables (document_url, table_index, headers, row_count, data, extracted_at) VALUES ('{{ $json.document_url }}', {{ $json.table_index }}, '{{ $json.headers }}'::jsonb, {{ $json.row_count }}, '{{ $json.data }}'::jsonb, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Table Document Webhook", "Extract Tables from Document"),
        conn("Extract Tables from Document", "Process Extracted Tables"),
        conn("Process Extracted Tables", "Save Structured Table Data"),
    ])
    save(folder, "75-table-extraction.json",
         workflow("wf-doc-75", "Table Extraction", ["document_parsing", "data"], nodes, connections))

    # 76 - Document Classification
    nodes = [
        webhook_node("n1", "Document Classification Webhook", "doc-classify", 0, 300),
        http_node("n2", "Classify Document", "http://ai-backend:8000/documents/classify", "POST", 250, 300,
                  [{"name": "content", "value": "={{ $json.document_text }}"}, {"name": "possible_types", "value": "invoice,contract,resume,report,email,form,policy,receipt"}]),
        if_node("n3", "Route by Document Type", "={{ $json.document_type }}", "equals", "invoice", 500, 300),
        http_node("n4", "Trigger Invoice Workflow", "http://n8n:5678/webhook/doc-pdf-invoice", "POST", 750, 200,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "document_type", "value": "invoice"}]),
        http_node("n5", "Trigger Generic Parser", "http://n8n:5678/webhook/doc-form-extract", "POST", 750, 400,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "document_type", "value": "={{ $json.document_type }}"}]),
    ]
    connections = build_connections([
        conn("Document Classification Webhook", "Classify Document"),
        conn("Classify Document", "Route by Document Type"),
        conn("Route by Document Type", "Trigger Invoice Workflow", 0, 0),
        conn("Route by Document Type", "Trigger Generic Parser", 1, 0),
    ])
    save(folder, "76-document-classification.json",
         workflow("wf-doc-76", "Document Classification", ["document_parsing", "ai"], nodes, connections))

    # 77 - Legal Doc Summary
    nodes = [
        webhook_node("n1", "Legal Document Webhook", "doc-legal-summary", 0, 300),
        http_node("n2", "AI Legal Summary", "http://ai-backend:8000/documents/summarize", "POST", 250, 300,
                  [{"name": "content", "value": "={{ $json.document_text }}"}, {"name": "context", "value": "legal"}, {"name": "extract", "value": "key_clauses,risks,obligations,dates,parties,jurisdiction"}]),
        set_node("n3", "Structure Legal Analysis", {
            "summary": "={{ $json.summary }}",
            "key_clauses": "={{ $json.extracted.key_clauses }}",
            "risks": "={{ $json.extracted.risks }}",
            "obligations": "={{ $json.extracted.obligations }}",
            "jurisdiction": "={{ $json.extracted.jurisdiction }}",
        }, 500, 300),
        postgres_node("n4", "Save Legal Analysis", "executeQuery",
                      "INSERT INTO legal_doc_analyses (document_id, summary, key_clauses, risks, obligations, jurisdiction, analyzed_by, analyzed_at) VALUES ({{ $json.document_id }}, '{{ $json.summary }}', '{{ $json.key_clauses }}'::jsonb, '{{ $json.risks }}'::jsonb, '{{ $json.obligations }}'::jsonb, '{{ $json.jurisdiction }}', {{ $json.user_id }}, NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Legal Document Webhook", "AI Legal Summary"),
        conn("AI Legal Summary", "Structure Legal Analysis"),
        conn("Structure Legal Analysis", "Save Legal Analysis"),
    ])
    save(folder, "77-legal-doc-summary.json",
         workflow("wf-doc-77", "Legal Document Summary", ["document_parsing", "legal", "ai"], nodes, connections))

    # 78 - Medical Record Processing
    nodes = [
        webhook_node("n1", "Medical Record Webhook", "doc-medical-record", 0, 300),
        http_node("n2", "Extract Medical Data", "http://ai-backend:8000/documents/parse", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.record_url }}"}, {"name": "document_type", "value": "medical_record"}, {"name": "extract_fields", "value": "patient_name,dob,diagnoses,medications,allergies,procedures,provider"}]),
        set_node("n3", "Map Medical Fields", {
            "patient_name": "={{ $json.extracted.patient_name }}",
            "date_of_birth": "={{ $json.extracted.dob }}",
            "diagnoses": "={{ $json.extracted.diagnoses }}",
            "medications": "={{ $json.extracted.medications }}",
            "allergies": "={{ $json.extracted.allergies }}",
            "provider": "={{ $json.extracted.provider }}",
        }, 500, 300),
        postgres_node("n4", "Save to Secure Medical Table", "executeQuery",
                      "INSERT INTO medical_records_structured (patient_id, patient_name, date_of_birth, diagnoses, medications, allergies, provider, source_url, processed_at) VALUES ({{ $json.patient_id }}, '{{ $json.patient_name }}', '{{ $json.date_of_birth }}', '{{ $json.diagnoses }}'::jsonb, '{{ $json.medications }}'::jsonb, '{{ $json.allergies }}'::jsonb, '{{ $json.provider }}', '{{ $json.record_url }}', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Medical Record Webhook", "Extract Medical Data"),
        conn("Extract Medical Data", "Map Medical Fields"),
        conn("Map Medical Fields", "Save to Secure Medical Table"),
    ])
    save(folder, "78-medical-record-processing.json",
         workflow("wf-doc-78", "Medical Record Processing", ["document_parsing", "healthcare"], nodes, connections))

    # 79 - Compliance Checking
    nodes = [
        webhook_node("n1", "Compliance Check Webhook", "doc-compliance-check", 0, 300),
        postgres_node("n2", "Fetch Compliance Rules", "executeQuery",
                      "SELECT rule_id, rule_name, pattern, severity, category FROM compliance_rules WHERE active = true AND (document_type = '{{ $json.document_type }}' OR document_type = 'all')",
                      250, 300),
        code_node("n3", "Run Compliance Check",
                  "const rules = $input.all().map(i => i.json);\nconst content = $input.first().json.document_text;\nconst violations = [];\nfor (const rule of rules) {\n  const regex = new RegExp(rule.pattern, 'gi');\n  if (!regex.test(content)) {\n    violations.push({\n      rule_id: rule.rule_id,\n      rule_name: rule.rule_name,\n      severity: rule.severity,\n      category: rule.category\n    });\n  }\n}\nconst is_compliant = violations.filter(v => v.severity === 'critical').length === 0;\nreturn [{json: { violations, is_compliant, violation_count: violations.length }}];",
                  500, 300),
        if_node("n4", "Has Violations?", "={{ $json.is_compliant }}", "equals", "false", 750, 300),
        slack_node("n5", "Alert Compliance Team", "#compliance-alerts",
                   ":warning: *Compliance Issue Detected!*\nDocument: {{ $json.document_id }}\nViolations: {{ $json.violation_count }}\nCritical Issues: {{ $json.violations.filter(v => v.severity === 'critical').length }}\n\nImmediate review required.",
                   1000, 200),
        noop_node("n6", "Document Compliant", 1000, 400),
    ]
    connections = build_connections([
        conn("Compliance Check Webhook", "Fetch Compliance Rules"),
        conn("Fetch Compliance Rules", "Run Compliance Check"),
        conn("Run Compliance Check", "Has Violations?"),
        conn("Has Violations?", "Alert Compliance Team", 0, 0),
        conn("Has Violations?", "Document Compliant", 1, 0),
    ])
    save(folder, "79-compliance-checking.json",
         workflow("wf-doc-79", "Compliance Checking", ["document_parsing", "compliance", "ai"], nodes, connections))

    # 80 - Bulk Document Processor
    nodes = [
        schedule_node("n1", "Hourly Batch Schedule", {"interval": [{"field": "hours", "hoursInterval": 1}]}, 0, 300),
        http_node("n2", "List Pending Documents from MinIO", "http://minio:9000/documents/pending?limit=20", "GET", 250, 300),
        code_node("n3", "Prepare Document Batch",
                  "const docs = $input.first().json.documents || [];\nreturn docs.map(doc => ({\n  json: {\n    document_url: `http://minio:9000/documents/${doc.name}`,\n    document_name: doc.name,\n    document_type: doc.metadata?.type || 'unknown',\n    size: doc.size\n  }\n}));",
                  500, 300),
        http_node("n4", "Run Through Parse Pipeline", "http://ai-backend:8000/documents/parse", "POST", 750, 300,
                  [{"name": "document_url", "value": "={{ $json.document_url }}"}, {"name": "document_type", "value": "={{ $json.document_type }}"}, {"name": "batch_mode", "value": "true"}]),
    ]
    connections = build_connections([
        conn("Hourly Batch Schedule", "List Pending Documents from MinIO"),
        conn("List Pending Documents from MinIO", "Prepare Document Batch"),
        conn("Prepare Document Batch", "Run Through Parse Pipeline"),
    ])
    save(folder, "80-bulk-document-processor.json",
         workflow("wf-doc-80", "Bulk Document Processor", ["document_parsing", "automation"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# MEETING SUMMARY WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_meeting_workflows():
    folder = "meetings"

    # 81 - Transcript Ingestion
    nodes = [
        webhook_node("n1", "Transcript Webhook", "meeting-transcript", 0, 300),
        http_node("n2", "Summarize Transcript", "http://ai-backend:8000/meetings/summarize", "POST", 250, 300,
                  [{"name": "transcript", "value": "={{ $json.transcript_text }}"}, {"name": "meeting_id", "value": "={{ $json.meeting_id }}"}, {"name": "participants", "value": "={{ $json.participants }}"}]),
        postgres_node("n3", "Save Meeting Summary", "executeQuery",
                      "INSERT INTO meeting_summaries (meeting_id, title, transcript, summary, key_points, participants, duration_minutes, summarized_at) VALUES ('{{ $json.meeting_id }}', '{{ $json.meeting_title }}', '{{ $json.transcript_text }}', '{{ $json.summary }}', '{{ $json.key_points }}'::jsonb, '{{ $json.participants }}'::jsonb, {{ $json.duration_minutes }}, NOW())",
                      500, 300),
        slack_node("n4", "Post Summary to Team", "={{ $json.team_channel }}",
                   ":notepad_spiral: *Meeting Summary: {{ $json.meeting_title }}*\n{{ $json.summary }}\n\nKey Points:\n{{ $json.key_points.map(p => `• ${p}`).join('\\n') }}\n\nFull notes: https://meetings.company.com/{{ $json.meeting_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Transcript Webhook", "Summarize Transcript"),
        conn("Summarize Transcript", "Save Meeting Summary"),
        conn("Save Meeting Summary", "Post Summary to Team"),
    ])
    save(folder, "81-transcript-ingestion.json",
         workflow("wf-meet-81", "Meeting Transcript Ingestion", ["meetings", "ai"], nodes, connections))

    # 82 - Action Item Extraction
    nodes = [
        webhook_node("n1", "Meeting Transcript Webhook", "meeting-action-items", 0, 300),
        http_node("n2", "Extract Action Items", "http://ai-backend:8000/meetings/extract-actions", "POST", 250, 300,
                  [{"name": "transcript", "value": "={{ $json.transcript_text }}"}, {"name": "participants", "value": "={{ $json.participants }}"}]),
        postgres_node("n3", "Create Action Item Tasks", "executeQuery",
                      "INSERT INTO action_items (meeting_id, task_description, assignee, due_date, priority, status, created_at) SELECT '{{ $json.meeting_id }}', item->>'task', item->>'assignee', (item->>'due_date')::date, item->>'priority', 'open', NOW() FROM json_array_elements('{{ $json.action_items }}'::json) AS item",
                      500, 300),
        slack_node("n4", "Send Action Items to Slack", "={{ $json.team_channel }}",
                   ":white_check_mark: *Action Items from {{ $json.meeting_title }}*\n{{ $json.action_items.map(a => `• [{{ a.assignee }}] {{ a.task }} — Due: {{ a.due_date }}`).join('\\n') }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Meeting Transcript Webhook", "Extract Action Items"),
        conn("Extract Action Items", "Create Action Item Tasks"),
        conn("Create Action Item Tasks", "Send Action Items to Slack"),
    ])
    save(folder, "82-action-item-extraction.json",
         workflow("wf-meet-82", "Action Item Extraction", ["meetings", "ai", "tasks"], nodes, connections))

    # 83 - Meeting Summary Email
    nodes = [
        webhook_node("n1", "Meeting End Webhook", "meeting-summary-email", 0, 300),
        http_node("n2", "Generate Summary", "http://ai-backend:8000/meetings/summarize", "POST", 250, 300,
                  [{"name": "transcript", "value": "={{ $json.transcript_text }}"}, {"name": "meeting_id", "value": "={{ $json.meeting_id }}"}]),
        code_node("n3", "Prepare Email for Each Participant",
                  "const participants = $input.first().json.participants || [];\nconst summary = $input.first().json;\nreturn participants.map(p => ({\n  json: {\n    ...summary,\n    participant_email: p.email,\n    participant_name: p.name\n  }\n}));",
                  500, 300),
        email_node("n4", "Send Summary to All Participants",
                   "={{ $json.participant_email }}",
                   "Meeting Summary: {{ $json.meeting_title }} — {{ $now.format('MMM DD, YYYY') }}",
                   "Hi {{ $json.participant_name }},\n\nHere is the summary for today's meeting:\n\n{{ $json.summary }}\n\nKey Points:\n{{ $json.key_points.map(p => `• ${p}`).join('\\n') }}\n\nAction Items:\n{{ $json.action_items.map(a => `• [${a.assignee}] ${a.task} — Due: ${a.due_date}`).join('\\n') }}\n\nFull notes: https://meetings.company.com/{{ $json.meeting_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Meeting End Webhook", "Generate Summary"),
        conn("Generate Summary", "Prepare Email for Each Participant"),
        conn("Prepare Email for Each Participant", "Send Summary to All Participants"),
    ])
    save(folder, "83-meeting-summary-email.json",
         workflow("wf-meet-83", "Meeting Summary Email", ["meetings", "email", "ai"], nodes, connections))

    # 84 - Follow-up Task Creation
    nodes = [
        webhook_node("n1", "Meeting Summary Webhook", "meeting-tasks", 0, 300),
        http_node("n2", "Create Tasks in Project Tool", "http://jira-api:8080/rest/api/2/issue", "POST", 250, 300,
                  [{"name": "summary", "value": "={{ $json.task_description }}"}, {"name": "assignee", "value": "={{ $json.assignee_jira_id }}"}, {"name": "duedate", "value": "={{ $json.due_date }}"}, {"name": "priority", "value": "={{ $json.priority }}"}, {"name": "labels", "value": "[\"meeting-action\", \"{{ $json.meeting_id }}\"]"}]),
        postgres_node("n3", "Update Action Item with Task ID", "executeQuery",
                      "UPDATE action_items SET jira_ticket_id = '{{ $json.key }}', status = 'in_progress' WHERE meeting_id = '{{ $json.meeting_id }}' AND task_description = '{{ $json.task_description }}'",
                      500, 300),
        slack_node("n4", "Notify Assignee", "={{ $json.assignee_slack_id }}",
                   ":clipboard: You have a new action item from *{{ $json.meeting_title }}*\n*Task:* {{ $json.task_description }}\n*Due:* {{ $json.due_date }}\n*Priority:* {{ $json.priority }}\n*Jira:* {{ $json.key }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Meeting Summary Webhook", "Create Tasks in Project Tool"),
        conn("Create Tasks in Project Tool", "Update Action Item with Task ID"),
        conn("Update Action Item with Task ID", "Notify Assignee"),
    ])
    save(folder, "84-followup-task-creation.json",
         workflow("wf-meet-84", "Follow-up Task Creation", ["meetings", "tasks", "integration"], nodes, connections))

    # 85 - Meeting Analytics Report
    nodes = [
        schedule_node("n1", "Weekly Meeting Analytics", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate Meeting Data", "executeQuery",
                      "SELECT COUNT(*) as total_meetings, AVG(duration_minutes) as avg_duration, SUM(duration_minutes) as total_meeting_hours, COUNT(DISTINCT meeting_id) as unique_meetings, (SELECT COUNT(*) FROM action_items WHERE created_at >= NOW() - INTERVAL '7 days') as action_items_created, (SELECT COUNT(*) FROM action_items WHERE status = 'completed' AND updated_at >= NOW() - INTERVAL '7 days') as action_items_completed FROM meeting_summaries WHERE summarized_at >= NOW() - INTERVAL '7 days'",
                      250, 300),
        code_node("n3", "Format Meeting Report",
                  "const d = $input.first().json;\nconst completionRate = d.action_items_created > 0 ? (d.action_items_completed / d.action_items_created * 100).toFixed(1) : 0;\nconst report = `Meeting Analytics Report\\n${'='.repeat(40)}\\n` +\n  `Total Meetings: ${d.total_meetings}\\n` +\n  `Avg Duration: ${parseFloat(d.avg_duration).toFixed(0)} min\\n` +\n  `Total Meeting Time: ${(d.total_meeting_hours / 60).toFixed(1)} hours\\n` +\n  `Action Items Created: ${d.action_items_created}\\n` +\n  `Action Items Completed: ${d.action_items_completed} (${completionRate}%)`;\nreturn [{json:{report, completion_rate: completionRate}}];",
                  500, 300),
        email_node("n4", "Send Analytics Report",
                   "management@company.com",
                   "Weekly Meeting Analytics — {{ $now.format('MMM DD, YYYY') }}",
                   "={{ $json.report }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly Meeting Analytics", "Aggregate Meeting Data"),
        conn("Aggregate Meeting Data", "Format Meeting Report"),
        conn("Format Meeting Report", "Send Analytics Report"),
    ])
    save(folder, "85-meeting-analytics-report.json",
         workflow("wf-meet-85", "Meeting Analytics Report", ["meetings", "analytics", "reporting"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER SUPPORT WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_support_workflows():
    folder = "support"

    # 86 - Ticket from Email
    nodes = [
        webhook_node("n1", "Email Support Webhook", "support-ticket-email", 0, 300),
        postgres_node("n2", "Create Support Ticket", "executeQuery",
                      "INSERT INTO support_tickets (subject, description, customer_email, customer_name, status, priority, source, created_at) VALUES ('{{ $json.subject }}', '{{ $json.body }}', '{{ $json.from_email }}', '{{ $json.from_name }}', 'open', 'normal', 'email', NOW()) RETURNING id, created_at",
                      250, 300),
        set_node("n3", "Prepare Confirmation Data", {
            "ticket_id": "={{ $json.id }}",
            "customer_email": "={{ $json.from_email }}",
            "ticket_number": "=TKT-{{ $json.id.toString().padStart(6, '0') }}",
        }, 500, 300),
        email_node("n4", "Send Ticket Confirmation",
                   "={{ $json.customer_email }}",
                   "Support Ticket Opened — {{ $json.ticket_number }}",
                   "Hi {{ $json.from_name }},\n\nWe have received your support request and created ticket {{ $json.ticket_number }}.\n\nOur team will respond within 24 hours.\n\nTrack your ticket: https://support.company.com/tickets/{{ $json.ticket_id }}\n\nSupport Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Email Support Webhook", "Create Support Ticket"),
        conn("Create Support Ticket", "Prepare Confirmation Data"),
        conn("Prepare Confirmation Data", "Send Ticket Confirmation"),
    ])
    save(folder, "86-ticket-from-email.json",
         workflow("wf-sup-86", "Ticket from Email", ["support"], nodes, connections))

    # 87 - Ticket Classification
    nodes = [
        webhook_node("n1", "New Ticket Webhook", "support-classify-ticket", 0, 300),
        http_node("n2", "AI Classify Ticket", "http://ai-backend:8000/support/classify", "POST", 250, 300,
                  [{"name": "ticket_id", "value": "={{ $json.ticket_id }}"}, {"name": "subject", "value": "={{ $json.subject }}"}, {"name": "description", "value": "={{ $json.description }}"}]),
        postgres_node("n3", "Update Ticket Classification", "executeQuery",
                      "UPDATE support_tickets SET category = '{{ $json.category }}', subcategory = '{{ $json.subcategory }}', priority = '{{ $json.priority }}', assigned_team = '{{ $json.assigned_team }}', classified_at = NOW() WHERE id = {{ $json.ticket_id }}",
                      500, 300),
        slack_node("n4", "Route to Appropriate Team", "={{ $json.team_slack_channel }}",
                   ":ticket: New {{ $json.priority }} priority ticket assigned to your team!\nTicket: TKT-{{ $json.ticket_id }}\nCategory: {{ $json.category }} / {{ $json.subcategory }}\nSubject: {{ $json.subject }}\nView: https://support.company.com/tickets/{{ $json.ticket_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("New Ticket Webhook", "AI Classify Ticket"),
        conn("AI Classify Ticket", "Update Ticket Classification"),
        conn("Update Ticket Classification", "Route to Appropriate Team"),
    ])
    save(folder, "87-ticket-classification.json",
         workflow("wf-sup-87", "Ticket Classification", ["support", "ai"], nodes, connections))

    # 88 - AI First Response
    nodes = [
        webhook_node("n1", "Classified Ticket Webhook", "support-ai-response", 0, 300),
        http_node("n2", "Generate AI Response", "http://ai-backend:8000/support/generate-response", "POST", 250, 300,
                  [{"name": "ticket_id", "value": "={{ $json.ticket_id }}"}, {"name": "category", "value": "={{ $json.category }}"}, {"name": "description", "value": "={{ $json.description }}"}]),
        email_node("n3", "Send AI First Response",
                   "={{ $json.customer_email }}",
                   "Re: {{ $json.subject }} [TKT-{{ $json.ticket_id }}]",
                   "={{ $json.ai_response }}\n\n---\nTicket #TKT-{{ $json.ticket_id }}\nIf this doesn't resolve your issue, a human agent will follow up.\nView ticket: https://support.company.com/tickets/{{ $json.ticket_id }}",
                   500, 300),
        postgres_node("n4", "Log AI Response", "executeQuery",
                      "INSERT INTO ticket_responses (ticket_id, response_type, response_text, sent_at) VALUES ({{ $json.ticket_id }}, 'ai_first_response', '{{ $json.ai_response }}', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Classified Ticket Webhook", "Generate AI Response"),
        conn("Generate AI Response", "Send AI First Response"),
        conn("Send AI First Response", "Log AI Response"),
    ])
    save(folder, "88-ai-first-response.json",
         workflow("wf-sup-88", "AI First Response", ["support", "ai", "email"], nodes, connections))

    # 89 - Escalation to Human
    nodes = [
        webhook_node("n1", "Escalation Check Webhook", "support-escalation", 0, 300),
        http_node("n2", "Check Escalation Need", "http://ai-backend:8000/support/escalation-check", "POST", 250, 300,
                  [{"name": "ticket_id", "value": "={{ $json.ticket_id }}"}, {"name": "conversation_history", "value": "={{ $json.conversation_history }}"}, {"name": "sentiment", "value": "={{ $json.sentiment }}"}]),
        if_node("n3", "Should Escalate?", "={{ $json.escalate }}", "equals", "true", 500, 300),
        postgres_node("n4", "Update Ticket for Human", "executeQuery",
                      "UPDATE support_tickets SET status = 'escalated', escalated_at = NOW(), escalation_reason = '{{ $json.escalation_reason }}' WHERE id = {{ $json.ticket_id }}",
                      750, 200),
        slack_node("n5", "Alert Human Support Team", "#support-escalations",
                   ":sos: *ESCALATION REQUIRED*\nTicket: TKT-{{ $json.ticket_id }}\nCustomer: {{ $json.customer_name }}\nReason: {{ $json.escalation_reason }}\nSentiment: {{ $json.sentiment }}\nView: https://support.company.com/tickets/{{ $json.ticket_id }}",
                   1000, 200),
        noop_node("n6", "No Escalation Needed", 750, 400),
    ]
    connections = build_connections([
        conn("Escalation Check Webhook", "Check Escalation Need"),
        conn("Check Escalation Need", "Should Escalate?"),
        conn("Should Escalate?", "Update Ticket for Human", 0, 0),
        conn("Should Escalate?", "No Escalation Needed", 1, 0),
        conn("Update Ticket for Human", "Alert Human Support Team"),
    ])
    save(folder, "89-escalation-to-human.json",
         workflow("wf-sup-89", "Escalation to Human", ["support", "ai"], nodes, connections))

    # 90 - SLA Breach Alert
    nodes = [
        schedule_node("n1", "Every 15 Minutes", {"interval": [{"field": "minutes", "minutesInterval": 15}]}, 0, 300),
        postgres_node("n2", "Find SLA Breaching Tickets", "executeQuery",
                      "SELECT t.*, c.name as customer_name, u.slack_id as assignee_slack FROM support_tickets t LEFT JOIN customers c ON t.customer_id = c.id LEFT JOIN users u ON t.assigned_to = u.id WHERE t.status IN ('open', 'in_progress') AND ((t.priority = 'urgent' AND t.created_at < NOW() - INTERVAL '2 hours') OR (t.priority = 'high' AND t.created_at < NOW() - INTERVAL '4 hours') OR (t.priority = 'normal' AND t.created_at < NOW() - INTERVAL '24 hours'))",
                      250, 300),
        set_node("n3", "Calculate Breach Severity", {
            "hours_open": "={{ Math.floor((new Date() - new Date($json.created_at)) / 3600000) }}",
            "sla_status": "=BREACHED",
        }, 500, 300),
        slack_node("n4", "Send Urgent SLA Alert", "#support-sla-alerts",
                   ":fire: *SLA BREACH ALERT*\nTicket: TKT-{{ $json.id }} ({{ $json.priority }} priority)\nCustomer: {{ $json.customer_name }}\nOpen: {{ $json.hours_open }} hours\nAssigned: <@{{ $json.assignee_slack }}>\nImmediate action required!\nhttps://support.company.com/tickets/{{ $json.id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Every 15 Minutes", "Find SLA Breaching Tickets"),
        conn("Find SLA Breaching Tickets", "Calculate Breach Severity"),
        conn("Calculate Breach Severity", "Send Urgent SLA Alert"),
    ])
    save(folder, "90-sla-breach-alert.json",
         workflow("wf-sup-90", "SLA Breach Alert", ["support", "sla"], nodes, connections))

    # 91 - Satisfaction Survey
    nodes = [
        webhook_node("n1", "Ticket Resolved Webhook", "support-csat-survey", 0, 300),
        set_node("n2", "Prepare Survey Data", {
            "survey_token": "={{ $json.ticket_id }}-{{ Date.now() }}",
            "survey_url": "=https://survey.company.com/csat/{{ $json.ticket_id }}",
            "delay_send": "=3600",
        }, 250, 300),
        postgres_node("n3", "Schedule Survey Send", "executeQuery",
                      "INSERT INTO csat_surveys (ticket_id, customer_email, survey_token, scheduled_at, status) VALUES ({{ $json.ticket_id }}, '{{ $json.customer_email }}', '{{ $json.survey_token }}', NOW() + INTERVAL '1 hour', 'scheduled')",
                      500, 300),
        email_node("n4", "Send CSAT Survey Email",
                   "={{ $json.customer_email }}",
                   "How did we do? Rate your support experience",
                   "Hi {{ $json.customer_name }},\n\nYour support ticket TKT-{{ $json.ticket_id }} has been resolved.\n\nHow was your experience? Please take 30 seconds to rate us:\n\n⭐⭐⭐⭐⭐ https://survey.company.com/csat/{{ $json.survey_token }}\n\nYour feedback helps us improve.\n\nSupport Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("Ticket Resolved Webhook", "Prepare Survey Data"),
        conn("Prepare Survey Data", "Schedule Survey Send"),
        conn("Schedule Survey Send", "Send CSAT Survey Email"),
    ])
    save(folder, "91-satisfaction-survey.json",
         workflow("wf-sup-91", "Satisfaction Survey", ["support", "feedback"], nodes, connections))

    # 92 - KB Article Suggestion
    nodes = [
        webhook_node("n1", "New Ticket for KB Webhook", "support-kb-suggest", 0, 300),
        http_node("n2", "Search Knowledge Base", "http://qdrant:6333/collections/knowledge_base/points/search", "POST", 250, 300,
                  [{"name": "vector", "value": "={{ $json.query_embedding }}"}, {"name": "limit", "value": "3"}, {"name": "with_payload", "value": "true"}]),
        set_node("n3", "Format Article Suggestions", {
            "suggestions": "={{ $json.result.map((r, i) => `${i+1}. ${r.payload.title} (relevance: ${(r.score * 100).toFixed(0)}%) - https://kb.company.com/docs/${r.id}`).join('\\n') }}",
            "has_suggestions": "={{ $json.result.length > 0 }}",
        }, 500, 300),
        email_node("n4", "Send KB Suggestions to Customer",
                   "={{ $json.customer_email }}",
                   "Helpful Articles for Your Request [TKT-{{ $json.ticket_id }}]",
                   "Hi {{ $json.customer_name }},\n\nWhile our team reviews your ticket, here are some articles that may help:\n\n{{ $json.suggestions }}\n\nIf none of these resolve your issue, we will follow up shortly.\n\nSupport Team",
                   750, 300),
    ]
    connections = build_connections([
        conn("New Ticket for KB Webhook", "Search Knowledge Base"),
        conn("Search Knowledge Base", "Format Article Suggestions"),
        conn("Format Article Suggestions", "Send KB Suggestions to Customer"),
    ])
    save(folder, "92-kb-article-suggestion.json",
         workflow("wf-sup-92", "KB Article Suggestion", ["support", "knowledge_base"], nodes, connections))

    # 93 - Ticket Resolution Summary
    nodes = [
        webhook_node("n1", "Ticket Close Webhook", "support-resolution-summary", 0, 300),
        http_node("n2", "Generate Resolution Summary", "http://ai-backend:8000/support/generate-response", "POST", 250, 300,
                  [{"name": "ticket_id", "value": "={{ $json.ticket_id }}"}, {"name": "mode", "value": "resolution_summary"}, {"name": "conversation_history", "value": "={{ $json.conversation_history }}"}]),
        postgres_node("n3", "Save Resolution Summary", "executeQuery",
                      "INSERT INTO ticket_resolution_summaries (ticket_id, summary, resolution_type, root_cause, time_to_resolve_hours, created_at) VALUES ({{ $json.ticket_id }}, '{{ $json.summary }}', '{{ $json.resolution_type }}', '{{ $json.root_cause }}', {{ $json.time_to_resolve_hours }}, NOW())",
                      500, 300),
        postgres_node("n4", "Update Ticket Status", "executeQuery",
                      "UPDATE support_tickets SET status = 'closed', closed_at = NOW(), resolution_summary = '{{ $json.summary }}' WHERE id = {{ $json.ticket_id }}",
                      750, 300),
    ]
    connections = build_connections([
        conn("Ticket Close Webhook", "Generate Resolution Summary"),
        conn("Generate Resolution Summary", "Save Resolution Summary"),
        conn("Save Resolution Summary", "Update Ticket Status"),
    ])
    save(folder, "93-ticket-resolution-summary.json",
         workflow("wf-sup-93", "Ticket Resolution Summary", ["support", "ai"], nodes, connections))

    # 94 - Support Metrics Dashboard
    nodes = [
        schedule_node("n1", "Daily Metrics Schedule", {"interval": [{"field": "days", "daysInterval": 1}]}, 0, 300),
        postgres_node("n2", "Aggregate Support Metrics", "executeQuery",
                      "SELECT COUNT(*) as total_tickets, COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets, COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets, AVG(CASE WHEN closed_at IS NOT NULL THEN EXTRACT(EPOCH FROM (closed_at - created_at))/3600 END) as avg_resolution_hours, COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent_tickets, (SELECT AVG(rating) FROM csat_responses WHERE created_at >= CURRENT_DATE) as avg_csat FROM support_tickets WHERE created_at >= CURRENT_DATE",
                      250, 300),
        code_node("n3", "Format Dashboard Data",
                  "const d = $input.first().json;\nconst dashboard = {\n  date: new Date().toISOString().split('T')[0],\n  total_tickets: d.total_tickets,\n  open_tickets: d.open_tickets,\n  closed_tickets: d.closed_tickets,\n  avg_resolution_hours: parseFloat(d.avg_resolution_hours).toFixed(1),\n  urgent_tickets: d.urgent_tickets,\n  avg_csat: parseFloat(d.avg_csat).toFixed(2),\n  first_response_rate: ((d.closed_tickets / d.total_tickets) * 100).toFixed(1)\n};\nreturn [{json: dashboard}];",
                  500, 300),
        http_node("n4", "Update Dashboard Data", "http://dashboard-api:3000/api/metrics/support", "PUT", 750, 300,
                  [{"name": "date", "value": "={{ $json.date }}"}, {"name": "metrics", "value": "={{ $json }}"}]),
    ]
    connections = build_connections([
        conn("Daily Metrics Schedule", "Aggregate Support Metrics"),
        conn("Aggregate Support Metrics", "Format Dashboard Data"),
        conn("Format Dashboard Data", "Update Dashboard Data"),
    ])
    save(folder, "94-support-metrics-dashboard.json",
         workflow("wf-sup-94", "Support Metrics Dashboard", ["support", "analytics", "reporting"], nodes, connections))

    # 95 - Feedback Analysis
    nodes = [
        schedule_node("n1", "Weekly Feedback Analysis", {"interval": [{"field": "weeks", "weeksInterval": 1}]}, 0, 300),
        postgres_node("n2", "Fetch CSAT Responses", "executeQuery",
                      "SELECT cr.*, st.category, st.subject FROM csat_responses cr JOIN support_tickets st ON cr.ticket_id = st.id WHERE cr.created_at >= NOW() - INTERVAL '7 days'",
                      250, 300),
        http_node("n3", "AI Sentiment & Insights", "http://ai-backend:8000/email/sentiment", "POST", 500, 300,
                  [{"name": "responses", "value": "={{ $json }}"}, {"name": "mode", "value": "batch_analysis"}, {"name": "generate_insights", "value": "true"}]),
        email_node("n4", "Send Insights Report",
                   "support-manager@company.com",
                   "Weekly Customer Feedback Insights — {{ $now.format('MMM DD, YYYY') }}",
                   "Weekly Feedback Analysis Report\n\nAverage CSAT: {{ $json.avg_csat }}/5\nTotal Responses: {{ $json.response_count }}\nPositive Rate: {{ $json.positive_rate }}%\n\nKey Themes:\n{{ $json.insights.map(i => `• ${i}`).join('\\n') }}\n\nAreas for Improvement:\n{{ $json.improvement_areas.map(a => `• ${a}`).join('\\n') }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("Weekly Feedback Analysis", "Fetch CSAT Responses"),
        conn("Fetch CSAT Responses", "AI Sentiment & Insights"),
        conn("AI Sentiment & Insights", "Send Insights Report"),
    ])
    save(folder, "95-feedback-analysis.json",
         workflow("wf-sup-95", "Feedback Analysis", ["support", "ai", "analytics"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# PROPOSAL WORKFLOWS
# ─────────────────────────────────────────────────────────────────────────────

def make_proposal_workflows():
    folder = "proposals"

    # 96 - RFP Parsing
    nodes = [
        webhook_node("n1", "RFP Document Webhook", "proposal-rfp-parse", 0, 300),
        http_node("n2", "Parse RFP Document", "http://ai-backend:8000/proposals/parse-rfp", "POST", 250, 300,
                  [{"name": "document_url", "value": "={{ $json.rfp_url }}"}, {"name": "extract", "value": "requirements,budget,timeline,evaluation_criteria,scope,deliverables,submission_deadline"}]),
        postgres_node("n3", "Save RFP Analysis", "executeQuery",
                      "INSERT INTO rfp_analyses (rfp_id, client_name, requirements, budget_range, timeline, evaluation_criteria, scope, deliverables, submission_deadline, complexity_score, analyzed_at) VALUES ('{{ $json.rfp_id }}', '{{ $json.client_name }}', '{{ $json.requirements }}'::jsonb, '{{ $json.budget_range }}', '{{ $json.timeline }}', '{{ $json.evaluation_criteria }}'::jsonb, '{{ $json.scope }}', '{{ $json.deliverables }}'::jsonb, '{{ $json.submission_deadline }}', {{ $json.complexity_score }}, NOW())",
                      500, 300),
        slack_node("n4", "Notify Proposals Team", "#proposals-team",
                   ":page_facing_up: New RFP Parsed!\nClient: *{{ $json.client_name }}*\nBudget: {{ $json.budget_range }}\nDeadline: {{ $json.submission_deadline }}\nComplexity: {{ $json.complexity_score }}/10\n\nView analysis: https://portal.company.com/rfp/{{ $json.rfp_id }}",
                   750, 300),
    ]
    connections = build_connections([
        conn("RFP Document Webhook", "Parse RFP Document"),
        conn("Parse RFP Document", "Save RFP Analysis"),
        conn("Save RFP Analysis", "Notify Proposals Team"),
    ])
    save(folder, "96-rfp-parsing.json",
         workflow("wf-prop-96", "RFP Parsing", ["proposals", "ai", "documents"], nodes, connections))

    # 97 - Proposal Generation
    nodes = [
        webhook_node("n1", "Proposal Request Webhook", "proposal-generate", 0, 300),
        postgres_node("n2", "Fetch RFP Analysis", "executeQuery",
                      "SELECT ra.*, c.name as client_name FROM rfp_analyses ra JOIN clients c ON ra.client_id = c.id WHERE ra.rfp_id = '{{ $json.rfp_id }}'",
                      250, 300),
        http_node("n3", "Generate Full Proposal", "http://ai-backend:8000/proposals/full-proposal", "POST", 500, 300,
                  [{"name": "rfp_data", "value": "={{ $json }}"}, {"name": "company_profile", "value": "{{ $json.company_profile }}"}, {"name": "similar_projects", "value": "={{ $json.similar_projects }}"}, {"name": "format", "value": "pdf"}]),
        http_node("n4", "Save Proposal to MinIO", "http://minio:9000/proposals/{{ $json.proposal_id }}.pdf", "PUT", 750, 300,
                  [{"name": "content", "value": "={{ $json.pdf_base64 }}"}, {"name": "metadata", "value": "{\"rfp_id\": \"{{ $json.rfp_id }}\", \"client\": \"{{ $json.client_name }}\"}"}]),
    ]
    connections = build_connections([
        conn("Proposal Request Webhook", "Fetch RFP Analysis"),
        conn("Fetch RFP Analysis", "Generate Full Proposal"),
        conn("Generate Full Proposal", "Save Proposal to MinIO"),
    ])
    save(folder, "97-proposal-generation.json",
         workflow("wf-prop-97", "Proposal Generation", ["proposals", "ai", "documents"], nodes, connections))

    # 98 - Competitor Analysis
    nodes = [
        webhook_node("n1", "Competitor Analysis Webhook", "proposal-competitor-analysis", 0, 300),
        http_node("n2", "Fetch Competitor Info", "http://web-scraper-api:3000/api/competitor?company={{ $json.competitor_name }}", "GET", 250, 300),
        http_node("n3", "AI Competitive Analysis", "http://ai-backend:8000/proposals/competitor-analysis", "POST", 500, 300,
                  [{"name": "competitor_data", "value": "={{ $json }}"}, {"name": "our_strengths", "value": "={{ $json.our_strengths }}"}, {"name": "rfp_context", "value": "={{ $json.rfp_context }}"}]),
        postgres_node("n4", "Save Competitor Insights", "executeQuery",
                      "INSERT INTO competitor_analyses (rfp_id, competitor_name, strengths, weaknesses, our_advantages, risk_level, analysis, created_at) VALUES ('{{ $json.rfp_id }}', '{{ $json.competitor_name }}', '{{ $json.competitor_strengths }}'::jsonb, '{{ $json.competitor_weaknesses }}'::jsonb, '{{ $json.our_advantages }}'::jsonb, '{{ $json.risk_level }}', '{{ $json.analysis }}', NOW())",
                      750, 300),
    ]
    connections = build_connections([
        conn("Competitor Analysis Webhook", "Fetch Competitor Info"),
        conn("Fetch Competitor Info", "AI Competitive Analysis"),
        conn("AI Competitive Analysis", "Save Competitor Insights"),
    ])
    save(folder, "98-competitor-analysis.json",
         workflow("wf-prop-98", "Competitor Analysis", ["proposals", "ai", "crm"], nodes, connections))

    # 99 - Proposal Approval
    nodes = [
        webhook_node("n1", "Proposal Review Webhook", "proposal-approval", 0, 300),
        postgres_node("n2", "Create Approval Record", "executeQuery",
                      "INSERT INTO proposal_approvals (proposal_id, rfp_id, submitted_by, status, approval_deadline, created_at) VALUES ({{ $json.proposal_id }}, '{{ $json.rfp_id }}', {{ $json.submitted_by }}, 'pending', NOW() + INTERVAL '2 days', NOW()) RETURNING approval_id",
                      250, 300),
        slack_node("n3", "Send Approval Request", "#proposals-review",
                   ":clipboard: *Proposal Review Required!*\nProposal ID: {{ $json.proposal_id }}\nRFP: {{ $json.rfp_title }}\nClient: {{ $json.client_name }}\nValue: ${{ $json.proposal_value }}\nDeadline: {{ $json.submission_deadline }}\n\nView & Approve: https://portal.company.com/proposals/{{ $json.proposal_id }}/review\nApprove: https://portal.company.com/proposals/{{ $json.proposal_id }}/approve\nReject: https://portal.company.com/proposals/{{ $json.proposal_id }}/reject",
                   500, 300),
        postgres_node("n4", "Track Approval Status", "executeQuery",
                      "UPDATE proposal_approvals SET reminder_sent_at = NOW() WHERE approval_id = {{ $json.approval_id }} AND status = 'pending'",
                      750, 300),
    ]
    connections = build_connections([
        conn("Proposal Review Webhook", "Create Approval Record"),
        conn("Create Approval Record", "Send Approval Request"),
        conn("Send Approval Request", "Track Approval Status"),
    ])
    save(folder, "99-proposal-approval.json",
         workflow("wf-prop-99", "Proposal Approval", ["proposals", "workflow"], nodes, connections))

    # 100 - Proposal Delivery
    nodes = [
        webhook_node("n1", "Proposal Approved Webhook", "proposal-delivery", 0, 300),
        postgres_node("n2", "Get Proposal & Client Details", "executeQuery",
                      "SELECT p.*, ra.client_name, ra.submission_deadline, c.email as client_email, c.contact_name FROM proposals p JOIN rfp_analyses ra ON p.rfp_id = ra.rfp_id JOIN clients c ON ra.client_id = c.id WHERE p.id = {{ $json.proposal_id }}",
                      250, 300),
        set_node("n3", "Prepare Delivery Data", {
            "tracking_pixel": "=https://tracking.company.com/pixel/{{ $json.proposal_id }}.png",
            "proposal_url": "=http://minio:9000/proposals/{{ $json.proposal_id }}.pdf",
            "expiry_date": "={{ $json.submission_deadline }}",
        }, 500, 300),
        email_node("n4", "Send Proposal to Client",
                   "={{ $json.client_email }}",
                   "Proposal for {{ $json.rfp_title }} — {{ $json.client_name }}",
                   "Dear {{ $json.contact_name }},\n\nThank you for the opportunity to respond to your RFP for {{ $json.rfp_title }}.\n\nPlease find our proposal attached and accessible at the link below:\n\n📄 Download Proposal: {{ $json.proposal_url }}\n\nProposal valid until: {{ $json.expiry_date }}\n\nWe would love to discuss how we can help {{ $json.client_name }} achieve its goals. Please feel free to reach out with any questions.\n\nBest regards,\nBusiness Development Team\n\n<img src='{{ $json.tracking_pixel }}' width='1' height='1' />",
                   750, 300),
    ]
    connections = build_connections([
        conn("Proposal Approved Webhook", "Get Proposal & Client Details"),
        conn("Get Proposal & Client Details", "Prepare Delivery Data"),
        conn("Prepare Delivery Data", "Send Proposal to Client"),
    ])
    save(folder, "100-proposal-delivery.json",
         workflow("wf-prop-100", "Proposal Delivery", ["proposals", "email", "tracking"], nodes, connections))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Generating 100 n8n workflow JSON files...\n")

    print("📁 HR Workflows (01-20)...")
    make_hr_workflows()

    print("\n📁 CRM Workflows (21-35)...")
    make_crm_workflows()

    print("\n📁 Invoice Workflows (36-50)...")
    make_invoice_workflows()

    print("\n📁 Email Workflows (51-60)...")
    make_email_workflows()

    print("\n📁 Knowledge Base Workflows (61-70)...")
    make_kb_workflows()

    print("\n📁 Document Parsing Workflows (71-80)...")
    make_doc_workflows()

    print("\n📁 Meeting Workflows (81-85)...")
    make_meeting_workflows()

    print("\n📁 Support Workflows (86-95)...")
    make_support_workflows()

    print("\n📁 Proposal Workflows (96-100)...")
    make_proposal_workflows()

    print("\n✅ All 100 workflow files generated successfully!")

    # Count verification
    import glob
    total = len(glob.glob(f"{BASE}/**/*.json", recursive=True))
    print(f"📊 Total files created: {total}")
