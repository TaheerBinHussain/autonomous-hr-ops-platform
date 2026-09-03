import os
import json
import glob
import pytest

def test_workflow_json_files_exist():
    workflows = glob.glob("workflows/*.json")
    assert len(workflows) >= 5, f"Found {len(workflows)} workflows, expected 5."
    
    expected_names = [
      "HR Recruitment Candidate Application & Automated Email",
      "Finance AI Invoice Parser & Audit Workflow",
      "Smart Customer Support AI Knowledge Base Workflow",
      "Sales & Proposal Generator Workflow",
      "Meeting Notes & Action Items AI Summarizer Workflow"
    ]
    
    found_names = []
    for wf in workflows:
        with open(wf, "r") as f:
            data = json.load(f)
            found_names.append(data.get("name"))
            
    for name in expected_names:
        assert name in found_names, f"Missing workflow: {name}"

def test_docker_compose_config():
    assert os.path.exists("docker-compose.yml"), "docker-compose.yml missing"
    with open("docker-compose.yml", "r") as f:
        content = f.read()
        assert "n8n" in content
        assert "postgres" in content
        assert "redis" in content
        assert "document_parser" in content
        assert "mailpit" in content
