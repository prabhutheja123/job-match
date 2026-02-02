from __future__ import annotations
from pathlib import Path
from collections import Counter
import re

OUT_DIR = Path("out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SAFE_ALWAYS_ADD = {
    # Generic tools/phrases that are safe to include as "familiarity" in many roles if JD expects them.
    # Keep this conservative. User can expand later.
    "jupyter", "pandas", "data analysis", "elt", "etl"
}

SECTION_HEADERS = [
    "SUMMARY",
    "CORE SKILLS",
    "EXPERIENCE",
    "PROJECTS",
    "EDUCATION",
    "CERTIFICATIONS",
]

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
    # keep . + # - for tech tokens (node.js, c++, c#)
    t = re.sub(r"[^a-z0-9\.\+\#\-\s/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_known_skills(text: str, skills: list[str]) -> set[str]:
    """
    Simple contains-based extraction; your project already has a stronger extractor.
    Keep this here as standalone, but you can import your existing functions later.
    """
    t = normalize(text)
    found = set()
    for s in skills:
        # word boundary when possible
        if " " in s or "." in s or "+" in s or "#" in s or "/" in s:
            if s in t:
                found.add(s)
        else:
            if re.search(rf"\b{re.escape(s)}\b", t):
                found.add(s)
    return found

def top_keywords(jd_text: str, limit: int = 10) -> list[str]:
    """
    Extract frequent meaningful tokens from JD for summary.
    """
    t = normalize(jd_text)
    tokens = [w for w in t.split() if len(w) > 2]
    stop = {"and","the","for","with","you","are","our","your","will","this","that","from","into","have","has","had"}
    tokens = [w for w in tokens if w not in stop]
    common = [w for w, _ in Counter(tokens).most_common(limit * 3)]
    # filter junk and keep a compact list
    out = []
    for w in common:
        if w.isdigit():
            continue
        if w in out:
            continue
        out.append(w)
        if len(out) >= limit:
            break
    return out

def guess_job_title(jd_text: str) -> str:
    """
    Very lightweight title guess from common patterns.
    Falls back to 'Professional'.
    """
    t = jd_text.lower()
    candidates = [
        "data engineer","data analyst","business analyst","software engineer","devops engineer",
        "cloud engineer","project manager","product manager","accountant","sales associate",
        "customer service","marketing specialist","hr specialist","financial analyst"
    ]
    for c in candidates:
        if c in t:
            return c.title()
    return "Professional"

def build_summary(job_title: str, jd_keywords: list[str], matched: set[str], missing: set[str]) -> str:
    # pick 4–6 “strong” items to mention
    strong = []
    for s in sorted(matched):
        if len(strong) >= 5:
            break
        strong.append(s)
    # add 2 missing (only safe) to show alignment without lying
    safe_missing = [s for s in sorted(missing) if s in SAFE_ALWAYS_ADD][:2]
    kw = ", ".join(jd_keywords[:5]) if jd_keywords else ""
    skill_line = ", ".join(strong + safe_missing) if (strong or safe_missing) else ""
    bits = []
    bits.append(f"{job_title} with experience supporting JD-aligned responsibilities and delivering measurable outcomes.")
    if kw:
        bits.append(f"Focus areas include {kw}.")
    if skill_line:
        bits.append(f"Tools/skills: {skill_line}.")
    return " ".join(bits)

def build_skills_section(matched: set[str], missing: set[str], max_items: int = 24) -> str:
    # prioritize matched, then safe missing, then the rest missing
    safe_missing = [s for s in missing if s in SAFE_ALWAYS_ADD]
    ordered = list(sorted(matched)) + list(sorted(set(safe_missing))) + list(sorted(missing - set(safe_missing)))
    # trim
    ordered = ordered[:max_items]
    return ", ".join(ordered) if ordered else "Add role-relevant skills here"

def build_experience_section(resume_text: str, jd_keywords: list[str], matched: set[str], missing: set[str]) -> str:
    """
    Generic bullets that remain true for many roles.
    We DO NOT invent companies or years.
    We reuse the user's existing experience text, then add a small 'Aligned Highlights' block.
    """
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
