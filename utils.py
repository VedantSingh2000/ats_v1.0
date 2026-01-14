import google.generativeai as genai
import re
import json
from docx import Document
from pypdf import PdfReader

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        return f"Error reading file: {e}"
    return ""

def rank_resumes_with_gemini(resumes_dict, jd_text, model):
    """
    Takes a dictionary {filename: text} and a JD.
    Returns a JSON list of ranked candidates.
    """
    
    # Construct a big prompt with all resumes
    candidates_text = ""
    for filename, text in resumes_dict.items():
        candidates_text += f"\n--- CANDIDATE START ({filename}) ---\n{text[:10000]}\n--- CANDIDATE END ---\n"

    prompt = f"""
    Act as a Senior Technical Recruiter and ATS System.
    
    JOB DESCRIPTION:
    {jd_text[:5000]}
    
    CANDIDATES:
    {candidates_text}
    
    TASK:
    1. Analyze all candidates against the JD.
    2. Rank them from #1 (Best Fit) to Last.
    3. Return the result strictly as a JSON list of objects.
    
    JSON FORMAT:
    [
        {{
            "rank": 1,
            "filename": "resume_filename.pdf",
            "candidate_name": "extracted name",
            "match_percentage": 85,
            "skills_match": "Python, SQL, AWS",
            "missing_skills": "Docker, Kubernetes",
            "reason": "Strongest match because..."
        }},
        ...
    ]
    
    Do not output markdown code blocks. Just the raw JSON string.
    """

    try:
        response = model.generate_content(prompt)
        # Clean JSON
        txt = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(txt)
        return data
    except Exception as e:
        return [{"filename": "Error", "reason": str(e)}]
