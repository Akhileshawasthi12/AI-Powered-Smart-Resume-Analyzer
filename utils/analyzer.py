import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "html",
    "css",
    "javascript",
    "react",
    "angular",
    "vue",
    "node.js",
    "nodejs",
    "express",
    "mongodb",
    "mysql",
    "sql",
    "postgresql",
    "oracle",
    "git",
    "github",
    "docker",
    "aws",
    "azure",
    "flask",
    "django",
    "spring",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data analysis",
    "data science",
    "communication",
    "problem solving"
]


def extract_skills(text):
    text = text.lower()
    found_skills = []

    for skill in SKILLS:
        skill_pattern = re.escape(skill)

        if re.search(r"(?<!\w)" + skill_pattern + r"(?!\w)", text):
            found_skills.append(skill)

    return sorted(set(found_skills))


def calculate_text_similarity(resume_text, job_description):
    if not resume_text.strip() or not job_description.strip():
        return 0

    vectorizer = TfidfVectorizer(stop_words="english")

    try:
        vectors = vectorizer.fit_transform(
            [resume_text.lower(), job_description.lower()]
        )

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        return round(similarity * 100)

    except ValueError:
        return 0


def calculate_skill_score(matched_skills, required_skills):
    if not required_skills:
        return 0

    return round(
        (len(matched_skills) / len(required_skills)) * 100
    )


def calculate_resume_quality(resume_text):
    score = 0

    text = resume_text.lower()

    sections = [
        "education",
        "experience",
        "skills",
        "project",
        "contact"
    ]

    for section in sections:
        if section in text:
            score += 20

    return min(score, 100)


def get_match_level(score):

    if score >= 80:
        return "Excellent Match"

    elif score >= 60:
        return "Good Match"

    elif score >= 40:
        return "Moderate Match"

    else:
        return "Low Match"


def analyze_resume(resume_text, job_description):

    resume_skills = extract_skills(resume_text)

    required_skills = extract_skills(job_description)

    matched_skills = [
        skill
        for skill in required_skills
        if skill in resume_skills
    ]

    missing_skills = [
        skill
        for skill in required_skills
        if skill not in resume_skills
    ]

    skill_score = calculate_skill_score(
        matched_skills,
        required_skills
    )

    text_score = calculate_text_similarity(
        resume_text,
        job_description
    )

    quality_score = calculate_resume_quality(
        resume_text
    )

    final_score = round(
        (skill_score * 0.60)
        + (text_score * 0.25)
        + (quality_score * 0.15)
    )

    match_level = get_match_level(final_score)

    suggestions = []

    if missing_skills:
        suggestions.append(
            "Consider adding or improving these skills: "
            + ", ".join(missing_skills)
        )

    if "communication" in required_skills:
        if "communication" not in resume_skills:
            suggestions.append(
                "Mention communication or teamwork experience in your resume."
            )

    if "problem solving" in required_skills:
        if "problem solving" not in resume_skills:
            suggestions.append(
                "Add examples that demonstrate problem-solving ability."
            )

    if "project" not in resume_text.lower():
        suggestions.append(
            "Add relevant academic or personal projects to your resume."
        )

    if not suggestions:
        suggestions.append(
            "Your resume matches the job requirements well."
        )

    return {
        "score": final_score,
        "skill_score": skill_score,
        "text_score": text_score,
        "quality_score": quality_score,
        "match_level": match_level,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "suggestions": suggestions
    }