from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import os
import json
import markdown

from src.pipeline.rag_pipeline import RAGPipeline
from src.database.db import create_tables, get_connection
from src.services.tracking_service import TrackingService

router = APIRouter()
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "frontend/templates")
)


pipeline = RAGPipeline()
tracker = TrackingService()

create_tables()

# ---------------- LOGIN ----------------
@router.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
)



@router.post("/login")
def login(request: Request, username: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    request.session["user_id"] = user_id

    return RedirectResponse("/dashboard", status_code=302)

# ---------------- DASHBOARD ----------------
@router.get("/dashboard")
def dashboard(request: Request):
    user_id = request.session.get("user_id")
    history = tracker.get_recent_chats(user_id)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "history": history
        }
    )

# ---------------- UPLOAD ----------------
# @router.post("/upload")
# async def upload(request: Request, file: UploadFile = File(...)):
#     try:
#         user_id = request.session.get("user_id")

#         if not user_id:
#             return RedirectResponse("/", status_code=302)

#         path = os.path.join("DATA", "raw", file.filename)

#         with open(path, "wb") as f:
#             f.write(await file.read())

#         pipeline.ingest(path, user_id)

#         return RedirectResponse("/dashboard", status_code=302)

#     except Exception:
#         return {"error": "Upload failed"}

# ---------------- CHAT ----------------

@router.get("/chat")
def chat_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "request": request
        }
    )
    
@router.post("/chat")
def chat(
    request: Request,
    query: str = Form(...)
):

    user_id = request.session.get("user_id")

    answer = pipeline.ask_question(user_id, query)

    # SAVE CHAT HISTORY
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chats (user_id, question, answer)
        VALUES (?, ?, ?)
        """,
        (user_id, query, answer)
    )

    conn.commit()

    conn.close()

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "answer": answer
        }
    )
    
    
@router.post("/upload")
async def upload(request: Request, file: UploadFile = File(None)):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/", status_code=302)

    # No file selected
    if file is None or file.filename == "":
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "error": "Please select a file first."
            }
        )

    try:
        os.makedirs("DATA/raw", exist_ok=True)

        path = os.path.join("DATA", "raw", file.filename)

        with open(path, "wb") as f:
            f.write(await file.read())

        pipeline.ingest(path, user_id)

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "success": f"{file.filename} uploaded successfully."
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "error": f"Upload failed: {str(e)}"
            }
        )

@router.post("/ask")
def ask(request: Request, query: str = Form(...), user_answer: str = Form(None)):
    try:
        user_id = request.session.get("user_id")
    
        if not user_id:

            return RedirectResponse("/", status_code=302)

        result = pipeline.generate_answer(query, user_id, user_answer)
        html_output = markdown.markdown(result["answer"])

        chats = tracker.get_recent_chats(user_id)

        return templates.TemplateResponse(
            request=request,
            name="chat.html",
            context={
                "request": request,
                "output": html_output,
                "score": result["score"],
                "feedback": result["feedback"],
                "chats": chats
            }
        )
    except Exception as e:
        return {"error": "something went wrong", "details": str(e)}
    

# ---------------- SUMMARY ----------------
@router.get("/summary")
def summary_page(request: Request):
    return templates.TemplateResponse(
        request=request,

        name="summary.html",
        context={
            "request": request,
            "summary": None
        }
    )


@router.post("/summary")
def summary(request: Request, topics: str = Form(None)):
    try:
        user_id = request.session.get("user_id")

        if not user_id:
            return RedirectResponse("/", status_code=302)

        topic_list = topics.split(",") if topics else None
        result = pipeline.summarize(user_id, topic_list)
        

        return templates.TemplateResponse(
            request=request,
            name="summary.html",
            context={
                "request": request,
                "summary": markdown.markdown(result)
            }
        )

    except Exception:
        return {"error": "Summary failed"}

# ---------------- QUESTIONS ----------------
@router.post("/generate-questions")
def generate_questions(request: Request, num: int = Form(5)):
    user_id = request.session.get("user_id")
    
    if not user_id:

        return RedirectResponse("/", status_code=302)

    output = pipeline.generate_questions(user_id, num)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "output": output
        }
    )

# ---------------- MCQ ----------------
@router.get("/mcq")
def mcq(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/", status_code=302)

    mcqs = pipeline.generate_mcqs(user_id)

    request.session["mcqs"] = mcqs

    return templates.TemplateResponse(
        request=request,
        name="mcq.html",
        context={
            "request": request,
            "mcqs": mcqs
        }
    )

@router.post("/submit-mcq")
async def submit_mcq(request: Request):
    try:
        form = await request.form()
        mcqs = request.session.get("mcqs", [])

        score = 0
        results = []

        for i, q in enumerate(mcqs):
            user_ans = form.get(f"q{i}")
            correct = q["answer"]

            if user_ans == correct:
                score += 1

            results.append({
                "question": q["question"],
                "user_answer": user_ans,
                "correct_answer": correct,
                "explanation": q["explanation"]
            })

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "request": request,
                "score": score,
                "total": len(mcqs),
                "results": results
            }
        )

    except Exception:
        return {"error": "MCQ submission failed"}

# ---------------- MSQ ----------------
@router.get("/msq")
def msq(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/", status_code=302)

    msqs = pipeline.generate_msqs(user_id)

    request.session["msqs"] = msqs

    return templates.TemplateResponse(
        request=request,
        name="msq.html",
        context={
            "request": request,
            "msqs": msqs
        }
    )

@router.post("/submit-msq")
async def submit_msq(request: Request):

    form = await request.form()

    score = 0
    total = 0

    user_answers = dict(form)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "score": score,
            "total": total,
            "answers": user_answers
        }
    )

# ---------------- ANALYTICS ----------------
@router.get("/analytics")
def analytics(request: Request):
    user_id = request.session.get("user_id")
    
    if not user_id:

        return RedirectResponse("/", status_code=302)

    stats = tracker.analyze_performance(user_id)
    weak = tracker.get_weak_topics(user_id)

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "request": request,
            "stats": stats,
            "weak_topics": weak
        }
    )





























































































































