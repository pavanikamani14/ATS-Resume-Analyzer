import os
from flask import Flask, request, jsonify, render_template
import PyPDF2
from google import genai

# ==============================
# CONFIG
# ==============================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = genai.Client(api_key="YOUR API KEY")  # 🔐 move to env later

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==============================
# PDF TEXT EXTRACTION
# ==============================
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
    return extracted_text

# ==============================
# GEMINI RESUME ANALYSIS
# ==============================
def analyze_resume(resume_text, job_description):
    prompt = f"""
You are an ATS system.

Compare the resume with the job description and give:
1. ATS Match score (out of 100)
2. Strengths
3. Weaknesses
4. Missing skills
5. Suggestions

Resume:
{resume_text}

Job Description:
{job_description}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# ==============================
# ROUTES
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description")

    if not resume_file or not job_description:
        return jsonify({"error": "Missing resume or job description"}), 400

    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(pdf_path)

    resume_text = extract_text_from_pdf(pdf_path)
    ats_result = analyze_resume(resume_text, job_description)

    return jsonify({
        "parsed_resume": resume_text,
        "parsed_job_description": job_description,
        "ats_result": ats_result
    })

# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(port=5000, debug=True)
