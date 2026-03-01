import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics import accuracy_score
import joblib
from collections import defaultdict
import psycopg2
from psycopg2 import Error
import bcrypt


# --- DATABASE CONFIG ---
DB_CONFIG = {
    'host': st.secrets["db.jeyypqpiqgcgfzfmxcus.supabase.co"],
    'dbname': st.secrets["postgres"],
    'user': st.secrets["db_user"],
    'password': st.secrets["DATABASE_supabase"],
    'port': st.secrets["5432"]
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Database connection failed: {e}")
        return None
# Import styling from separate file
from styles import load_css, get_colors

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Career Pathfinder", 
    layout="wide",
    initial_sidebar_state="expanded"
)


# Apply CSS styling
st.markdown(load_css(), unsafe_allow_html=True)

# Get colors for use in the app
colors = get_colors()
PRIMARY_COLOR = colors['primary']
BACKGROUND_COLOR = colors['background']
SECONDARY_BG = colors['secondary_bg']
TEXT_COLOR = colors['text']
ACCENT_COLOR_1 = colors['accent1']
ACCENT_COLOR_2 = colors['accent2']
ACCENT_COLOR_3 = colors['accent3']

# from career_radar import show_career_radar
# show_career_radar(colors)  

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "ml_models" not in st.session_state:
    st.session_state.ml_models = {}
if "ml_accuracy" not in st.session_state:
    st.session_state.ml_accuracy = {}
if "quiz_responses" not in st.session_state:
    st.session_state.quiz_responses = {}
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False

# --- FILE PATHS ---
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "datasets")

# File paths
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
CAREERS_FILE = os.path.join(DATA_DIR, "careers.csv")
COLLEGES_FILE = os.path.join(DATA_DIR, "colleges.csv")
MARKET_FILE = os.path.join(DATA_DIR, "market_demand.csv")
QUIZ_FILE = os.path.join(DATA_DIR, "psychometric_questions.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "user_career_history.csv")
FEEDBACK_FILE = os.path.join(DATA_DIR, "user_feedback.csv")
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

# Create ML models directory
os.makedirs(ML_MODELS_DIR, exist_ok=True)

# --- INTEREST CATEGORIZATION ---
TECHNICAL_INTERESTS = ["Coding", "Physics", "Data Handling", "Biology", "Psychology", 
                       "Business", "Finance", "Law", "Engineering", "Medicine", 
                       "Research", "Analytics", "Technology", "Science", "Mathematics",
                       "Economics", "Statistics", "Chemistry", "Computer Science",
                       "Taxation", "Auditing", "Compliance", "Corporate Governance",
                       "Aviation", "Space Technology", "Nutrition", "Child Development",
                       "Architecture", "Environmental Science", "Food Science"]

CREATIVE_INTERESTS = ["Arts", "Archaeology", "Design", "Photography", "Architecture", 
                      "Sports", "Culinary", "Music", "Dance", "Theater", "Film", 
                      "Fashion", "Writing", "Creative Arts", "Painting", "Sculpture",
                      "Graphic Design", "Interior Design", "Performing Arts", "Textile Design",
                      "Literature", "Media", "Creative Writing", "Journalism"]

# --- QUIZ SCORING FUNCTION ---
def calculate_quiz_score(answer, options):
    """
    Convert Likert scale answers to scores:
    Strongly Agree = 4
    Agree = 3  
    Disagree = 2
    Strongly Disagree = 1
    """
    if answer not in options:
        return 0
    
    # Find index of answer in options
    try:
        answer_index = options.index(answer)
        # Calculate score based on position (A=4, B=3, C=2, D=1)
        if answer_index == 0:  # Option A
            return 4
        elif answer_index == 1:  # Option B
            return 3
        elif answer_index == 2:  # Option C
            return 2
        elif answer_index == 3:  # Option D
            return 1
    except:
        return 0
    return 0

# --- FEEDBACK STORAGE ---
def save_feedback(username, feedback, recommendation):
    """Save user feedback to CSV file"""
    try:
        # Create feedback file if it doesn't exist
        if not os.path.exists(FEEDBACK_FILE):
            pd.DataFrame(columns=[
                'user_id', 'feedback', 'recommendation', 'timestamp'
            ]).to_csv(FEEDBACK_FILE, index=False)
        
        # Load existing feedback
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        
        # Create new feedback record
        new_feedback = {
            'user_id': username,
            'feedback': feedback,
            'recommendation': recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Append new feedback
        feedback_df = pd.concat([feedback_df, pd.DataFrame([new_feedback])], ignore_index=True)
        feedback_df.to_csv(FEEDBACK_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False

# --- LOGIN / SIGNUP SYSTEM ---
def login_system():
    st.sidebar.header("🔐 Login / Signup")
    mode = st.sidebar.radio("Select Mode", ["Login", "Signup"], horizontal=True)
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button(f"{mode}", use_container_width=True):
        if not username or not password:
            st.sidebar.error("Please enter both username and password")
            return

        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()

        try:
            if mode == "Signup":
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    st.sidebar.error("Username already exists")
                else:
                    from datetime import datetime
                    hashed_pw = bcrypt.hashpw(
                        password.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    cursor.execute(
                        "INSERT INTO users (username, password, last_login) VALUES (%s, %s, %s)",
                        (username, hashed_pw, datetime.now())
                    )
                    conn.commit()
                    st.sidebar.success("Signup successful! Please login.")

            else:  # Login
                cursor.execute(
                    "SELECT username, password FROM users WHERE username = %s", 
                    (username,)
                )
                user = cursor.fetchone()
                if user and bcrypt.checkpw(
                    password.encode('utf-8'), 
                    user[1].encode('utf-8')
                ):
                    from datetime import datetime
                    cursor.execute(
                        "UPDATE users SET last_login = %s WHERE username = %s",
                        (datetime.now(), username)
                    )
                    conn.commit()
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.sidebar.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials")

        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            cursor.close()
            conn.close()
# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.quiz_responses = {}
    st.session_state.quiz_completed = False
    st.rerun()

# --- ML FUNCTIONS ---
def load_or_train_ml_models():
    nb_model_path = os.path.join(ML_MODELS_DIR, 'naive_bayes_model.pkl')
    lr_model_path = os.path.join(ML_MODELS_DIR, 'logistic_model.pkl')
    encoders_path = os.path.join(ML_MODELS_DIR, 'label_encoders.pkl')
    scaler_path = os.path.join(ML_MODELS_DIR, 'scaler.pkl')
    
    try:
        # Try to load existing models
        if (os.path.exists(nb_model_path) and os.path.exists(lr_model_path) and 
            os.path.exists(encoders_path) and os.path.exists(scaler_path)):
            
            nb_model = joblib.load(nb_model_path)
            lr_model = joblib.load(lr_model_path)
            label_encoders = joblib.load(encoders_path)
            scaler = joblib.load(scaler_path)
            
            st.session_state.ml_models = {
                'nb': nb_model,
                'lr': lr_model,
                'encoders': label_encoders,
                'scaler': scaler
            }
            
            # Load accuracy if available
            accuracy_file = os.path.join(ML_MODELS_DIR, 'model_accuracy.csv')
            if os.path.exists(accuracy_file):
                acc_df = pd.read_csv(accuracy_file)
                st.session_state.ml_accuracy = acc_df.set_index('model')['accuracy'].to_dict()
            
            return True
    except Exception as e:
        st.sidebar.warning(f"Could not load ML models: {str(e)[:50]}...")
        pass
    
    # Try to train models automatically
    if train_ml_models():
        return True
    
    return False

def train_ml_models():
    try:
        y=None
        conn = get_db_connection()
        if not conn:
          return False
        try:
          history_df = pd.read_sql("SELECT * FROM user_history", conn)
        finally:
          conn.close()

        if history_df.empty:
          st.sidebar.info("No user history found. ML models will train when users start using the system.")
          return False
        
        if len(history_df) < 30:
          st.sidebar.info(f"Collecting more user data for ML training ({len(history_df)}/30 samples)")
          return False
        
        # Clean data - remove rows with NaN in critical columns
        history_df = history_df.dropna(subset=['math_score', 'science_score', 'english_score',
                                              'economics_score', 'physical_education_score',
                                              'computers_score', 'social_studies_score',
                                              'primary_interest', 'career_stream'])
        
        if len(history_df) < 30:
            return False
        
               # Prepare features - ALL 7 subjects now
        X = history_df[['math_score', 'science_score', 'english_score', 'economics_score', 
                       'physical_education_score', 'computers_score', 'social_studies_score', 
                       'primary_interest', 'secondary_interest']].copy()
        y = history_df['career_stream']
        
        # Encode categorical features
        label_encoders = {}
        for col in ['primary_interest', 'secondary_interest']:
            le = LabelEncoder()
            # Handle missing values
            X[col] = X[col].fillna('None')
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le
        
        # Scale numerical features
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
        
        # Train Naive Bayes
        nb_model = MultinomialNB()
        nb_model.fit(X_train, y_train)
        nb_pred = nb_model.predict(X_test)
        nb_accuracy = accuracy_score(y_test, nb_pred)
        
        # Train Logistic Regression
        lr_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        lr_accuracy = accuracy_score(y_test, lr_pred)
        
        # Calculate ensemble accuracy
        ensemble_pred = []
        for i in range(len(X_test)):
            nb_prob = nb_model.predict_proba(X_test[i:i+1])[0]
            lr_prob = lr_model.predict_proba(X_test[i:i+1])[0]
            
            # Average probabilities
            avg_prob = (nb_prob + lr_prob) / 2
            ensemble_pred.append(nb_model.classes_[np.argmax(avg_prob)])
        
        ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
        
        # Save models
        joblib.dump(nb_model, os.path.join(ML_MODELS_DIR, 'naive_bayes_model.pkl'))
        joblib.dump(lr_model, os.path.join(ML_MODELS_DIR, 'logistic_model.pkl'))
        joblib.dump(label_encoders, os.path.join(ML_MODELS_DIR, 'label_encoders.pkl'))
        joblib.dump(scaler, os.path.join(ML_MODELS_DIR, 'scaler.pkl'))
        
        # Save accuracy
        acc_df = pd.DataFrame({
            'model': ['Naive Bayes', 'Logistic Regression', 'Ensemble'],
            'accuracy': [nb_accuracy, lr_accuracy, ensemble_accuracy]
        })
        acc_df.to_csv(os.path.join(ML_MODELS_DIR, 'model_accuracy.csv'), index=False)
        
        # Update session state
        st.session_state.ml_models = {
            'nb': nb_model,
            'lr': lr_model,
            'encoders': label_encoders,
            'scaler': scaler
        }
        st.session_state.ml_accuracy = {
            'Naive Bayes': nb_accuracy,
            'Logistic Regression': lr_accuracy,
            'Ensemble': ensemble_accuracy
        }
        print(f"✅ Model Accuracy - Naive Bayes: {nb_accuracy*100:.1f}%, Logistic: {lr_accuracy*100:.1f}%, Ensemble: {ensemble_accuracy*100:.1f}%")
        return True
        
    except Exception as e:
        st.error(f"Error training ML models: {e}")
        return False

def predict_with_ml(user_features, model_type='ensemble'):
    if not st.session_state.ml_models:
        return None
    
    try:
        # Prepare user features
        features_df = pd.DataFrame([user_features])
        
        # Encode categorical features
        encoders = st.session_state.ml_models['encoders']
        for col in ['primary_interest', 'secondary_interest']:
            if col in features_df.columns:
                # Handle unseen labels
                if user_features[col] in encoders[col].classes_:
                    features_df[col] = encoders[col].transform([user_features[col]])[0]
                else:
                    # Use most common label for unknown
                    features_df[col] = 0
        
        # Scale features
        scaler = st.session_state.ml_models['scaler']
        X_scaled = scaler.transform(features_df)
        
        # Get predictions
        nb_model = st.session_state.ml_models['nb']
        lr_model = st.session_state.ml_models['lr']
        
        if model_type == 'naive_bayes':
            nb_proba = nb_model.predict_proba(X_scaled)[0]
            return dict(zip(nb_model.classes_, nb_proba))
        
        elif model_type == 'logistic':
            lr_proba = lr_model.predict_proba(X_scaled)[0]
            return dict(zip(lr_model.classes_, lr_proba))
        
        else:  # ensemble - average both models
            nb_proba = nb_model.predict_proba(X_scaled)[0]
            lr_proba = lr_model.predict_proba(X_scaled)[0]
            
            # Average probabilities
            ensemble_proba = {}
            all_classes = set(nb_model.classes_) | set(lr_model.classes_)
            
            for cls in all_classes:
                nb_val = nb_proba[list(nb_model.classes_).index(cls)] if cls in nb_model.classes_ else 0
                lr_val = lr_proba[list(lr_model.classes_).index(cls)] if cls in lr_model.classes_ else 0
                ensemble_proba[cls] = (nb_val + lr_val) / 2
            
            return ensemble_proba
            
    except Exception as e:
        st.error(f"ML prediction error: {e}")
        return None

def save_user_data_for_training(username, grades, interests, quiz_scores, career_stream, user_rating=None):
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        from datetime import datetime
        cursor.execute("""
            INSERT INTO user_history (
                user_id, math_score, science_score, english_score,
                economics_score, physical_education_score, computers_score,
                social_studies_score, primary_interest, secondary_interest,
                career_stream, user_rating, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            grades['Math'],
            grades['Science'],
            grades['English'],
            grades['Economics'],
            grades['Physical Education'],
            grades['Computers'],
            grades['Social Studies'],
            interests['primary'],
            interests['secondary'] if interests['secondary'] != "None" else None,
            career_stream,
            user_rating if user_rating else None,
            datetime.now()
        ))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM user_history")
        count = cursor.fetchone()[0]
        if count % 25 == 0 and count >= 30:
            train_ml_models()

    except Error as e:
        st.error(f"Error saving to database: {e}")
    finally:
        cursor.close()
        conn.close()
# --- SHOW LOGIN PAGE OR WELCOME SCREEN ---
if not st.session_state.logged_in:
    # Clean homepage with your theme
    st.markdown("<h1 class='main-header'>🎓 Career Pathfinder</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-header'>Find Your Perfect Career Match</h3>", unsafe_allow_html=True)
    
    # Create centered content
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"""
        <div class='theme-card'>
            <h3 style='color: {PRIMARY_COLOR};'>Welcome to Career Pathfinder</h3>
            <p>This intelligent system helps you discover career paths that match your:</p>
            <ul>
                <li><b>Academic strengths</b> in Math, Science, English, Economics, Physical Education, and Computers</li>
                <li><b>Personal interests</b> and passions</li>
                <li><b>Personality traits</b> from psychometric assessment</li>
            </ul>
            <p>Get personalized recommendations, explore career options, and plan your future education path.</p>
            <hr>
            <p><i>Please login or signup from the sidebar to begin.</i></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("### Key Features:")
    features_col1, features_col2, features_col3 = st.columns(3)
    
    with features_col1:
        st.markdown(f"""
        <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; border-left: 4px solid {PRIMARY_COLOR};'>
            <h4>🎯 Personalized Recommendations</h4>
            <p>AI-powered career suggestions based on your unique profile</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features_col2:
        st.markdown(f"""
        <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; border-left: 4px solid {ACCENT_COLOR_1};'>
            <h4>📊 Detailed Analysis</h4>
            <p>Comprehensive breakdown of your strengths and matches</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features_col3:
        st.markdown(f"""
        <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; border-left: 4px solid {ACCENT_COLOR_2};'>
            <h4>🏫 College & Career Info</h4>
            <p>Information on top colleges and career opportunities</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show login/signup
    login_system()
    st.stop()

# --- LOAD DATASETS ---
try:
    careers_df = pd.read_csv(CAREERS_FILE, header=0)
    colleges_df = pd.read_csv(COLLEGES_FILE)
    market_df = pd.read_csv(MARKET_FILE)
    quiz_df = pd.read_csv(QUIZ_FILE, on_bad_lines='skip', encoding='utf-8')
except FileNotFoundError as e:
    st.error(f"Missing dataset: {e.filename}")
    st.stop()

# --- ML MODELS LOADING ---
ml_loaded = load_or_train_ml_models()
if not ml_loaded:
    st.sidebar.info("🤖 AI Mode: Training with user data...")
else:
    st.sidebar.success("✅ AI Mode: Active • 25+ career paths")

# --- SIDEBAR INPUTS ---
st.sidebar.header(f"Welcome, {st.session_state.username}")

# Logout button
if st.sidebar.button("Logout", use_container_width=True):
    logout()

st.sidebar.markdown("---")
st.sidebar.subheader("Enter Your Grades")

# Number inputs stacked vertically with subject names above
st.sidebar.markdown('<div class="subject-input-container">', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Math</label>', unsafe_allow_html=True)
math_score = st.sidebar.number_input("Math", min_value=0, max_value=100, value=50, step=1, key="math_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Science</label>', unsafe_allow_html=True)
science_score = st.sidebar.number_input("Science", min_value=0, max_value=100, value=50, step=1, key="science_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>English</label>', unsafe_allow_html=True)
english_score = st.sidebar.number_input("English", min_value=0, max_value=100, value=50, step=1, key="english_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Economics</label>', unsafe_allow_html=True)
economics_score = st.sidebar.number_input("Economics", min_value=0, max_value=100, value=50, step=1, key="economics_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Physical Education</label>', unsafe_allow_html=True)
physical_education_score = st.sidebar.number_input("Physical Education", min_value=0, max_value=100, value=50, step=1, key="pe_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Computers</label>', unsafe_allow_html=True)
computers_score = st.sidebar.number_input("Computers", min_value=0, max_value=100, value=50, step=1, key="computers_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="subject-item"><label>Social Studies</label>', unsafe_allow_html=True)
social_studies_score = st.sidebar.number_input("Social Studies", min_value=0, max_value=100, value=50, step=1, key="social_studies_input", label_visibility="collapsed")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Keep your grades dictionary
grades = {
    "Math": math_score,
    "Science": science_score,
    "English": english_score,
    "Economics": economics_score,
    "Physical Education": physical_education_score,
    "Computers": computers_score,
    "Social Studies": social_studies_score
}

# Grade summary
st.sidebar.markdown("---")
st.sidebar.subheader("Your Interests")

# Get all unique interests from dataset
if not careers_df.empty and 'top_interests' in careers_df.columns:
    all_interests = careers_df["top_interests"].dropna().str.split("|").explode().unique()
else:
    all_interests = []

# Combine with our categorized interests for completeness
all_interest_options = sorted(list(set(list(all_interests) + TECHNICAL_INTERESTS + CREATIVE_INTERESTS)))

primary_interest = st.sidebar.selectbox(
    "Primary Interest", 
    all_interest_options
)

secondary_interest = st.sidebar.selectbox(
    "Secondary Interest (Optional)", 
    ["None"] + list(all_interest_options)
)

# --- MAIN CONTENT AREA ---
st.markdown(f"""
<div class='theme-card'>
    <h2 style='color: {PRIMARY_COLOR};'>🧠 Psychometric Assessment</h2>
    <p>Complete this assessment to help us understand your personality traits and work preferences.</p>
</div>
""", unsafe_allow_html=True)

total_questions = len(quiz_df)
answered = 0
quiz_scores = defaultdict(int)

# Initialize quiz responses in session state
if 'quiz_responses' not in st.session_state:
    st.session_state.quiz_responses = {}
    st.session_state.quiz_completed = False

# Use tabs to organize quiz instead of one long scroll
quiz_tab1, quiz_tab2 = st.tabs(["📝 Take Assessment", "📊 Quiz Progress"])

with quiz_tab1:
    # Create expander for quiz questions
    with st.expander("Click to view and answer quiz questions", expanded=True):
        # Add custom CSS for wider radio buttons
        st.markdown("""
        <style>
        div[data-testid="stRadio"] > div {
            padding: 15px 25px !important;
            margin: 12px 0 !important;
            background-color: #E3E8DA !important;
            border-radius: 10px !important;
            border-left: 4px solid #556B2F !important;
            width: 95% !important;
            max-width: 95% !important;
        }
        div[data-testid="stRadio"] label {
            width: 100% !important;
            white-space: normal !important;
            word-wrap: break-word !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for i, row in quiz_df.iterrows():
            options = [row.get("option_a"), row.get("option_b"), row.get("option_c")]
            if "option_d" in row and pd.notna(row.get("option_d")):
                options.append(row["option_d"])
            
            valid_options = [o for o in options if pd.notna(o)]
            
            # Create question key
            question_key = f"quiz_{i}"
            
            # Get stored response or default
            default_index = 0
            if question_key in st.session_state.quiz_responses:
                if st.session_state.quiz_responses[question_key] in valid_options:
                    default_index = valid_options.index(st.session_state.quiz_responses[question_key]) + 1
            
            # Question display
            st.markdown(f"**Q{i+1}. {row.get('question', f'Question {i+1}')}**")
            
            # Create selection with "Select an option" as first
            selection_options = ["-- Select --"] + valid_options
            ans = st.radio(
                f"Select your answer for Q{i+1}:",
                selection_options,
                index=default_index,
                key=f"quiz_select_{i}",
                horizontal=False,
                label_visibility="collapsed"
            )
            
            # Store response and calculate score
            if ans != "-- Select --":
                st.session_state.quiz_responses[question_key] = ans
                answered += 1
                
                # Calculate score properly
                answer_index = selection_options.index(ans) - 1
                if 0 <= answer_index < len(valid_options):
                    trait = row.get("trait", "")
                    if trait:
                        # Score mapping based on position
                        if answer_index == 0:  # Strongly Agree
                            quiz_scores[trait] += 4
                        elif answer_index == 1:  # Agree
                            quiz_scores[trait] += 3
                        elif answer_index == 2:  # Disagree
                            quiz_scores[trait] += 2
                        elif answer_index == 3:  # Strongly Disagree
                            quiz_scores[trait] += 1
            
            # Add a small separator between questions
            if i < len(quiz_df) - 1:
                st.markdown("---")

with quiz_tab2:
    st.subheader("Quiz Progress & Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Questions Answered", f"{answered}/{total_questions}")
    
    with col2:
        percentage = (answered / total_questions) * 100
        st.metric("Completion", f"{percentage:.0f}%")
    
    with col3:
        if answered == total_questions:
            st.session_state.quiz_completed = True
            st.success("✅ Quiz Complete!")
        elif answered >= total_questions * 0.5:
            st.info("📝 In Progress")
        else:
            st.warning("⚠️ More to Answer")
    
    # Progress bar
    progress = answered / total_questions
    st.progress(progress)
    
    # Quiz reset button
    if st.button("🔄 Reset Quiz", type="secondary"):
        st.session_state.quiz_responses = {}
        st.session_state.quiz_completed = False
        st.rerun()

# Add spacing before generate button
st.markdown("<br><br>", unsafe_allow_html=True)

# --- GENERATE RECOMMENDATION ---
if st.button("🚀 Generate Career Recommendations", type="primary", use_container_width=True):
    # Validation check
    if total_questions > 0 and answered < total_questions * 0.3:
        st.error(f"Please answer at least {int(total_questions * 0.3)} quiz questions for recommendations.")
        st.stop()
    
    if not st.session_state.quiz_completed:
        st.warning("Complete the quiz for best results!")
    
    # Calculate quiz trait scores properly
    quiz_trait_scores = defaultdict(int)
    for i, row in quiz_df.iterrows():
        question_key = f"quiz_{i}"
        if question_key in st.session_state.quiz_responses:
            ans = st.session_state.quiz_responses[question_key]
            trait = row.get("trait", "")
            options = []
            for opt in ['option_a', 'option_b', 'option_c', 'option_d']:
                if opt in row and pd.notna(row[opt]):
                    options.append(row[opt])
            
            if ans in options:
                idx = options.index(ans)
                # Convert to score: Strongly Agree=4, Agree=3, Disagree=2, Strongly Disagree=1
                score = 4 - idx
                quiz_trait_scores[trait] += score
    
    # Normalize quiz scores to 0-100 scale
    max_possible_score = len(quiz_df) * 4  # Max 4 per question
    if max_possible_score > 0:
        total_quiz_score = sum(quiz_trait_scores.values())
        quiz_percentage = (total_quiz_score / max_possible_score) * 100
    else:
        quiz_percentage = 0
    
    # Define scoring function
        # Define scoring function
    def calc_score(row):
        # --- ACADEMIC SCORING (45% weight) ---
        subjects = row.get("core_subjects", "").split("|") if pd.notna(row.get("core_subjects", "")) else []
        subject_scores = []
        
        for subject in subjects:
            subject_clean = subject.strip()
            
            # Map subjects to grades
            if subject_clean in ["Math", "Mathematics"]:
                subject_scores.append(grades['Math'])
            elif subject_clean == "Physics":
                subject_scores.append(grades['Math'] * 0.5 + grades['Science'] * 0.5)
            elif subject_clean in ["Chemistry", "Biology", "Science"]:
                subject_scores.append(grades['Science'])
            elif subject_clean in ["English", "Literature", "Writing"]:
                subject_scores.append(grades['English'])
            elif subject_clean == "Logic":
                subject_scores.append(grades['Math'])
            elif subject_clean in ["Computers", "Computer_Science", "Computer Science", "IT"]:
                subject_scores.append(grades['Computers'])
            elif subject_clean in ["Economics", "Business", "Finance", "Commerce"]:
                subject_scores.append(grades['Economics'])
            elif subject_clean in ["Physical_Education", "Physical Education", "Sports"]:
                subject_scores.append(grades['Physical Education'])
            elif subject_clean in ["History", "Political_Science", "Sociology", "Geography", "Psychology", "Civics", "Social Studies"]:
                subject_scores.append(grades['Social Studies'])
            elif subject_clean in ["Art", "Design", "Music", "Photography", "Fashion", "Fine Arts"]:
                subject_scores.append(grades['English'] * 0.4 + grades['Social Studies'] * 0.3 + grades['Science'] * 0.3)
            elif subject_clean in ["Home_Science", "Home Science", "Nutrition"]:
                subject_scores.append(grades['Science'] * 0.5 + grades['Social Studies'] * 0.5)
            elif subject_clean in ["Statistics", "Data Science"]:
                subject_scores.append(grades['Math'] * 0.7 + grades['Computers'] * 0.3)
            elif subject_clean in ["Law", "Legal Studies"]:
                subject_scores.append(grades['English'] * 0.5 + grades['Social Studies'] * 0.5)
        
        # Calculate subject score
        if len(subject_scores) >= 2:
            academic_score = np.mean(subject_scores)
        elif len(subject_scores) == 1:
            academic_score = subject_scores[0] * 0.6
        else:
            academic_score = 0
        
        # --- INTEREST SCORING (35% weight) ---
        interests = row.get("top_interests", "").split("|") if pd.notna(row.get("top_interests", "")) else []
        
        primary_match = primary_interest in interests
        secondary_match = (secondary_interest != "None") and (secondary_interest in interests)
        
        if primary_match and secondary_match:
            interest_score = 100
        elif primary_match:
            interest_score = 80
        elif secondary_match:
            interest_score = 50
        else:
            # Check for partial word matches
            interest_score = 0
            primary_words = set(primary_interest.lower().split())
            for interest in interests:
                interest_words = set(interest.lower().split())
                if primary_words & interest_words:
                    interest_score = 30
                    break
        
        # --- PERSONALITY SCORING (20% weight) ---
        row_traits = row.get("traits", "").split("|") if pd.notna(row.get("traits", "")) else []
        
        if row_traits and quiz_trait_scores:
            trait_scores = []
            for trait in row_traits:
                trait_clean = trait.strip()
                user_trait_score = quiz_trait_scores.get(trait_clean, 0)
                trait_question_count = len(quiz_df[quiz_df['trait'] == trait_clean])
                
                if trait_question_count > 0:
                    max_trait_score = trait_question_count * 4
                    normalized_trait_score = (user_trait_score / max_trait_score) * 100
                    trait_scores.append(normalized_trait_score)
            
            personality_score = np.mean(trait_scores) if trait_scores else 50
        else:
            personality_score = 50
        
        # --- FINAL SCORE (Weighted average) ---
        final_score = (academic_score * 0.45) + (interest_score * 0.35) + (personality_score * 0.20)
        
        return academic_score, primary_match, final_score, secondary_match, personality_score
        # Prepare user features for ML
    user_features = {
        'math_score': grades['Math'],
        'science_score': grades['Science'],
        'english_score': grades['English'],
        'economics_score': grades['Economics'],
        'physical_education_score': grades['Physical Education'],
        'computers_score': grades['Computers'],
        'social_studies_score': grades['Social Studies'],
        'primary_interest': primary_interest,
        'secondary_interest': secondary_interest if secondary_interest != "None" else "None"
    }
    
    # Use ensemble ML if available
    ml_predictions = None
    if st.session_state.ml_models:
        ml_predictions = predict_with_ml(user_features, model_type='ensemble')
    
    print(f"\n🎯 ML Predictions for {st.session_state.username}:")
    if st.session_state.ml_accuracy:
        for model, acc in st.session_state.ml_accuracy.items():
            print(f"   {model}: {acc*100:.1f}% accuracy")
    print(f"   Top 3 predictions: {dict(list(ml_predictions.items())[:3])}")
    print("-" * 50)

    # Check if careers_df exists and is not empty
    if careers_df.empty:
        st.error("Careers dataset is empty. Please check your careers.csv file.")
        st.stop()
        # Calculate rule-based scores for all careers
    scores = careers_df.apply(calc_score, axis=1)
    careers_df["subject_score"] = [s[0] for s in scores]
    careers_df["primary_interest_match"] = [s[1] for s in scores]
    careers_df["rule_based_score"] = [s[2] for s in scores]
    careers_df["secondary_match"] = [s[3] for s in scores]
    careers_df["personality_score"] = [s[4] for s in scores]

    # Combine ML predictions with rule-based scores if available
    if ml_predictions and len(ml_predictions) > 0:
        # Add ML probability scores
        # Add this line right before line 888
        careers_df["ml_score"] = careers_df["career_stream"].map(        lambda x: ml_predictions.get(x, 0) * 100
        ).fillna(0)
        
        # Combined score (60% ML, 40% rule-based)
        careers_df["final_score"] = careers_df["ml_score"] * 0.6 + careers_df["rule_based_score"] * 0.4
        sort_column = "final_score"
        score_column = "final_score"
    else:
        careers_df["final_score"] = careers_df["rule_based_score"]
        sort_column = "rule_based_score"
        score_column = "rule_based_score"
    
    # Sort careers by score
    careers_df_sorted = careers_df.sort_values(sort_column, ascending=False)
    
    # Check if we have any results
    if careers_df_sorted.empty:
        st.error("No career recommendations could be generated.")
        st.stop()
    
    # Get top recommendation
    best_row = careers_df_sorted.iloc[0]
    career_stream = best_row.get("career_stream", "")  # Change from "career_stream" to "stream"
    top_careers = best_row.get("example_careers", "").split("|") if pd.notna(best_row.get("example_careers", "")) else []

    # Calculate rule-based scores for all careers
    scores = careers_df.apply(calc_score, axis=1)
    careers_df["subject_score"] = [s[0] for s in scores]
    careers_df["primary_interest_match"] = [s[1] for s in scores]
    careers_df["rule_based_score"] = [s[2] for s in scores]
    careers_df["secondary_match"] = [s[3] for s in scores]
    careers_df["personality_score"] = [s[4] for s in scores]

    # Get top recommendation
    sort_column = "final_score" if "final_score" in careers_df.columns else "rule_based_score"
    careers_df_sorted = careers_df.sort_values(sort_column, ascending=False)
    best_row = careers_df_sorted.iloc[0]
    career_stream = best_row.get("career_stream", "")
    print(f"DEBUG - career_stream = '{career_stream}'")
    top_careers = best_row.get("example_careers", "").split("|") if pd.notna(best_row.get("example_careers", "")) else []

    # Save user data for ML training
    save_user_data_for_training(
        username=st.session_state.username,
        grades=grades,
        interests={'primary': primary_interest, 'secondary': secondary_interest},
        quiz_scores=dict(quiz_trait_scores),
        career_stream=career_stream,
    )
    st.session_state.career_stream = career_stream
    st.session_state.best_row = best_row
    st.session_state.score_column = score_column
    st.session_state.top_careers = top_careers
    st.session_state.careers_df_sorted = careers_df_sorted

career_stream = st.session_state.get("career_stream", "")
best_row = st.session_state.get("best_row", None)
score_column = st.session_state.get("score_column", "rule_based_score")
top_careers = st.session_state.get("top_careers", [])
careers_df_sorted = st.session_state.get("careers_df_sorted", pd.DataFrame())

# --- DISPLAY RESULTS IN TABS ---
tabs = st.tabs(["Results", "Analysis", "Roadmap"])

with tabs[0]:
    if best_row is not None:
        st.markdown(f"""
        <div class='theme-card'>
            <h2 style='color: {PRIMARY_COLOR}; text-align: center;'>Your Career Recommendation</h2>
        </div>
        """, unsafe_allow_html=True)

        # Top metrics in cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <h3>Recommended Stream</h3>
                <h2>{career_stream}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            success_prob = min(99, int(best_row[score_column]))
            if st.session_state.ml_models:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>AI Match Score</h3>
                    <h2>{success_prob}%</h2>
                    <small>AI-Powered Analysis</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>Match Score</h3>
                    <h2>{success_prob}%</h2>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            top_career = top_careers[0] if top_careers else "Various Careers"
            st.markdown(f"""
            <div class='metric-card'>
                <h3>Top Career</h3>
                <h2>{top_career}</h2>
            </div>
            """, unsafe_allow_html=True)

        # Alternative paths
        st.markdown(f"""
        <div class='theme-card'>
            <h3 style='color: {PRIMARY_COLOR};'>Alternative Career Paths</h3>
        </div>
        """, unsafe_allow_html=True)

        top_alternatives = []
        for idx in range(1, min(4, len(careers_df_sorted))):
            alt_row = careers_df_sorted.iloc[idx]
            alt_stream = alt_row.get("career_stream", "")
            alt_careers = (
                alt_row.get("example_careers", "").split("|")
                if pd.notna(alt_row.get("example_careers", ""))
                else []
            )

            if alt_stream != career_stream:
                top_alternatives.append({
                    "career_stream": alt_stream,
                    "score": alt_row[score_column],
                    "top_career": alt_careers[0] if alt_careers else "Various",
                    "academic_match": alt_row["subject_score"],
                    "interest_match": "Yes" if alt_row["primary_interest_match"] else "No",
                })

        if top_alternatives:
            cols = st.columns(len(top_alternatives))
            for idx, alt in enumerate(top_alternatives):
                with cols[idx]:
                    st.markdown(f"""
                    <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px;
                                border-left: 4px solid {ACCENT_COLOR_1};'>
                        <h4>Alternative {idx+1}</h4>
                        <h3>{alt['career_stream']}</h3>
                        <p><b>Match Score:</b> {int(alt['score'])}%</p>
                        <p><b>Top Career:</b> {alt['top_career']}</p>
                        <p><b>Interest Match:</b> {alt['interest_match']}</p>
                        <p><b>Academic Fit:</b> {int(alt['academic_match'])}%</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No alternative career paths found.")
    else:
        st.info("👆 Fill in your grades and click 'Generate Career Recommendations' to see results.")

with tabs[1]:
    if best_row is not None:
        st.markdown(f"""
        <div class='theme-card'>
            <h3 style='color: {PRIMARY_COLOR};'>📊 Score Breakdown & Subject Analysis</h3>
        </div>
        """, unsafe_allow_html=True)

        # Pie chart at the top
        st.subheader("⚖️ Score Weight Distribution")

        # Calculate breakdown properly
        academic_val = float(best_row["subject_score"])
        interest_val = 70.0 if best_row.get("primary_interest_match", False) else 0.0
        if best_row.get('secondary_match', False):
            interest_val = 100.0 if interest_val == 70 else 40.0
        personality_val = float(best_row.get("personality_score", 50))

        # Normalize for pie chart
        total = academic_val + interest_val + personality_val
        if total > 0:
            academic_pct = (academic_val / total) * 100
            interest_pct = (interest_val / total) * 100
            personality_pct = (personality_val / total) * 100
        else:
            academic_pct = interest_pct = personality_pct = 33.33

        breakdown = {
            "Academic (45%)": academic_pct,
            "Interest (35%)": interest_pct,
            "Personality (20%)": personality_pct
        }

        # Create two columns for pie chart and explanation
        pie_col, explain_col = st.columns([2, 3])

        with pie_col:
            fig, ax = plt.subplots(figsize=(6, 6))
            colors = [ACCENT_COLOR_1, ACCENT_COLOR_2, ACCENT_COLOR_3]
            wedges, texts, autotexts = ax.pie(
                breakdown.values(),
                labels=breakdown.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                textprops={'fontsize': 10, 'color': TEXT_COLOR},
                explode=(0.05, 0.05, 0.05)
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_backgroundcolor(PRIMARY_COLOR)
            ax.axis('equal')
            fig.patch.set_facecolor(BACKGROUND_COLOR)
            plt.tight_layout()
            st.pyplot(fig)

        with explain_col:
            st.markdown(f"""
            ### What This Breakdown Means:
            
            **🎓 Academic Subjects ({int(academic_pct)}%)**
            - Based on your grades in all 7 subjects
            - Higher scores in relevant subjects increase this component
            
            **❤️ Interest Match ({int(interest_pct)}%)**
            - Primary interest match: +70%
            - Secondary interest match: +40% bonus
            
            **🧩 Personality ({int(personality_pct)}%)**
            - Derived from your psychometric test responses
            - Evaluates personality traits and work preferences
            """)

        # --- SUBJECT STRENGTH ANALYSIS ---
        st.markdown("---")
        st.subheader("📈 Subject Strength Analysis (All 7 Subjects)")

        if pd.notna(best_row.get("core_subjects", "")):
            career_subjects = best_row["core_subjects"].split("|")
        else:
            career_subjects = []

        subject_display_names = ['Math', 'Science', 'English', 'Economics', 'P.E.', 'Computers', 'Soc. Studies']
        subject_values = [
            grades['Math'],
            grades['Science'],
            grades['English'],
            grades['Economics'],
            grades['Physical Education'],
            grades['Computers'],
            grades['Social Studies']
        ]
        subject_colors = [PRIMARY_COLOR, ACCENT_COLOR_1, ACCENT_COLOR_2, ACCENT_COLOR_3,
                          ACCENT_COLOR_1, ACCENT_COLOR_2, ACCENT_COLOR_3]

        for i, (subj, val, color) in enumerate(zip(subject_display_names, subject_values, subject_colors)):
            is_critical = False
            for cs in career_subjects:
                cs_clean = cs.strip().lower()
                subj_clean = subj.lower()
                if subj_clean in cs_clean or cs_clean in subj_clean:
                    is_critical = True
                    break
                if subj == "P.E." and "physical" in cs_clean:
                    is_critical = True
                    break
                if subj == "Soc. Studies" and ("history" in cs_clean or "political" in cs_clean or "geography" in cs_clean):
                    is_critical = True
                    break
                if subj == "Economics" and ("business" in cs_clean or "finance" in cs_clean or "commerce" in cs_clean):
                    is_critical = True
                    break
                if subj == "Computers" and ("computer" in cs_clean or "it" in cs_clean or "data" in cs_clean):
                    is_critical = True
                    break

            col_subj, col_bar = st.columns([1, 3])
            with col_subj:
                if is_critical:
                    st.markdown(f"**{subj}** ⭐")
                else:
                    st.markdown(f"**{subj}**")
            with col_bar:
                progress_color = PRIMARY_COLOR if is_critical else color
                st.markdown(f"""
                <div style='background-color: {SECONDARY_BG}; border-radius: 10px; height: 30px; width: 100%; margin: 5px 0;'>
                    <div style='background: linear-gradient(90deg, {progress_color}, {color}); 
                                width: {val}%; height: 30px; border-radius: 10px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px;'>
                        <span style='color: white; font-weight: bold;'>{int(val)}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**📌 Required Subjects for this Career:**")

        if career_subjects:
            req_cols = st.columns(3)
            req_idx = 0
            for subject in career_subjects[:9]:
                subject_clean = subject.strip()
                display_name = subject_clean.replace('_', ' ')
                with req_cols[req_idx % 3]:
                    st.markdown(f"""
                    <span style='background-color: {SECONDARY_BG}; color: {TEXT_COLOR}; 
                               padding: 8px 12px; border-radius: 20px; font-size: 0.9rem;
                               border-left: 4px solid {PRIMARY_COLOR}; display: inline-block; margin: 3px; font-weight: 500;'>
                        {display_name}
                    </span>
                    """, unsafe_allow_html=True)
                req_idx += 1
        else:
            st.info("No specific subject requirements found for this career path.")
    else:
        st.info("👆 Generate your recommendations first.")

with tabs[2]:
    if best_row is not None:
        st.markdown(f"""
        <div class='theme-card'>
            <h3 style='color: {PRIMARY_COLOR};'>🗺️ Your Career Roadmap</h3>
        </div>
        """, unsafe_allow_html=True)

        if pd.notna(best_row.get("core_subjects", "")):
            career_subjects = best_row["core_subjects"].split("|")
        else:
            career_subjects = ["Relevant subjects"]

        entrance_exams = "Relevant exams"
        if not colleges_df.empty and career_stream:
            matching_colleges = colleges_df[colleges_df['career_stream'].str.contains(career_stream, case=False, na=False)]
            if not matching_colleges.empty and 'entrance_test' in matching_colleges.columns:
                exams = matching_colleges['entrance_test'].dropna().unique()
                if len(exams) > 0:
                    entrance_exams = exams[0].split()[0] if len(exams) == 1 else f"{exams[0].split()[0]}, {exams[1].split()[0]}"

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; 
                        border-left: 5px solid {PRIMARY_COLOR}; text-align: center; height: 140px;'>
                <div style='background-color: {PRIMARY_COLOR}; width: 30px; height: 30px; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            margin: 0 auto 10px auto;'>
                    <span style='color: white; font-weight: bold;'>1</span>
                </div>
                <h4 style='color: {PRIMARY_COLOR}; margin-bottom: 5px; font-size: 1rem;'>11th-12th</h4>
                <p style='color: {TEXT_COLOR}; font-size: 0.8rem; margin: 0;'>
                    {', '.join([s.replace('_', ' ') for s in career_subjects[:2]])}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; 
                        border-left: 5px solid {ACCENT_COLOR_1}; text-align: center; height: 140px;'>
                <div style='background-color: {ACCENT_COLOR_1}; width: 30px; height: 30px; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            margin: 0 auto 10px auto;'>
                    <span style='color: white; font-weight: bold;'>2</span>
                </div>
                <h4 style='color: {ACCENT_COLOR_1}; margin-bottom: 5px; font-size: 1rem;'>Entrance</h4>
                <p style='color: {TEXT_COLOR}; font-size: 0.8rem; margin: 0;'>
                    {entrance_exams}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; 
                        border-left: 5px solid {ACCENT_COLOR_2}; text-align: center; height: 140px;'>
                <div style='background-color: {ACCENT_COLOR_2}; width: 30px; height: 30px; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            margin: 0 auto 10px auto;'>
                    <span style='color: white; font-weight: bold;'>3</span>
                </div>
                <h4 style='color: {ACCENT_COLOR_2}; margin-bottom: 5px; font-size: 1rem;'>Degree</h4>
                <p style='color: {TEXT_COLOR}; font-size: 0.8rem; margin: 0;'>
                    {career_stream.replace('_', ' ').split()[0] if ' ' in career_stream else career_stream[:10]}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div style='background-color: {SECONDARY_BG}; padding: 15px; border-radius: 10px; 
                        border-left: 5px solid {ACCENT_COLOR_3}; text-align: center; height: 140px;'>
                <div style='background-color: {ACCENT_COLOR_3}; width: 30px; height: 30px; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            margin: 0 auto 10px auto;'>
                    <span style='color: white; font-weight: bold;'>4</span>
                </div>
                <h4 style='color: {ACCENT_COLOR_3}; margin-bottom: 5px; font-size: 1rem;'>Career</h4>
                <p style='color: {TEXT_COLOR}; font-size: 0.8rem; margin: 0;'>
                    {top_careers[0].split()[0] if top_careers else 'Job'}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📈 10-Year Growth Projection")

        years = list(range(1, 11))
        base_score = best_row[score_column]

        if career_stream in ['Medical', 'Computer Science', 'Engineering', 'Aerospace_Engineering', 'IT_Computer_Science']:
            growth_rate = 0.10
        elif career_stream in ['Business Management', 'Commerce', 'Chartered_Accountancy', 'Company_Secretary', 'Sports_Management']:
            growth_rate = 0.08
        elif career_stream in ['Design', 'Fashion_Design', 'Graphic_Design', 'Photography', 'Performing_Arts']:
            growth_rate = 0.07
        else:
            growth_rate = 0.06

        growth_curve = [base_score * (1 + growth_rate * y) for y in years]

        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(years, growth_curve, marker='o', color=PRIMARY_COLOR, linewidth=2, markersize=6)
        ax2.fill_between(years, growth_curve, alpha=0.2, color=ACCENT_COLOR_1)
        ax2.set_xlabel('Years')
        ax2.set_ylabel('Career Index')
        ax2.set_title(f'Growth: {career_stream.replace("_", " ")[:20]}')
        ax2.grid(True, alpha=0.3)
        ax2.set_facecolor(BACKGROUND_COLOR)
        fig2.patch.set_facecolor(BACKGROUND_COLOR)
        plt.tight_layout()
        st.pyplot(fig2)

        year_1_value = growth_curve[0]
        year_5_value = growth_curve[4]
        year_10_value = growth_curve[9]
        five_year_growth = ((year_5_value - year_1_value) / year_1_value) * 100
        ten_year_growth = ((year_10_value - year_1_value) / year_1_value) * 100

        st.markdown(f"""
        <div style='background-color: {SECONDARY_BG}; border-radius: 10px; padding: 15px; 
                    border-left: 5px solid {PRIMARY_COLOR}; margin-top: 15px;'>
            <div style='display: flex; justify-content: space-around; text-align: center;'>
                <div>
                    <p style='color: {TEXT_COLOR}; opacity: 0.8; margin: 0; font-size: 0.8rem;'>Year 1</p>
                    <p style='color: {PRIMARY_COLOR}; font-size: 1.2rem; font-weight: bold; margin: 0;'>{int(year_1_value)}</p>
                </div>
                <div>
                    <p style='color: {TEXT_COLOR}; opacity: 0.8; margin: 0; font-size: 0.8rem;'>Year 5</p>
                    <p style='color: {ACCENT_COLOR_1}; font-size: 1.2rem; font-weight: bold; margin: 0;'>{int(year_5_value)}</p>
                </div>
                <div>
                    <p style='color: {TEXT_COLOR}; opacity: 0.8; margin: 0; font-size: 0.8rem;'>Year 10</p>
                    <p style='color: {ACCENT_COLOR_2}; font-size: 1.2rem; font-weight: bold; margin: 0;'>{int(year_10_value)}</p>
                </div>
                <div>
                    <p style='color: {TEXT_COLOR}; opacity: 0.8; margin: 0; font-size: 0.8rem;'>5Y Growth</p>
                    <p style='color: {PRIMARY_COLOR}; font-size: 1.2rem; font-weight: bold; margin: 0;'>+{five_year_growth:.0f}%</p>
                </div>
                <div>
                    <p style='color: {TEXT_COLOR}; opacity: 0.8; margin: 0; font-size: 0.8rem;'>10Y Growth</p>
                    <p style='color: {ACCENT_COLOR_2}; font-size: 1.2rem; font-weight: bold; margin: 0;'>+{ten_year_growth:.0f}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Generate your recommendations first.")
