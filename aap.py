import streamlit as st
import pandas as pd
import google.generativeai as genai
from utils import extract_text, clean_text, rank_resumes_with_gemini

# --- Page Config ---
st.set_page_config(page_title="ATS Ranker v1.0", page_icon="🏆", layout="wide")

st.title("🏆 AI ATS Ranker v1.0")
st.markdown("Upload multiple resumes (1-5) and a Job Description to get a ranked leaderboard.")

# --- Inputs ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1️⃣ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("2️⃣ Upload Resumes")
    uploaded_files = st.file_uploader(
        "Select 1-5 PDF/DOCX files", 
        type=["pdf", "docx"], 
        accept_multiple_files=True
    )

with col2:
    st.subheader("3️⃣ Job Description")
    jd_text = st.text_area("Paste the JD here:", height=300)

# --- Logic ---
analyze_btn = st.button("🚀 Rank Candidates", type="primary", use_container_width=True)

if analyze_btn:
    # 1. Validation
    if not api_key:
        st.error("⚠️ Please enter your API Key.")
        st.stop()
    if not jd_text or len(jd_text) < 50:
        st.error("⚠️ Please paste a valid Job Description.")
        st.stop()
    if not uploaded_files:
        st.error("⚠️ Please upload at least one resume.")
        st.stop()
    if len(uploaded_files) > 5:
        st.error("⚠️ Limit is 5 resumes for this version.")
        st.stop()

    # 2. Configure Gemini
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
    except Exception as e:
        st.error(f"API Configuration Error: {e}")
        st.stop()

    # 3. Process Files
    resumes_content = {}
    progress_bar = st.progress(0, text="Reading files...")
    
    for i, file in enumerate(uploaded_files):
        text = extract_text(file)
        if text and not text.startswith("Error"):
            resumes_content[file.name] = clean_text(text)
        progress_bar.progress((i + 1) / len(uploaded_files), text=f"Reading {file.name}...")
    
    if not resumes_content:
        st.error("Could not extract text from any of the uploaded files.")
        st.stop()

    # 4. AI Ranking
    with st.spinner("🤖 AI is comparing candidates against JD..."):
        ranked_data = rank_resumes_with_gemini(resumes_content, jd_text, model)
        progress_bar.empty()

    # 5. Display Leaderboard
    if isinstance(ranked_data, list) and "filename" in ranked_data[0]:
        st.balloons()
        st.subheader("🥇 Candidate Leaderboard")
        
        # Convert to Pandas DataFrame for a nice table
        df = pd.DataFrame(ranked_data)
        
        # Reorder columns for better display
        cols = ["rank", "match_percentage", "candidate_name", "filename", "skills_match", "missing_skills", "reason"]
        # Filter to ensure columns exist before selecting
        existing_cols = [c for c in cols if c in df.columns]
        df = df[existing_cols]
        
        # Display as an interactive table
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "rank": "Rank",
                "match_percentage": st.column_config.ProgressColumn(
                    "Match %", min_value=0, max_value=100, format="%d%%"
                ),
                "candidate_name": "Name",
                "filename": "File",
                "reason": "AI Analysis"
            },
            use_container_width=True
        )
        
        # Detailed Breakdown
        st.markdown("---")
        st.subheader("📋 Detailed Analysis")
        for candidate in ranked_data:
            with st.expander(f"#{candidate.get('rank', '?')} - {candidate.get('candidate_name', 'Unknown')} ({candidate.get('match_percentage', 0)}%)"):
                st.write(f"**Why:** {candidate.get('reason')}")
                st.write(f"**✅ Skills:** {candidate.get('skills_match')}")
                st.write(f"**❌ Missing:** {candidate.get('missing_skills')}")
                
    else:
        st.error("AI failed to return a valid ranking. Please try again.")
