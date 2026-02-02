from __future__ import annotations

from pathlib import Path
import re

OUT_DIR = Path("out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Keep conservative: only add if JD asks AND it's generally safe to claim "familiarity"
SAFE_ALWAYS_ADD = {
    "jupyter", "pandas", "data analysis", "etl", "elt"
}

# Minimal "safe" non-skill keywords that can help summary without sounding stuffed
SAFE_BUSINESS_TERMS = {
    "stakeholders", "reporting", "dashboards", "documentation", "requirements",
    "quality", "automation", "monitoring", "compliance", "security"
}

def read_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore").strip()

def load_skills(path: str = "src/skills_master.txt") -> list[str]:
    text = read_text(path)
    skills = []
    for line in text.splitlines():
        s = line.strip().lower()
        if not s or s.startswith("#"):
            continue
        skills.append(s)

    # de-dupe, preserve order
    seen = set()
    out = []
    for s in skills:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

def normalize(text: str) -> str:
    t = text.lower()
    # keep . + # - / for tech tokens (node.js, c++, c#, ci/cd)
    t = re.sub(r"[^a-z0-9\.\+\#\-\s/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_known_skills(text: str, skills: list[str]) -> set[str]:
    """
    Simple contains-based extraction.
    (You can swap this later to import your stronger extractor.)
    """
    t = normalize(text)
    found = set()
    for s in skills:
        if not s:
            continue

        # Phrase / special tokens
        if (" " in s) or ("." in s) or ("+" in s) or ("#" in s) or ("/" in s) or ("-" in s):
            if s in t:
                found.add(s)
        else:
            # Single word skill
            if re.search(rf"\b{re.escape(s)}\b", t):
                found.add(s)
    return found

def guess_job_title(jd_text: str) -> str:
    """
    Lightweight title guess; fallback is "Professional".
    """
    t = jd_text.lower()
    candidates = [
        "data engineer", "data analyst", "business analyst", "software engineer", "devops engineer",
        "cloud engineer", "project manager", "product manager", "accountant", "sales associate",
        "customer service", "marketing specialist", "hr specialist", "financial analyst",
    ]
    for c in candidates:
        if c in t:
            return c.title()
    return "Professional"

def extract_contact_block(resume_text: str) -> dict[str, str]:
    """
    Pull basic contact info from resume text (if present).
    Keeps it ATS simple. If missing, uses blanks (no placeholders).
    """
    text = resume_text.strip()

    # Email
    email_match = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""

    # Phone (very simple)
    phone_match = re.search(r"(\+?\d[\d\-\s\(\)]{8,}\d)", text)
    phone = phone_match.group(1).strip() if phone_match else ""

    # Name: take first non-empty line if it looks like a name (letters + spaces)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = ""
    if lines:
        first = lines[0]
        if re.fullmatch(r"[A-Za-z][A-Za-z\s\.\-']{2,60}", first) and len(first.split()) <= 5:
            name = first

    # Location: try to detect "Location:" line
    loc = ""
    for ln in lines[:25]:
        if "location" in ln.lower():
            # e.g. Location: New Jersey
            parts = ln.split(":")
            if len(parts) >= 2:
                loc = parts[1].strip()
                break

    return {"name": name, "email": email, "phone": phone, "location": loc}

def extract_education_section(resume_text: str) -> list[str]:
    """
    Extract education lines from resume text.

    Strategy:
    1) Find an EDUCATION heading (EDUCATION / Education / Academic Background).
    2) Capture lines until the next likely section heading.
    3) Clean + return as bullet-ready lines.
    4) Fallback: pattern match common degree/university/year lines.
    """
    raw = resume_text.strip()
    if not raw:
        return []

    lines = [ln.rstrip() for ln in raw.splitlines()]
    norm = [ln.strip().lower() for ln in lines]

    edu_headings = {
        "education",
        "academic background",
        "academics",
        "education & certifications",
        "qualification",
        "qualifications",
    }

    stop_headings = {
        "experience",
        "professional experience",
        "work experience",
        "projects",
        "skills",
        "technical skills",
        "certifications",
        "summary",
        "interests",
        "hobbies",
        "achievements",
        "publications",
    }

    # find education heading
    start_idx = None
    for i, h in enumerate(norm):
        h_clean = re.sub(r"[^a-z\s&]", "", h).strip()
        if h_clean in edu_headings:
            start_idx = i + 1
            break

    # Extract block under EDUCATION heading
    if start_idx is not None:
        extracted: list[str] = []
        for j in range(start_idx, len(lines)):
            ln = lines[j].strip()
            if not ln:
                continue

            chk = re.sub(r"[^a-z\s&]", "", ln.lower()).strip()
            if chk in stop_headings:
                break

            extracted.append(ln)

        cleaned = []
        for ln in extracted:
            ln = re.sub(r"^\s*[-•\u2022]+\s*", "", ln).strip()
            if ln:
                cleaned.append(ln)

        return cleaned[:5]

    # Fallback: pattern matching if no heading
    degree_words = r"(b\.?tech|bachelor|master|m\.?s\.?|m\.?tech|mba|phd|b\.?sc|m\.?sc)"
    uni_words = r"(university|college|institute|school)"
    year_words = r"(19\d{2}|20\d{2}|present|current)"

    fallback = []
    for ln in lines:
        l = ln.strip()
        if not l:
            continue
        low = l.lower()
        if re.search(degree_words, low) or re.search(uni_words, low):
            if re.search(year_words, low):
                fallback.append(l)
            else:
                fallback.append(l)

    out = []
    seen = set()
    for ln in fallback:
        key = ln.lower()
        if key in seen:
            continue
        seen.add(key)
        ln = re.sub(r"^\s*[-•\u2022]+\s*", "", ln).strip()
        if ln:
            out.append(ln)
        if len(out) >= 4:
            break

    return out

def build_summary(job_title: str, matched: set[str], missing: set[str], jd_text: str) -> str:
    """
    Human-sounding, low-buzzword summary.
    Uses matched skills + (optionally) 1-2 safe missing skills.
    Avoids random JD words.
    """
    strong = [s for s in sorted(matched) if s not in {"data engineering"}]
    safe_missing = [s for s in sorted(missing) if s in SAFE_ALWAYS_ADD][:2]

    # add 1-2 business terms only if present in JD
    t = normalize(jd_text)
    biz_terms = [w for w in SAFE_BUSINESS_TERMS if re.search(rf"\b{re.escape(w)}\b", t)]
    biz_terms = sorted(biz_terms)[:2]

    parts = [f"{job_title} with hands-on experience delivering JD-aligned work in a production environment."]
    if strong:
        parts.append(f"Strengths include {', '.join(strong[:5])}.")
    if biz_terms:
        parts.append(f"Comfortable with {', '.join(biz_terms)}.")
    if safe_missing:
        parts.append(f"Additional alignment: {', '.join(safe_missing)}.")

    return " ".join(parts)

def build_skills_section(matched: set[str], missing: set[str], max_items: int = 18) -> str:
    """
    Clean skills list. Avoids dumping too many items.
    """
    safe_missing = [s for s in sorted(missing) if s in SAFE_ALWAYS_ADD]
    ordered = list(sorted(matched)) + safe_missing

    # de-dupe, cap length
    out = []
    seen = set()
    for s in ordered:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= max_items:
            break

    return ", ".join(out)

def build_experience_bullets(job_title: str, matched: set[str], missing: set[str]) -> list[str]:
    """
    Generates 4–6 defensible bullets WITHOUT pasting the whole resume.
    No fake companies, no fake dates.
    """
    bullets: list[str] = []

    # tech-oriented bullets if tech skills exist
    if {"python", "sql"} & matched:
        bullets.append("Built and supported data workflows using Python and SQL, including validation and basic monitoring.")
    if "airflow" in matched:
        bullets.append("Automated scheduled workflows with Airflow DAGs to improve reliability and repeatability of pipeline runs.")
    if "dbt" in matched or "dbt" in missing:
        if "dbt" in matched:
            bullets.append("Developed transformation models with dbt-style practices (staging to marts) and maintained reusable SQL logic.")
        else:
            bullets.append("Familiarity with dbt concepts for SQL-based transformations and modular modeling (staging to marts).")
    if "data modeling" in matched:
        bullets.append("Applied data modeling principles to produce analytics-ready datasets for reporting and downstream consumption.")
    if "data quality" in matched:
        bullets.append("Implemented data quality checks (nulls, schema, freshness) to reduce defects and improve trust in datasets.")
    if "aws" in matched:
        bullets.append("Worked with AWS services for data storage and processing while following access control and security basics.")

    # non-tech friendly fallback bullets
    if not bullets:
        bullets.append("Delivered JD-aligned responsibilities with a focus on quality, documentation, and measurable business outcomes.")
        bullets.append("Collaborated with cross-functional stakeholders to translate requirements into clear deliverables.")

    # safe missing skills (soft insertion)
    safe_missing = [s for s in sorted(missing) if s in SAFE_ALWAYS_ADD][:3]
    if safe_missing:
        bullets.append(f"Used tools aligned to the role including {', '.join(safe_missing)} for analysis and validation.")

    return bullets[:6]

def build_projects_section(job_title: str, matched: set[str]) -> list[str]:
    """
    Keep projects short and ATS clean.
    """
    projects: list[str] = []

    if "github actions" in matched or "git" in matched:
        projects.append("Job Match Copilot (GitHub Actions): Automates JD vs resume skill matching and produces tailored ATS resume output.")
    else:
        projects.append("Job Match Copilot: Automated JD vs resume matching to identify skill gaps and tailor resume content.")

    if {"python", "sql", "airflow", "etl", "elt"} & matched:
        projects.append("Pipeline Mini-Project: Built a small ETL/ELT workflow using Python/SQL with basic validation and repeatable runs.")

    return projects[:2]

def build_resume(jd_text: str, resume_text: str, skills: list[str]) -> str:
    job_title = guess_job_title(jd_text)

    jd_found = extract_known_skills(jd_text, skills)
    resume_found = extract_known_skills(resume_text, skills)

    matched = jd_found & resume_found
    missing = jd_found - resume_found

    contact = extract_contact_block(resume_text)
    name = contact["name"] or ""
    email = contact["email"] or ""
    phone = contact["phone"] or ""
    location = contact["location"] or ""

    summary = build_summary(job_title, matched, missing, jd_text)
    skills_line = build_skills_section(matched, missing)
    exp_bullets = build_experience_bullets(job_title, matched, missing)
    projects = build_projects_section(job_title, matched)

    education_lines = extract_education_section(resume_text)

    header_parts = [p for p in [job_title, location] if p]
    header_line = " | ".join(header_parts).strip()

    contact_parts = [p for p in [phone, email] if p]
    contact_line = " | ".join(contact_parts).strip()

    out_lines = []
    if name:
        out_lines.append(name)
    if header_line:
        out_lines.append(header_line)
    if contact_line:
        out_lines.append(contact_line)

    out_lines.append("")
    out_lines.append("SUMMARY")
    out_lines.append(summary)
    out_lines.append("")
    out_lines.append("CORE SKILLS")
    out_lines.append(skills_line if skills_line else "")
    out_lines.append("")
    out_lines.append("EXPERIENCE")
    for b in exp_bullets:
        out_lines.append(f"- {b}")
    out_lines.append("")
    out_lines.append("PROJECTS")
    for p in projects:
        out_lines.append(f"- {p}")
    out_lines.append("")
    out_lines.append("EDUCATION")
    if education_lines:
        for e in education_lines:
            out_lines.append(f"- {e}")
    else:
        out_lines.append("- Education details available upon request")

    return "\n".join(out_lines).strip() + "\n"

def main():
    jd = read_text("data/jd/jd.txt")
    resume = read_text("data/resume/resume.txt")

    if not jd or not resume:
        raise SystemExit("Missing inputs. Ensure data/jd/jd.txt and data/resume/resume.txt exist.")

    skills = load_skills("src/skills_master.txt")
    out = build_resume(jd, resume, skills)

    out_path = OUT_DIR / "tailored_resume.txt"
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()    """
    base = resume_text.strip()
    if not base:
        base = "- Add your existing experience bullets here\n"

    # Aligned highlights: generic, defensible, based on matched/missing
    highlights = []
    if matched:
        highlights.append(f"- Worked with: {', '.join(list(sorted(matched))[:8])}.")
    safe_missing = [s for s in sorted(missing) if s in SAFE_ALWAYS_ADD][:3]
    if safe_missing:
        highlights.append(f"- Familiarity/working knowledge aligned to JD: {', '.join(safe_missing)}.")
    if jd_keywords:
        highlights.append(f"- Supported business goals related to: {', '.join(jd_keywords[:6])}.")
    highlights_block = "\n".join(highlights) if highlights else "- Tailor highlights based on JD.\n"

    return f"""{base}

Aligned Highlights (JD keywords)
{highlights_block}
"""

def build_resume(jd_text: str, resume_text: str, skills: list[str]) -> str:
    job_title = guess_job_title(jd_text)
    jd_kw = top_keywords(jd_text, limit=10)

    jd_found = extract_known_skills(jd_text, skills)
    resume_found = extract_known_skills(resume_text, skills)

    matched = jd_found & resume_found
    missing = jd_found - resume_found

    summary = build_summary(job_title, jd_kw, matched, missing)
    skills_line = build_skills_section(matched, missing)
    exp = build_experience_section(resume_text, jd_kw, matched, missing)

    # NOTE: user details are placeholders, universal for any user.
    return f"""FULL NAME
{job_title} | Location | Email | LinkedIn | GitHub/Portfolio

SUMMARY
{summary}

CORE SKILLS
{skills_line}

EXPERIENCE
{exp}

PROJECTS
- (Optional) Add 1–3 projects relevant to the JD. Include GitHub/portfolio links.

EDUCATION
- Degree | University | Year

CERTIFICATIONS
- (Optional) Relevant certifications
"""

def main():
    jd = read_text("data/jd/jd.txt")
    resume = read_text("data/resume/resume.txt")

    if not jd or not resume:
        raise SystemExit("Missing inputs. Ensure data/jd/jd.txt and data/resume/resume.txt exist.")

    skills = load_skills("src/skills_master.txt")
    out = build_resume(jd, resume, skills)

    out_path = OUT_DIR / "tailored_resume.txt"
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
