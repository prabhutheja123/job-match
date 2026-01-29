import os
from pathlib import Path

# Create folders
Path("inputs").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)

# Read inputs from GitHub Actions
job_description = os.environ.get("JD", "")
resume_text = os.environ.get("RESUME", "")

# Save inputs to files
with open("inputs/job_description.txt", "w", encoding="utf-8") as f:
    f.write(job_description)

with open("inputs/resume.txt", "w", encoding="utf-8") as f:
    f.write(resume_text)

print("Inputs saved successfully")
print("JD chars:", len(job_description))
print("Resume chars:", len(resume_text))
