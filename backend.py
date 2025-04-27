from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from src.helper import get_pdf_text, get_text_chunks, get_vector_store, user_query, save_text_to_pdf
import os

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Processing API!"}

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile):
    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Extract text from the PDF
        raw_text = get_pdf_text([temp_file_path])
        if not raw_text.strip():
            return JSONResponse(content={"error": "Couldn't extract any text from the PDF."}, status_code=400)

        # Split text into chunks
        text_chunks = get_text_chunks(raw_text)
        if not text_chunks:
            return JSONResponse(content={"error": "Failed to split text into chunks."}, status_code=400)

        # Generate vector store
        get_vector_store(text_chunks)

        # Clean up temporary file
        os.remove(temp_file_path)

        return {"message": "PDF processed successfully."}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/generate-questions/")
async def generate_questions(
    question: str = Form(...),
    num_questions: int = Form(...),
    difficulty_level: str = Form(...),
    question_types: str = Form(...),
    include_answers: str = Form("Yes")
):
    try:
        response = user_query(
            question=question,
            num_questions=num_questions,
            difficulty_level=difficulty_level,
            question_types=question_types,
            include_answers=include_answers
        )
        return {"questions": response}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/save-to-pdf/")
async def save_to_pdf(content: str = Form(...), filename: str = Form(...)):
    try:
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        file_path = save_text_to_pdf(content, filename=filename)
        return {"message": "PDF saved successfully.", "file_path": file_path}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

with open("README.md", "r", encoding="utf-8") as file:
    content = file.read()

with open("README.md", "w", encoding="utf-8") as file:
    file.write(content)