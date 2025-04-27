from PyPDF2 import PdfReader
from fpdf import FPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv(override=True)
import os






# gemini api key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# configure the genai 
genai.configure(api_key=GEMINI_API_KEY)



def get_pdf_text(pdf_docs):
    """
    Extracts text content from a list of PDF files.

    Args:
        pdf_docs (list): List of uploaded PDF files.

    Returns:
        str: Combined extracted text from all pages of the PDF documents.
    """
    text = ""
    # Handle single file upload
    if not isinstance(pdf_docs, list):
        pdf_docs = [pdf_docs]
        
    for pdf in pdf_docs:
        if pdf is not None:
            doc_pdf = PdfReader(pdf)
            for page in doc_pdf.pages:
                text += page.extract_text()
    return text


def get_text_chunks(text):
    """
    Splits large text into smaller, overlapping chunks for processing.

    Args:
        text (str): The full text to be split.

    Returns:
        list: A list of text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text=text)
    return chunks


embedding_model = None
def get_vector_store(text_chunks):
    """
    Creates and saves a FAISS vector store from the provided text chunks using Google's embedding model.

    Args:
        text_chunks (list): List of text chunks to embed and store.

    Returns:
        None
    """
    global embedding_model
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )
    vectore_store = FAISS.from_texts(text_chunks, embedding_model)
    vectore_store.save_local(folder_path="faiss-index")






# Define the function to take user query and return results
def user_query(question, num_questions, difficulty_level, question_types, include_answers):
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001",
                                                   google_api_key=GEMINI_API_KEY)
    
    # Load FAISS index from local storage
    new_db = FAISS.load_local(folder_path="faiss-index",
                              embeddings=embedding_model,
                              allow_dangerous_deserialization=True)
    
    # Perform similarity search to get relevant documents
    docs = new_db.similarity_search(query=question, k=10)
    
    # Prepare the input for the chain
    chain_input = {
        "input_documents": docs,
        "input": question,
        "num_questions": num_questions,
        "difficulty_level": difficulty_level,
        "question_types": question_types,
        "include_answers": include_answers
    }
    
    exam_prompt = """
                    You are a knowledgeable and professional AI assistant that specializes in generating high-quality exam questions.

                    Your role is to:

                    1. Generate clear, accurate, and well-structured exam questions based on the provided context and requirements.
                    2. Ensure that questions are relevant to the given subject, topic, and difficulty level.
                    3. Vary the question types if requested (e.g., multiple choice, true/false, short answer, essay).
                    4. Provide correct answers or model answers if specified.
                    5. Follow academic standards and avoid overly simplistic or overly complex wording unless specified.
                    6. If context is not enough to generate meaningful questions, acknowledge the limitation and ask for more detail.
                    7. Provide why the this answer is correct or incorrect if the question type is multiple choice or True/False. 

                    Remember:
                    - Do not make up unrelated information.
                    - Stick closely to the topic and subject area.
                    - Maintain clarity and educational value in all questions.
                    - Avoid repetition unless explicitly instructed.
                    - Ensure consistency with the question format and style.
                    - Do not put words in " " or ' '
                    - If the question type is multiple choice:
                    * "Place the choices **each on a new line** starting with a), b), c), d)"
                    * "Do not inline choices"
                    * "Keep formatting clean and professional"

                    Context:
                    {context}

                    Instructions:
                    - Number of Questions: {num_questions}
                    - Difficulty Level: {difficulty_level}
                    - Question Type(s): {question_types}
                    - Include Answers: {include_answers}

                    Now, generate the questions based on the above.
                    
                    """

    
    exam_prompt_template = PromptTemplate(
        input_variables=["context", "num_questions", "difficulty_level", "question_types", "include_answers"],
        template=exam_prompt
    )

    
    model = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY, model="gemini-2.0-flash")

   
    chain = load_qa_chain(llm=model, prompt=exam_prompt_template)

    
    response = chain(chain_input, return_only_outputs=True)
    
    response = response["output_text"] + " ? "
    return response




def save_text_to_pdf(text, filename):
    # Ensure the directory exists, create it if necessary
    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    pdf = FPDF()
    pdf.add_page()

    font_path = "fonts/DejaVuSans.ttf"

    if os.path.exists(font_path):  
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=14)
    else:
        pdf.set_font("Arial", size=12)  
        
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, txt=line)
        
    pdf.output(filename)
    return filename
