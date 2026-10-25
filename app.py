from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session
)
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from io import BytesIO
from xml.sax.saxutils import escape
import os

from utils.extractor import extract_text
from utils.analyzer import analyze_resume


app = Flask(__name__)
app.secret_key = "resume-analyzer-local-secret-key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return "Error: Resume file was not provided.", 400

    resume = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if not resume or not resume.filename:
        return "Please select a resume file.", 400

    if not allowed_file(resume.filename):
        return "Unsupported file. Please upload a PDF or DOCX file.", 400

    if not job_description:
        return "Please enter the job description.", 400

    filename = secure_filename(resume.filename)

    if not filename:
        return "Invalid filename.", 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    resume.save(file_path)

    try:
        resume_text = extract_text(file_path)
    except Exception:
        app.logger.exception("Resume text extraction failed")
        return "Could not read this resume. Please check the file and try again.", 400

    if not resume_text or not resume_text.strip():
        return (
            "No readable text was found. If this is a scanned PDF, "
            "OCR may be required.",
            400
        )

    analysis_result = analyze_resume(resume_text, job_description)

    # Keep the latest report data for the PDF download route.
    session["resume_report"] = {
        "filename": filename,
        "score": analysis_result["score"],
        "skill_score": analysis_result["skill_score"],
        "text_score": analysis_result["text_score"],
        "quality_score": analysis_result["quality_score"],
        "match_level": analysis_result["match_level"],
        "resume_skills": analysis_result["resume_skills"],
        "required_skills": analysis_result["required_skills"],
        "matched_skills": analysis_result["matched_skills"],
        "missing_skills": analysis_result["missing_skills"],
        "suggestions": analysis_result["suggestions"]
    }

    return render_template(
        "result.html",
        filename=filename,
        score=analysis_result["score"],
        skill_score=analysis_result["skill_score"],
        text_score=analysis_result["text_score"],
        quality_score=analysis_result["quality_score"],
        match_level=analysis_result["match_level"],
        resume_skills=analysis_result["resume_skills"],
        required_skills=analysis_result["required_skills"],
        matched_skills=analysis_result["matched_skills"],
        missing_skills=analysis_result["missing_skills"],
        suggestions=analysis_result["suggestions"]
    )


@app.route("/download-report", methods=["GET"])
def download_report():
    report = session.get("resume_report")

    if not report:
        return (
            "No analysis report found. Please analyze a resume first.",
            404
        )

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    title_style.textColor = colors.HexColor("#4F46A5")

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    story = [
        Paragraph("AI-Powered Smart Resume Analyzer", title_style),
        Spacer(1, 12),
        Paragraph("Resume Analysis Report", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(
            f"<b>Resume:</b> {escape(report['filename'])}",
            styles["Normal"]
        ),
        Spacer(1, 12),
        Paragraph(
            f"<b>Overall Match Score: {report['score']}%</b>",
            styles["Heading2"]
        ),
        Paragraph(
            f"<b>Match Level:</b> {escape(report['match_level'])}",
            styles["Normal"]
        ),
        Spacer(1, 12),
        Paragraph("Score Breakdown", styles["Heading2"]),
        Paragraph(
            f"Skills Match: {report['skill_score']}%",
            styles["Normal"]
        ),
        Paragraph(
            f"Content Similarity: {report['text_score']}%",
            styles["Normal"]
        ),
        Paragraph(
            f"Resume Quality: {report['quality_score']}%",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]

    def add_list_section(title, items):
        story.append(Paragraph(escape(title), styles["Heading2"]))
        if not items:
            story.append(Paragraph("None detected.", styles["Normal"]))
        else:
            for item in items:
                safe_item = escape(str(item))
                story.append(
                    Paragraph(f"&bull; {safe_item}", styles["Normal"])
                )
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    add_list_section("Resume Skills", report["resume_skills"])
    add_list_section("Required Skills", report["required_skills"])
    add_list_section("Matched Skills", report["matched_skills"])
    add_list_section("Missing Skills", report["missing_skills"])
    add_list_section("Improvement Suggestions", report["suggestions"])

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Note: This is a project-generated analytical indicator, "
            "not an official ATS score or a guarantee of hiring outcomes.",
            styles["Italic"]
        )
    )

    document.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Resume_Analysis_Report.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)