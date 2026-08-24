from backend.app.services.pdf_extractor import extract_text_from_pdf
from backend.app.services.resume_parser import parse_resume


PDF_PATH = r"D:\RESUMECV_NEW.pdf"


text = extract_text_from_pdf(PDF_PATH)

resume = parse_resume(text)

print("\n===== PARSED RESUME =====")

print("\nNAME:")
print(resume.name)

print("\nEMAIL:")
print(resume.email)

print("\nPHONE:")
print(resume.phone)

print("\nSKILLS:")
for skill in resume.skills:
    print("-", skill)

print("\nEDUCATION:")
for education in resume.education:
    print(education.model_dump())

print("\nPROJECTS:")
for project in resume.projects:
    print(project.model_dump())

print("\nCERTIFICATIONS:")
for certification in resume.certifications:
    print("-", certification)

print("\nLANGUAGES:")
for language in resume.languages:
    print("-", language)

print("\n===== END =====")