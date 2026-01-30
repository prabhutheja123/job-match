import re
from pathlib import Path

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text

def extract_skills(text: str, skills: list) -> set:
    found = set()
    for skill in skills:
        if skill in text:
            found.add(skill)
    return found

if __name__ == "__main__":
    jd_text = Path("data/jd/jd.txt").read_text(encoding="utf-8")
    resume_text = Path("data/resume/resume.txt").read_text(encoding="utf-8")

    SKILLS = [
        "python", "sql", "aws", "gcp", "azure",
        "spark", "hadoop", "airflow", "docker", "kubernetes",
        "terraform", "ci/cd", "jenkins", "git",
        "data engineering", "data analysis", "etl",
        "machine learning", "ml", "llm",
        "bigquery", "redshift", "snowflake",
        "linux", "bash"
    ]

    jd_norm = normalize(jd_text)
    resume_norm = normalize(resume_text)

    jd_skills = extract_skills(jd_norm, SKILLS)
    resume_skills = extract_skills(resume_norm, SKILLS)

    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills

    match_percent = (len(matched) / len(jd_skills)) * 100 if jd_skills else 0

    print("JD Skills:", sorted(jd_skills))
    print("Resume Skills:", sorted(resume_skills))
    print("Matched Skills:", sorted(matched))
    print("Missing Skills:", sorted(missing))
    print(f"Skill Match %: {match_percent:.2f}")
