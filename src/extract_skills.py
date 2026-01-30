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

# Add more as you see junk in logs
STOPWORDS = set("""
a an and are as at be been being by can could did do does doing for from had has have having
he her hers him his i if in into is it its me my of on or our ours she so than that the
their them they this those to was we were what when where which who why will with would you your
""".split())

# Common US states show up in legal job posts
US_STATES = set("""
alabama alaska arizona arkansas california colorado connecticut delaware florida georgia hawaii idaho illinois indiana iowa
kansas kentucky louisiana maine maryland massachusetts michigan minnesota mississippi missouri montana nebraska nevada
new hampshire new jersey new mexico new york north carolina north dakota ohio oklahoma oregon pennsylvania
rhode island south carolina south dakota tennessee texas utah vermont virginia washington west virginia wisconsin wyoming
""".split())

# Policy/legal words that aren't skills
LEGAL_JUNK = set("""
equal employment opportunity ordinances notice notices non-sales incentive pay plan qualifications legal state-specific
""".split())

def load_skills(path="src/skills_master.txt") -> list:
    text = Path(path).read_text(encoding="utf-8")
    skills = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        skills.append(line.lower())
    # de-dup keep order
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
    # keep + . # / - because of c++, node.js, c#, ci/cd
    text = re.sub(r"[^a-z0-9\s\+\.\#\/\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_known_skills(text: str, skills: list) -> set:
    found = set()
    for skill in skills:
        if " " in skill or any(ch in skill for ch in ".#+/"):
            if skill in text:
                found.add(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", text):
                found.add(skill)
    return found

def is_bad_token(tok: str) -> bool:
    t = tok.lower().strip()
    if len(t) < 2:
        return True
    if t in STOPWORDS or t in US_STATES or t in LEGAL_JUNK:
        return True
    if t.endswith(".com") or t.endswith(".io") or t.endswith(".ai"):
        return True
    # remove pure numbers or dates
    if re.fullmatch(r"\d+", t):
        return True
    return False

def extract_dynamic_tech_tokens(original_text: str) -> set:
    """
    Only capture likely TECH tokens, not normal words.
    Examples we want: S3, EC2, OAuth, JWT, PyTorch, Node.js, C++, C#, Databricks
    """
    tokens = set()

    # 1) tokens with digits (S3, EC2, Python3)
    tokens |= set(re.findall(r"\b[A-Za-z]{1,10}\d{1,4}\b", original_text))

    # 2) tokens with dot (Node.js) or plus/hash (C++, C#)
    tokens |= set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*\.(?:js|net|io)\b", original_text, flags=re.I))
    tokens |= set(re.findall(r"\bC\+\+|C#\b", original_text))

    # 3) Common all-caps acronyms (JWT, OAuth, SSO, IAM)
    tokens |= set(re.findall(r"\b[A-Z]{2,6}\b", original_text))

    cleaned = set()
    for tok in tokens:
        t = tok.lower()
        if not is_bad_token(t):
            cleaned.add(t)
    return cleaned

if __name__ == "__main__":
    skills = load_skills()

    jd_text = Path("data/jd/jd.txt").read_text(encoding="utf-8")
    resume_text = Path("data/resume/resume.txt").read_text(encoding="utf-8")

    jd_norm = normalize(jd_text)
    resume_norm = normalize(resume_text)

    jd_known = extract_known_skills(jd_norm, skills)
    resume_known = extract_known_skills(resume_norm, skills)

    # safer dynamic tech-only tokens
    jd_dyn = extract_dynamic_tech_tokens(jd_text)
    resume_dyn = extract_dynamic_tech_tokens(resume_text)

    # Only count dynamic terms if they appear in BOTH JD and Resume (reduces noise hard)
    dyn_shared = jd_dyn & resume_dyn

    jd_skills = jd_known | dyn_shared
    resume_skills = resume_known | dyn_shared

    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills

    match_percent = (len(matched) / len(jd_skills)) * 100 if jd_skills else 0

    print("JD Skills Count:", len(jd_skills))
    print("Resume Skills Count:", len(resume_skills))
    print("Matched Skills Count:", len(matched))
    print("Missing Skills Count:", len(missing))
    print(f"Skill Match %: {match_percent:.2f}")

    print("\nMatched Skills:", sorted(matched)[:120])
    print("\nMissing Skills:", sorted(missing)[:120])
