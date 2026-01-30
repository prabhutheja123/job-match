import os
from pathlib import Path

# Final folder structure (LOCKED)
jd_dir = Path("data/jd")
resume_dir = Path("data/resume")
out_dir = Path("out")

jd_dir.mkdir(parents=True, exist_ok=True)
resume_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)

# Read inputs from GitHub Actions
job_description = os.environ.get("JD", "")
resume_text = os.environ.get("RESUME", "")

# Save inputs
(jd_dir / "jd.txt").write_text(job_description, encoding="utf-8")
(resume_dir / "resume.txt").write_text(resume_text, encoding="utf-8")

print("Inputs saved successfully")
print("JD chars:", len(job_description))
print("Resume chars:", len(resume_text))
