import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.getenv("OPENAI_API_KEY")


st.set_page_config(page_title="AI Resume Critique", page_icon="📄", layout="centered")
st.title("📄 AI Resume Critique")
st.write("Upload your resume in PDF format, and I'll provide feedback to help you improve it.")

api_key = get_openai_api_key()
if not api_key:
    st.error("Missing OpenAI API key. Set OPENAI_API_KEY in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Extract text from PDF
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    resume_text = ""
    for page in pdf_reader.pages:
        resume_text += page.extract_text() or ""

    if not resume_text.strip():
        st.error("Could not extract text from this PDF. Make sure it's not a scanned image.")
    else:
        with st.expander("Extracted Resume Text", expanded=False):
            st.text(resume_text[:3000] + ("..." if len(resume_text) > 3000 else ""))

        if st.button("Critique My Resume", type="primary"):
            with st.spinner("Analyzing your resume..."):
                prompt = (
                    "You are an expert career coach and resume reviewer. "
                    "Analyze the following resume and provide detailed, constructive feedback covering:\n"
                    "1. **Overall Impression** – First impression and overall quality\n"
                    "2. **Content & Clarity** – Is the experience and skills clearly communicated?\n"
                    "3. **Formatting & Structure** – Is it well-organized and easy to read?\n"
                    "4. **Impact & Achievements** – Are accomplishments quantified and impactful?\n"
                    "5. **Keywords & ATS** – Is it optimized for applicant tracking systems?\n"
                    "6. **Specific Improvements** – List 3–5 concrete actions to improve it.\n\n"
                    f"Resume:\n{resume_text[:6000]}"
                )

                try:
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        stream=True,
                    )
                    st.subheader("Resume Critique")
                    with st.container():
                        output = st.empty()
                        full_response = ""
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content or ""
                            full_response += delta
                            output.markdown(full_response)
                except Exception as e:
                    st.error(f"OpenAI error: {e}")
else:
    st.info("👆 Upload a PDF to get started.")
