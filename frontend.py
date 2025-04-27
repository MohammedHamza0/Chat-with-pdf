import streamlit as st
import requests
from src.helper import (get_pdf_text, 
                        get_text_chunks, 
                        get_vector_store, 
                        user_query,
                        save_text_to_pdf)

def process_pdf_via_api(file):
    url = "http://127.0.0.1:8000/process-pdf/"
    files = {"file": (file.name, file.getvalue())}
    response = requests.post(url, files=files)
    return response.json()

def generate_questions_via_api(question, num_questions, difficulty_level, question_types):
    url = "http://127.0.0.1:8000/generate-questions/"
    data = {
        "question": question,
        "num_questions": num_questions,
        "difficulty_level": difficulty_level,
        "question_types": question_types
    }
    response = requests.post(url, data=data)
    return response.json()

def save_to_pdf_via_api(content, filename):
    url = "http://127.0.0.1:8000/save-to-pdf/"
    data = {"content": content, "filename": filename}
    response = requests.post(url, data=data)
    return response.json()

def main():
    st.set_page_config(page_title="Chat PDFs", page_icon="💬")
    
    # Session state
    if "history" not in st.session_state:
        st.session_state.history = []
    if "response" not in st.session_state:
        st.session_state.response = ""

    st.header("Exam Questions Generator🧾")
    st.caption("Hi, I will help you to prepare for your exam..☺")

    with st.sidebar:
        st.title("Menu:")
        doc_files = st.file_uploader(label="Upload your PDF files", accept_multiple_files=True)
        if st.button("Process"):
            if doc_files is not None:
                with st.spinner("Processing...."):
                    response = process_pdf_via_api(doc_files[0])
                    if "error" in response:
                        st.error(f"❌ {response['error']}")
                    else:
                        st.success("✅ Done.")
                    
    question = st.text_input("What do you want me to do?")
    num_questions = st.number_input("Choose the number of questions", min_value=10, max_value=100)
    difficulty_level = st.selectbox("Difficulty Level", options=["easy", "medium", "hard"])
    question_types = st.selectbox("Questions Type", options=["multiple choice", "true/false", "short answer", "essay"])

    generate = st.button("Generate")

    if generate:
          with st.spinner("Generating..."):
               response = generate_questions_via_api(
               question=question,
               num_questions=num_questions,
               difficulty_level=difficulty_level,
               question_types=question_types
               )
               if "error" in response:
                   st.error(f"❌ {response['error']}")
               else:
                   st.session_state.response = response.get("questions", "")

    if st.session_state.response:
          st.subheader("Generated Questions:")
          st.write(st.session_state.response)
          
          file_name = st.text_input("**Write the file name (with .pdf)**", value="questions.pdf")

          if st.button("Save To PDF"):
               if file_name:
                    response = save_to_pdf_via_api(st.session_state.response, file_name)
                    if "error" in response:
                        st.error(f"❌ {response['error']}")
                    else:
                        st.success("✅ PDF saved successfully!")
                        file_path = response.get("file_path")
                        with open(file_path, "rb") as pdf_file:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_file,
                                file_name=file_name,
                                mime="application/pdf"
                            )
               else:
                    st.warning("⚠️ Please write a file name.")

if __name__ == "__main__":
    main()



