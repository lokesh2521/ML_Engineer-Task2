import streamlit as st
import PyPDF2
from docx import Document 
import requests
import os
from dotenv import load_dotenv 
import re

# Load Hugging Face API token from .env
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Function to call Hugging Face API for summarization
def summarize_text(text, max_length=150):
    payload = {"inputs": text, "parameters": {"max_length": max_length}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        try:
            return response.json()[0]['summary_text']
        except (KeyError, IndexError):
            return "Error: Could not parse summary response."
    else:
        return f"Error: {response.status_code} - {response.text}"

# Improved function to split long text into chunks
def chunk_text(text, max_len=2000):
    sentences = re.split(r'(?<=[.!?]) +', text)  # split at sentence boundaries
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_len:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# Extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Streamlit UI
st.title("📄 Document Summarizer (Hugging Face)")

uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])

if uploaded_file:
    file_type = uploaded_file.type
    if file_type == "application/pdf":
        doc_text = extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc_text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file type!")
        doc_text = None

    if doc_text:
        st.subheader("Original Text (Preview)")
        st.text_area("Text Preview", doc_text[:2000], height=300)

        if st.button("Summarize"):
            with st.spinner("Summarizing..."):
                chunks = chunk_text(doc_text, max_len=2000)  # split text into manageable chunks
                summary_chunks = []
                for i, chunk in enumerate(chunks):
                    st.info(f"Summarizing chunk {i+1}/{len(chunks)}...")
                    summary_chunks.append(summarize_text(chunk, max_length=200))
                final_summary = " ".join(summary_chunks)
            st.subheader("Summary")
            st.write(final_summary)
