import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
import requests
from dotenv import load_dotenv
from docx2pdf import convert  # Import docx2pdf for conversion
import pythoncom  # For COM initialization
from gtts import gTTS
from io import BytesIO
import base64
import pandas as pd

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("API Key not found! Please set it in a .env file.")
    st.stop()  # Stop execution if API key is missing

# Configure Google Generative AI with API Key
genai.configure(api_key=API_KEY)

# Extract text from PDF using pdfplumber
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""  # Handle cases where text might be None
    return text

# Chat with PDF content using Gemini model
def chat_with_pdf(pdf_text, user_query):
    prompt = f"""
    You are an AI mentor specializing in hackathons. Based on the following hackathon-related document:
    
    {pdf_text}
    
    Answer the user's question with relevant and structured insights.
    """
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Convert DOCX to PDF using docx2pdf
def convert_docx_to_pdf(docx_file):
    """Converts a .docx file to a .pdf file using docx2pdf and returns the PDF as a byte stream."""
    pythoncom.CoInitialize()  # Initialize COM
    output_pdf_path = "converted_output.pdf"
    
    with open("temp.docx", "wb") as temp_docx:
        temp_docx.write(docx_file.read())  # Save uploaded DOCX temporarily
    
    convert("temp.docx", output_pdf_path)
    
    with open(output_pdf_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()
    
    os.remove("temp.docx")  # Clean up temp DOCX file
    return pdf_data

# Convert Text to Speech
def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp

# Main Streamlit App
def main():
    st.sidebar.title("🏆 Hackathon AI Mentor & File Assistant 👾")
    
    # PDF File Upload
    pdf_file = st.sidebar.file_uploader("Upload a Hackathon-related PDF", type="pdf")
    
    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        st.subheader("Extracted Hackathon Document Text:")
        st.text_area("Extracted Text", pdf_text[:1500], height=200)
    
        user_query = st.text_input("Ask about the hackathon document:")
        if user_query:
            response = chat_with_pdf(pdf_text, user_query)
            st.write(f"🤖 AI Mentor's Response: {response}")
    
    # DOCX to PDF Upload
    docx_file = st.sidebar.file_uploader("Upload a DOCX file for Hackathon Docs", type="docx")
    if docx_file:
        pdf_data = convert_docx_to_pdf(docx_file)
        st.write("✅ Converted Hackathon PDF is ready to download:")
        st.download_button("📥 Download PDF", pdf_data, "converted_output.pdf", "application/pdf")
    
    # Web3 Integration Section
    st.sidebar.subheader("🌐 Web3 Integration")
    st.sidebar.write("Connect your Ethereum wallet to explore blockchain features tailored for hackathons.")
    st.sidebar.write("⚠ Connecting your wallet allows the app to view your account address and balance. No transactions will be made without your explicit consent.")
    
    # Embed JavaScript for Web3 wallet connection
    st.components.v1.html("""
        <script src="https://cdn.jsdelivr.net/npm/web3@1.5.2/dist/web3.min.js"></script>
        <script>
        async function connectWallet() {
            if (typeof window.ethereum !== 'undefined') {
                try {
                    // Request account access
                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    const account = accounts[0];
                    document.getElementById('account').innerText = 'Account: ' + account;
                    
                    // Get balance
                    const web3 = new Web3(window.ethereum);
                    const balance = await web3.eth.getBalance(account);
                    const etherBalance = web3.utils.fromWei(balance, 'ether');
                    document.getElementById('balance').innerText = 'Balance: ' + etherBalance + ' ETH';
                } catch (error) {
                    console.error(error);
                    document.getElementById('account').innerText = 'Error connecting to wallet';
                }
            } else {
                document.getElementById('account').innerText = 'MetaMask not installed';
            }
        }
        </script>
        <button onclick="connectWallet()">Connect Wallet</button>
        <div id="account"></div>
        <div id="balance"></div>
    """, height=200)
    
    # Hackathon AI Chatbot
    st.header("🚀 Hackathon Chatbot")
    user_input = st.text_input("Ask me anything about hackathons! 💬")
    if user_input:
        prompt = f"""
        You are an expert in hackathons. Provide guidance on:
        - How to prepare for hackathons.
        - Best tech stacks and tools.
        - Team formation strategies.
        - Pitching and presentation tips.
        - Judging criteria and winning strategies.
        
        *User Query:* {user_input}
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.write(response.text)
    
        # Convert Response to Speech
        if st.button("🔊 Listen to Response"):
            speech_fp = text_to_speech(response.text, lang="en")
            st.audio(speech_fp, format="audio/mpeg", start_time=0)
    
            b64 = base64.b64encode(speech_fp.getvalue()).decode()
            st.markdown(f'<a href="data:audio/mpeg;base64,{b64}" download="hackathon_tips.mp3">📥 Download Audio</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
