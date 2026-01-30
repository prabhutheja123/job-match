import re
from pathlib import Path

ALIASES = {
    # language shortcuts / variants
    "js": "javascript",
    "ts": "typescript",
    "node js": "node.js",
    "golang": "go",
    "c sharp": "c#",
    "dot net": "dotnet",
    "asp net": "asp.net",

    # cloud variations
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "amazon web services": "aws",

    # devops variations
    "ci cd": "ci/cd",
    "k8s": "kubernetes",
    "argocd": "argo cd",

    # data variations
    "pyspark": "spark",
    "spark sql": "spark",
    "gcs": "cloud storage",
}

COMMON_WORDS = set([
    "and","or","with","for","the","a","an","to","of","in","on","by","using",
    "experience","knowledge","skills","years","responsibilities","required","preferred"
])

def load_skills(path="src/skills_master.txt") -> list:
    text = Path(path).read_text(encoding="utf-8")
    skills = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        skills.append(line.lower())
    # de-dup, keep order
    seen = set()
    out = []
    for s in skills:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

def normalize(text: str) -> str:
    text = text.lower()
    for k, v in ALIASES.items():
        text = text.replace(k, v)
    # keep + and . and # for skills like c++, node.js, c#
    text = re.sub(r"[^a-z0-9\s\+\.\#\/\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_known_skills(text: str, skills: list) -> set:
    found = set()
    # word-boundary-ish matching for single words; substring for multiword
    for skill in skills:
        if " " in skill or "." in skill or "#" in skill or "+" in skill or "/" in skill:
            if skill in text:
                found.add(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", text):
                found.add(skill)
    return found

def extract_dynamic_terms(original_text: str) -> set:
    # captures things like Databricks, Snowflake, Kubernetes, PowerBI, etc.
    candidates = set(re.findall(r"\b[A-Z][A-Za-z0-9+\-\.]{2,}\b", original_text))
    return {c.lower() for c in candidates if c.lower() not in COMMON_WORDS}

if __name__ == "__main__":
    skills = load_skills()

    jd_text = Path("data/jd/jd.txt").read_text(encoding="utf-8")
    resume_text = Path("data/resume/resume.txt").read_text(encoding="utf-8")

    jd_norm = normalize(jd_text)
    resume_norm = normalize(resume_text)

    jd_known = extract_known_skills(jd_norm, skills)
    resume_known = extract_known_skills(resume_norm, skills)

    jd_dynamic = extract_dynamic_terms(jd_text)
    resume_dynamic = extract_dynamic_terms(resume_text)

    jd_skills = jd_known | jd_dynamic
    resume_skills = resume_known | resume_dynamic

    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills

    match_percent = (len(matched) / len(jd_skills)) * 100 if jd_skills else 0

    print("JD Skills Count:", len(jd_skills))
    print("Resume Skills Count:", len(resume_skills))
    print("Matched Skills Count:", len(matched))
    print("Missing Skills Count:", len(missing))
    print(f"Skill Match %: {match_percent:.2f}")

    # Optional: show top lists (keeps logs readable)
    print("\nMatched Skills:", sorted(matched)[:80])
    print("\nMissing Skills:", sorted(missing)[:80])
