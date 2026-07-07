# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
import pandas as pd
import numpy as np
import os
import database
import skills
from orchestrator import MultiAgentOrchestrator

DB_PATH = "state.db"

# Page styling
st.set_page_config(
    page_title="Runtime Terrors Companion",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS injection
st.markdown("""
<style>
    /* Import Inter and Outfit Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;600&display=swap');

    /* Main typography & background overrides */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        background-color: #FAF6F0 !important;
        color: #0F172A !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F0E6D2 !important;
        border-right: 1px solid rgba(15, 23, 42, 0.08) !important;
    }

    /* Custom premium card styling */
    .custom-card {
        background: #FFFFFF;
        border: 1px solid rgba(37, 99, 235, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(15, 23, 42, 0.02);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }

    .custom-card:hover {
        transform: translateY(-2px);
        border-color: rgba(37, 99, 235, 0.3);
        box-shadow: 0 10px 40px rgba(37, 99, 235, 0.06);
    }

    .card-title {
        font-family: 'Outfit', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }

    .card-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }

    .card-subtitle {
        font-size: 0.75rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Premium Gradient Headers */
    h1 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        background: linear-gradient(135deg, #0F172A 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }

    h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: #0F172A !important;
        margin-top: 1.5rem !important;
    }

    /* Tab overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        color: #64748B;
        padding: 12px 16px;
        background-color: transparent;
        border: none;
        transition: all 0.3s;
    }

    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
database.init_db(DB_PATH)
orchestrator = MultiAgentOrchestrator(DB_PATH)

st.title("Runtime Terrors Companion")
st.markdown("<p style='color: #475569; font-size: 1.1rem; margin-top: -10px;'>Multi-Agent AI Study & Athletic Performance Companion</p>", unsafe_allow_html=True)
st.markdown("---")

# ----------------- SIDEBAR: USER SELECTION & REGISTRATION -----------------
st.sidebar.header("User State Registry")

# Add a default demo user if empty
with database.get_connection(DB_PATH) as conn:
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        database.add_user(DB_PATH, "Dawn Andrei Pamesa", "Student-Athlete", "Junior BS Data Science (FEU Tech)")

# Fetch users
users_list = []
with database.get_connection(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role, academic_level FROM users")
    users_list = [dict(row) for row in cursor.fetchall()]

user_options = {f"{u['name']} ({u['role']})": u['id'] for u in users_list}
selected_user_label = st.sidebar.selectbox("Active Profile", list(user_options.keys()))
active_user_id = user_options[selected_user_label]

st.sidebar.markdown("---")
st.sidebar.subheader("Register New Student-Athlete")
new_name = st.sidebar.text_input("Full Name")
new_role = st.sidebar.selectbox("Role", ["Student-Athlete", "Coach/Instructor", "Performer"])
new_academics = st.sidebar.text_input("Academic Major / Level", value="BS Data Science")

if st.sidebar.button("Register Profile"):
    if new_name.strip():
        new_id = database.add_user(DB_PATH, new_name, new_role, new_academics)
        st.sidebar.success(f"Registered {new_name} (ID: {new_id})!")
        st.rerun()

# ----------------- MAIN INTERFACE -----------------
user_profile = database.get_user(DB_PATH, active_user_id)

if user_profile:
    # 5-Tab Layout incorporating Sophy and the ML Lab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard & Data Hub", 
        "Academic Tutor Agent", 
        "Performance Coach Agent", 
        "Sophy Spaced Repetition (SRS)", 
        "Data Science ML Sandbox"
    ])
    
    # ----------------- TAB 1: DASHBOARD & STATE DATA -----------------
    with tab1:
        st.header("Profile Status & Analytics")
        
        # Load latest metrics for calculation
        with database.get_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Fetch latest recovery score
            cursor.execute("SELECT recovery_score FROM athletic_metrics WHERE user_id = ? ORDER BY id DESC LIMIT 1", (active_user_id,))
            latest_rec_row = cursor.fetchone()
            latest_recovery = latest_rec_row[0] if latest_rec_row else 100.0
            
            # Counts
            study_sessions_count = conn.execute("SELECT COUNT(*) FROM academic_milestones WHERE user_id = ?", (active_user_id,)).fetchone()[0]
            workouts_count = conn.execute("SELECT COUNT(*) FROM athletic_metrics WHERE user_id = ?", (active_user_id,)).fetchone()[0]

        # Premium metric card rendering
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"""
            <div class="custom-card">
                <div class="card-title">Academic Mastery</div>
                <div class="card-value">{user_profile['mastery_score']}%</div>
                <div class="card-subtitle">Based on milestones</div>
            </div>
        """, unsafe_allow_html=True)
        col2.markdown(f"""
            <div class="custom-card">
                <div class="card-title">Recovery Index</div>
                <div class="card-value">{latest_recovery} <span style="font-size: 1rem; color:#64748B;">/100</span></div>
                <div class="card-subtitle">Latest training score</div>
            </div>
        """, unsafe_allow_html=True)
        col3.markdown(f"""
            <div class="custom-card">
                <div class="card-title">Study Sessions</div>
                <div class="card-value">{study_sessions_count}</div>
                <div class="card-subtitle">Milestones recorded</div>
            </div>
        """, unsafe_allow_html=True)
        col4.markdown(f"""
            <div class="custom-card">
                <div class="card-title">Workouts Logged</div>
                <div class="card-value">{workouts_count}</div>
                <div class="card-subtitle">Training records</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Skill Integration: Markdown Study Parser
        st.subheader("Skill Integration: Study Note Markdown Parser")
        st.markdown("<p style='color:#475569;'>Paste markdown notes here to automatically extract academic subjects, topics, and performance grades.</p>", unsafe_allow_html=True)
        
        default_md = (
            "- Subject: Machine Learning\n"
            "- Topic: Support Vector Machines\n"
            "- Status: Mastered\n"
            "- Grade: 94.5\n"
        )
        md_content = st.text_area("Markdown Notes Content", value=default_md, height=120)
        if st.button("Parse & Update Milestones"):
            milestones = skills.parse_study_markdown(md_content)
            if milestones:
                for m in milestones:
                    database.add_academic_milestone(DB_PATH, active_user_id, m["subject"], m["topic"], m["status"], m["grade"])
                st.success(f"Successfully parsed and loaded {len(milestones)} milestones to SQLite state database!")
                st.rerun()
            else:
                st.warning("No valid milestones parsed. Please ensure the formatting matches '- Subject: <name>' and '- Topic: <name>'.")
                
        st.markdown("---")
        
        # Render SQLite tables
        st.subheader("Academic Milestones Table (SQLite)")
        with database.get_connection(DB_PATH) as conn:
            academic_df = pd.read_sql_query("SELECT subject, topic, status, grade, recorded_date FROM academic_milestones WHERE user_id = ?", conn, params=(active_user_id,))
        if not academic_df.empty:
            st.dataframe(academic_df, use_container_width=True)
        else:
            st.info("No study sessions logged yet.")
            
        st.subheader("Athletic Metrics Table (SQLite)")
        with database.get_connection(DB_PATH) as conn:
            athletic_df = pd.read_sql_query("SELECT session_type, duration_minutes, intensity_rpe, recovery_score, recorded_date FROM athletic_metrics WHERE user_id = ?", conn, params=(active_user_id,))
        if not athletic_df.empty:
            st.dataframe(athletic_df, use_container_width=True)
        else:
            st.info("No athletic training logs found.")

    # ----------------- TAB 2: ACADEMIC TUTOR AGENT -----------------
    with tab2:
        st.header("The Academic Tutor Agent")
        st.markdown("Explains data science concepts and establishes learning pipelines.")
        
        sub_col1, sub_col2 = st.columns(2)
        subject_input = sub_col1.text_input("Subject Area", value="Machine Learning")
        topic_input = sub_col2.text_input("Topic Details", value="Loss Functions & Optimization")
        academic_query = st.text_area("Question / Explanatory Query", value="Explain the differences between Cross-Entropy and MSE loss functions.")
        
        if st.button("Submit to Academic Tutor"):
            with st.spinner("Tutor Agent executing learning pipeline..."):
                resp = orchestrator.run_academic_tutor(active_user_id, subject_input, topic_input, academic_query)
                st.markdown("### Tutor Response:")
                st.markdown(f"<div class='custom-card' style='background: #FFFDF9; border-left: 4px solid #2563eb;'>{resp}</div>", unsafe_allow_html=True)
                
        # Show recent conversations
        st.markdown("---")
        st.subheader("Tutor Dialogue History")
        history = database.get_conversation_history(DB_PATH, active_user_id)
        tutor_history = [h for h in history if h["agent_role"] == "Academic Tutor"]
        for msg in tutor_history:
            role_label = "Student" if msg["message_role"] == "user" else "Tutor"
            border = "border-left: 4px solid #64748B;" if role_label == "Student" else "border-left: 4px solid #2563eb; background: #FFFDF9;"
            st.markdown(f"<div class='custom-card' style='padding:12px; margin-bottom:10px; {border}'><strong>{role_label}:</strong> {msg['message_content']}</div>", unsafe_allow_html=True)

    # ----------------- TAB 3: PERFORMANCE COACH AGENT -----------------
    with tab3:
        st.header("The Performance Coach Agent")
        st.markdown("Evaluates physical recovery indexing and balances scheduling loads.")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        session_input = c_col1.text_input("Training Activity Type", value="Taekwondo Sparring")
        duration_input = c_col2.number_input("Duration (minutes)", min_value=5, max_value=300, value=60)
        rpe_input = c_col3.slider("Intensity (RPE 1-10)", 1, 10, value=7)
        
        coach_query = st.text_area("Coaching Query", value="Can I study neural networks for 3 hours after this workout?")
        
        if st.button("Submit to Performance Coach"):
            with st.spinner("Coach Agent calculating recovery stats..."):
                resp = orchestrator.run_performance_coach(active_user_id, session_input, duration_input, rpe_input, coach_query)
                st.markdown("### Coach Response:")
                st.markdown(f"<div class='custom-card' style='background: #FFFDF9; border-left: 4px solid #2563eb;'>{resp}</div>", unsafe_allow_html=True)
                
        # Show recent conversations
        st.markdown("---")
        st.subheader("Coach Dialogue History")
        history = database.get_conversation_history(DB_PATH, active_user_id)
        coach_history = [h for h in history if h["agent_role"] == "Performance Coach"]
        for msg in coach_history:
            role_label = "Athlete" if msg["message_role"] == "user" else "Coach"
            border = "border-left: 4px solid #64748B;" if role_label == "Athlete" else "border-left: 4px solid #2563eb; background: #FFFDF9;"
            st.markdown(f"<div class='custom-card' style='padding:12px; margin-bottom:10px; {border}'><strong>{role_label}:</strong> {msg['message_content']}</div>", unsafe_allow_html=True)

    # ----------------- TAB 4: SOPHY SPACED REPETITION (SRS) -----------------
    with tab4:
        st.header("Sophy: Spaced Repetition Study Engine")
        st.markdown("Generates culturally aware, multilingual flashcards in Tagalog or Taglish and handles scheduling intervals via the SM-2 algorithm.")
        
        gen_col1, gen_col2 = st.columns(2)
        sophy_subject = gen_col1.text_input("Flashcard Subject", value="Data Science Basics")
        sophy_topic = gen_col2.text_input("Flashcard Topic", value="Cross Validation")
        sophy_lang = st.selectbox("Tutor Language Mode", ["Taglish", "Tagalog", "English"])
        
        if st.button("Generate & Verify Flashcards"):
            with st.spinner("Sophy Dual-API generating flashcards..."):
                cards = orchestrator.generate_study_flashcards(active_user_id, sophy_subject, sophy_topic, count=3, language=sophy_lang)
                st.success(f"Generated and verified {len(cards)} flashcards!")
                for c in cards:
                    st.markdown(f"<div class='custom-card'><strong>Q:</strong> {c['question']}<br><strong>A:</strong> {c['answer']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("Generate Flashcards from Subject Modules (PDF / PPTX)")
        st.markdown("<p style='color:#475569;'>Upload your lecture slides or syllabus modules to automatically extract content and create custom review cards.</p>", unsafe_allow_html=True)
        
        uploaded_doc = st.file_uploader("Upload Lecture Module (PDF or PPTX)", type=["pdf", "pptx"])
        doc_subject = st.text_input("Module Subject", value="Machine Learning", key="doc_sub")
        doc_topic = st.text_input("Module Topic", value="Gradient Descent", key="doc_top")
        doc_lang = st.selectbox("Tutor Language Mode", ["Taglish", "Tagalog", "English"], key="doc_lang")
        doc_count = st.slider("Flashcard Count", 1, 10, value=3)
        
        if st.button("Generate Cards from Document"):
            if uploaded_doc is not None:
                # Save locally temporarily to parse
                temp_filename = f"temp_{uploaded_doc.name}"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_doc.getbuffer())
                
                with st.spinner("Extracting text and running OCR if scanned..."):
                    if uploaded_doc.name.endswith(".pdf"):
                        extracted_text = skills.extract_text_from_pdf(temp_filename)
                    else:
                        extracted_text = skills.extract_text_from_pptx(temp_filename)
                
                # Cleanup temp file
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    
                if extracted_text.strip():
                    st.info(f"Extracted {len(extracted_text)} characters from document. Running Sophy cognitive generation...")
                    with st.spinner("Sophy generating flashcards..."):
                        cards = orchestrator.generate_flashcards_from_text(
                            active_user_id, doc_subject, doc_topic, extracted_text, count=doc_count, language=doc_lang
                        )
                        st.success(f"Successfully generated {len(cards)} flashcards from uploaded document!")
                        for c in cards:
                            st.markdown(f"<div class='custom-card'><strong>Q:</strong> {c['question']}<br><strong>A:</strong> {c['answer']}</div>", unsafe_allow_html=True)
                else:
                    st.error("No text could be extracted from the uploaded document. Please check the file formatting.")
            else:
                st.error("Please upload a PDF or PPTX file first.")
        
        st.markdown("---")
        st.subheader("Review Due Flashcards")
        
        due_cards = database.get_due_flashcards(DB_PATH, active_user_id)
        if due_cards:
            st.warning(f"You have {len(due_cards)} flashcards due for review!")
            card = due_cards[0]
            
            st.markdown(f"<div class='custom-card' style='background: #FFFDF9; border-top: 4px solid #2563eb; padding:30px;'><h3 style='margin:0 0 10px 0;'>Question:</h3><p style='font-size:1.2rem;'>{card['question']}</p></div>", unsafe_allow_html=True)
            
            if "show_answer" not in st.session_state:
                st.session_state.show_answer = False
                
            if st.button("Show Answer"):
                st.session_state.show_answer = True
                
            if st.session_state.show_answer:
                st.markdown(f"<div class='custom-card' style='border-top: 4px solid #10b981; padding:30px;'><h3 style='margin:0 0 10px 0;'>Answer:</h3><p style='font-size:1.2rem;'>{card['answer']}</p></div>", unsafe_allow_html=True)
                
                st.write("Rate your recall quality (0 = Total Blackout, 5 = Perfect):")
                q_cols = st.columns(6)
                for q in range(6):
                    if q_cols[q].button(str(q), key=f"rate_{card['id']}_{q}"):
                        new_ef, new_interval, next_date, new_streak = skills.calculate_sm2_review(
                            card["ease_factor"], card["interval_days"], card["consecutive_correct"], q
                        )
                        database.update_flashcard_review(DB_PATH, card["id"], new_ef, new_interval, next_date, new_streak)
                        st.success(f"Card rated {q}! Next review scheduled on {next_date}.")
                        st.session_state.show_answer = False
                        st.rerun()
        else:
            st.success("🎉 All caught up! No due flashcards to review.")

    # ----------------- TAB 5: DATA SCIENCE ML SANDBOX -----------------
    with tab5:
        st.header("Data Science ML Laboratory")
        st.markdown("Runs a leakage-free 5-Phase Machine Learning Pipeline directly on uploaded tabular datasets using tree-based models.")
        
        uploaded_file = st.file_uploader("Upload CSV Dataset", type=["csv"])
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            np.random.seed(42)
            n_samples = 200
            sample_data = {
                'Study_Hours_Per_Week': np.random.normal(15, 5, n_samples).clip(2, 40),
                'Sleep_Hours_Per_Night': np.random.normal(7, 1.2, n_samples).clip(4, 10),
                'Workout_Duration_Mins': np.random.normal(60, 20, n_samples).clip(10, 180),
                'Workout_Intensity_RPE': np.random.randint(3, 10, n_samples),
                'Role': np.random.choice(['Athlete', 'Performer', 'Coach'], n_samples),
                'Academic_Level': np.random.choice(['Junior', 'Senior', 'Sophomore'], n_samples),
                'Burnout_Target': np.random.choice([0, 1], n_samples, p=[0.75, 0.25])
            }
            df = pd.DataFrame(sample_data)
            st.info("Showing mock Student-Athlete performance dataset. Upload a CSV to use your own data.")
            
        st.subheader("Data Overview (First 5 Rows)")
        st.dataframe(df.head(), use_container_width=True)
        
        all_cols = list(df.columns)
        target_col = st.selectbox("Select Target Variable (Y)", all_cols, index=len(all_cols)-1)
        
        remaining_cols = [c for c in all_cols if c != target_col]
        num_cols = st.multiselect("Select Numerical Features", remaining_cols, default=[c for c in remaining_cols if df[c].dtype != 'object'])
        cat_cols = st.multiselect("Select Categorical Features", remaining_cols, default=[c for c in remaining_cols if df[c].dtype == 'object'])
        
        if st.button("Run Complete ML Pipeline (Phases 1-5)"):
            if not num_cols and not cat_cols:
                st.error("Please select at least one feature.")
            else:
                st.subheader("Phase 1: Exploratory Data Analysis & Diagnostics")
                integrity_df = skills.inspect_data_integrity(df)
                st.dataframe(integrity_df, use_container_width=True)
                
                X = df[num_cols + cat_cols]
                y = df[target_col]
                
                if y.dtype == 'object':
                    y = pd.Series(pd.factorize(y)[0])
                    
                preprocessor = skills.build_preprocessing_pipeline(num_cols, cat_cols)
                
                st.subheader("Phases 2-4: Leakage-Free Preprocessing & Stratified K-Fold CV")
                models = skills.get_baseline_models()
                
                cv_results = {}
                with st.spinner("Running cross-validation loops..."):
                    for model_name, model in models.items():
                        try:
                            scores = skills.evaluate_pipeline_cv(model, preprocessor, X, y)
                            cv_results[model_name] = scores
                        except Exception as e:
                            st.warning(f"Failed to evaluate {model_name}: {str(e)}")
                            
                if cv_results:
                    cv_df = pd.DataFrame(cv_results).T
                    st.dataframe(cv_df, use_container_width=True)
                    
                st.subheader("Phase 5: Evaluation Metrics & Interpretation Dictionary")
                
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                best_model = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=6, random_state=42, eval_metric='logloss')
                model_pipeline = Pipeline(steps=[
                    ('preprocessor', preprocessor),
                    ('model', best_model)
                ])
                
                with st.spinner("Fitting final production pipeline model..."):
                    model_pipeline.fit(X_train, y_train)
                    
                output_report, importance_df = skills.display_final_metrics(model_pipeline, X_test, y_test, preprocessor)
                
                col_m1, col_m2 = st.columns([1, 1])
                col_m1.text(output_report)
                
                col_m2.markdown("#### Feature Importance Profile")
                col_m2.dataframe(importance_df, use_container_width=True)
                
                st.success("Production ML Pipeline run successfully!")
else:
    st.error("No active user profile selected. Please register a profile first.")
