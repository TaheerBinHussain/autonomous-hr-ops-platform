import sys
import os
import pytest
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('microservices/document_parser'))

from main import (
    classify_document_authenticity,
    extract_experience_years,
    extract_education_level,
    calculate_enterprise_score
)

def test_document_authenticity_valid_resume():
    valid_text = "Usman Ali\nWork History: Senior DevOps Engineer with 5 years experience in Python, Docker, Kubernetes.\nEducation: Bachelor of Science in Computer Science.\nContact: usman@example.com"
    res = classify_document_authenticity(valid_text)
    assert res["is_genuine_resume"] is True
    assert "Valid Candidate Resume" in res["document_type"]

def test_document_authenticity_study_plan_roadmap():
    study_plan_text = "Weekly Plan for learning DevOps\nWeek 1: Python basics and roadmap\nWeek 2: Docker and Kubernetes course syllabus\nAssignment and homework module 1"
    res = classify_document_authenticity(study_plan_text)
    assert res["is_genuine_resume"] is False
    assert "Invalid Document" in res["document_type"]

def test_extract_experience_years():
    text1 = "Senior Cloud Architect with 5+ years of experience in AWS."
    assert extract_experience_years(text1) == 5

    text2 = "DevOps Engineer from 2018 - 2024"
    assert extract_experience_years(text2) == 6

def test_extract_education_level():
    text_phd = "Doctor of Philosophy in Artificial Intelligence (PhD)"
    assert extract_education_level(text_phd) == "PhD"

    text_masters = "Master of Science (M.S.) in Computer Science"
    assert extract_education_level(text_masters) == "Master's"

    text_bachelors = "Bachelor of Technology (B.Tech) in IT"
    assert extract_education_level(text_bachelors) == "Bachelor's"

def test_calculate_enterprise_score_roadmap_rejection():
    roadmap_text = "Weekly Plan and Roadmap for learning Python, Docker, Kubernetes"
    score_res = calculate_enterprise_score(
        text=roadmap_text,
        required_skills=["python", "docker", "kubernetes"],
        req_exp_years=3,
        req_education="Bachelor's"
    )
    assert score_res["is_genuine_resume"] is False
    assert score_res["final_score"] == 0
    assert score_res["is_shortlisted"] is False
