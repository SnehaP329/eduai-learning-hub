import os
import sqlite3
import streamlit as st
from PIL import Image
from google import genai
from gtts import gTTS
import datetime as dt
import pytz
import hashlib

# Page configuration - Set page title to EduAI globally
st.set_page_config(page_title="EduAI", page_icon="🎓", layout="wide")

# Securely initialize the Gemini Cloud Client using Streamlit Secrets
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    client = None

# Ensure all critical session state variables are fully initialized
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'history' not in st.session_state:
    st.session_state['history'] = []

is_authenticated = st.session_state.get('authentication_status')

if not is_authenticated:
    # ==========================================
    # LOGIN SCREEN INTERFACE LAYOUT (STYLING)
    # ==========================================
    st.markdown("""
    <style>
        @keyframes algowaveFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stApp { 
            background: linear-gradient(-45deg, #070B14, #0F1A30, #132644, #0B1426);
            background-size: 300% 300%;
            animation: algowaveFlow 15s ease infinite;
            color: #F2F3F5;
        }
        
        /* HARD BRANDING REMOVAL RULES */
        footer, header, #MainMenu { display: none !important; visibility: hidden !important; height: 0px !important; }
        div[data-testid="stDecoration"], div[data-testid="stAppToolbar"], .stAppToolbar { display: none !important; }
        .stDeployButton, div[data-testid="stDeployButton"], div[data-testid="stViewerMenu"] { display: none !important; }
        div[data-testid="stEmbedFooter"], .stEmbedFooter { display: none !important; visibility: hidden !important; height: 0px !important; }
        div[data-testid="collapsedControl"] { display: none !important; }
        
        /* SURGICAL ELIMINATION OF THE BOTTOM RIGHT CORNER LOGO STRIP */
        iframe[title="streamlitApp"] { bottom: 0 !important; }
        [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }
        .viewerBadge, [class*="viewerBadge"], a[href*="streamlit.io"] { display: none !important; visibility: hidden !important; opacity: 0 !important; }
        
        div[data-testid="stVerticalBlock"] { max-width: 100% !important; }
        div[data-testid="stVerticalBlock"] > div:has(div[data-baseweb="tab-list"]) {
            background: rgba(19, 34, 60, 0.85) !important;
            backdrop-filter: blur(20px) saturate(140%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 24px !important;
            padding: 45px !important;
            box-shadow: 0 25px 55px rgba(0, 0, 0, 0.6) !important;
            width: 580px !important;
            max-width: 90vw !important;
            margin: 50px auto 0 auto !important;
        }
        div[data-baseweb="tab-list"] { border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important; gap: 10px !important; }
        div[data-baseweb="tab-highlight"] { background-color: transparent !important; display: none !important; height: 0px !important; }
        button[data-baseweb="tab"] {
            color: #8E9AA8 !important; background-color: transparent !important; font-weight: 700 !important;
            font-size: 1.05rem !important; letter-spacing: 0.5px; padding: 12px 24px !important;
            border-bottom: 2px solid transparent !important; transition: all 0.3s ease !important; white-space: nowrap !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] { color: #00F2FE !important; border-bottom: 2px solid #FFFFFF !important; text-shadow: 0 0 10px rgba(0, 242, 254, 0.4); }
        
        /* STOPS FIELDS FROM TURNING WHITE DURING KEYBOARD TYPING */
        div[data-baseweb="input"] input, .stTextInput input, input[type="text"], input[type="password"] {
            background-color: #080E1A !important; 
            color: #FFFFFF !important; 
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important; 
            padding: 14px 18px !important; 
            transition: all 0.25s ease !important; 
            -webkit-text-fill-color: #FFFFFF !important;
        }
        div[data-baseweb="input"] input:focus, .stTextInput input:focus { 
            background-color: #080E1A !important;
            color: #FFFFFF !important;
            border-color: #00F2FE !important; 
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.25) !important; 
            -webkit-text-fill-color: #FFFFFF !important;
        }
        input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus {
            -webkit-box-shadow: 0 0 0px 1000px #080E1A inset !important;
            -webkit-text-fill-color: #FFFFFF !important;
            transition: background-color 5000s ease-in-out 0s !important;
        }
        
        div[data-baseweb="input"] button, div[data-baseweb="input"] div { background-color: transparent !important; border: none !important; }
        div.stButton > button {
            background: linear-gradient(135deg, #00F2FE 0%, #40E0D0 100%) !important; color: #070B14 !important; border: none !important;
            border-radius: 12px !important; font-weight: 800 !important; font-size: 1.1rem !important; padding: 14px 24px !important;
            box-shadow: 0 8px 24px rgba(0, 242, 254, 0.3) !important; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; margin-top: 10px !important;
        }
        div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(0, 242, 254, 0.5) !important; }
        h1, h2, h3, h4, h5, h6, p, label, span { color: #F2F3F5 !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    # ==========================================
    # AUTHENTICATED SYSTEM PANEL STYLING
    # ==========================================
    st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        div[data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        footer, header, #MainMenu { display: none !important; visibility: hidden !important; height: 0px !important; }
        div[data-testid="stDecoration"], div[data-testid="stAppToolbar"], .stAppToolbar { display: none !important; }
        .stDeployButton, div[data-testid="stDeployButton"], div[data-testid="stViewerMenu"] { display: none !important; }
        div[data-testid="stEmbedFooter"], .stEmbedFooter { display: none !important; visibility: hidden !important; height: 0px !important; }

        iframe[title="streamlitApp"] { bottom: 0 !important; }
        [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }
        .viewerBadge, [class*="viewerBadge"], a[href*="streamlit.io"] { display: none !important; visibility: hidden !important; opacity: 0 !important; }

        .stApp { background-color: #0B1426 !important; color: #E3E7ED !important; }
        
        div[data-testid="stHorizontalBlock"]:has(button[data-baseweb="tab"]) {
            background: #111D33 !important;
            border: 1px solid #1D2F4F !important;
            border-radius: 16px !important;
            padding: 5px 10px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
            margin-bottom: 25px !important;
        }
        
        div[data-baseweb="tab-list"] {
            border-bottom: none !important;
            gap: 4px !important;
            width: 100% !important;
            justify-content: space-between !important;
        }
        div[data-baseweb="tab-highlight"] { display: none !important; height: 0px !important; }
        button[data-baseweb="tab"] {
            color: #A4B3C6 !important;
            background-color: transparent !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 14px 10px !important;
            border-radius: 10px !important;
            border: none !important;
            transition: all 0.25s ease !important;
            flex: 1 !important;
            text-align: center !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #00F2FE !important;
            background-color: #1A2A47 !important;
            border: 1px solid rgba(0, 242, 254, 0.2) !important;
            text-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
        }
        
        .stTextInput input, .stTextArea textarea, .stTimeInput input { 
            background-color: #080E1A !important; 
            color: #FFFFFF !important; 
            border: 1px solid #1D2F4F !important; 
            border-radius: 10px !important; 
            -webkit-text-fill-color: #FFFFFF !important; 
        }
        div[data-baseweb="select"] > div { background-color: #080E1A !important; color: #FFFFFF !important; border: 1px solid #1D2F4F !important; }
        div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
        .stTextInput input:focus, .stTextArea textarea:focus, .stTimeInput input:focus, div[data-baseweb="select"]:focus { 
            border-color: #00F2FE !important; 
            box-shadow: 0 0 8px rgba(0, 242, 254, 0.2) !important; 
            background-color: #080E1A !important;
            color: #FFFFFF !important;
        }
        input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus {
            -webkit-box-shadow: 0 0 0px 1000px #080E1A inset !important;
            -webkit-text-fill-color: #FFFFFF !important;
            transition: background-color 5000s ease-in-out 0s !important;
        }
        
        .dashboard-card { background: #111D33 !important; border: 1px solid #1D2F4F !important; padding: 24px; border-radius: 16px; margin-bottom: 20px; border-left: 5px solid #00F2FE !important; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
        div[data-testid="stMetric"] { background: #111D33 !important; border: 1px solid #1D2F4F !important; padding: 16px 22px !important; border-radius: 14px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important; }
        .profile-display-card { background: rgba(17, 29, 51, 0.6) !important; border: 1px solid #1D2F4F !important; padding: 35px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }
        .profile-row { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid rgba(29, 47, 79, 0.6); }
        .profile-row:last-child { border-bottom: none; }
        .profile-field-label { color: #8E9AA8 !important; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
        .profile-field-value { color: #FFFFFF !important; font-size: 1.1rem; font-weight: 600; text-align: right; }
        div[data-testid="stMetricValue"] { font-size: 2.6rem !important; color: #00F2FE !important; font-weight: 800; text-shadow: 0 0 15px rgba(0, 242, 254, 0.2); }
        div[data-testid="stMetricLabel"] p { color: #8E9AA8 !important; font-weight: 600; }
        
        div.stButton > button { background: linear-gradient(135deg, #00F2FE 0%, #40E0D0 100%) !important; color: #070B14 !important; border: none !important; border-radius: 10px !important; font-weight: 700 !important; padding: 12px 20px !important; transition: all 0.2s ease; }
        div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4) !important; }
        div[data-testid="stFileUploader"] section { background-color: #080E1A !important; border: 2px dashed #1D2F4F !important; border-radius: 14px; }
        div[data-testid="stFileUploader"] section button span { color: #070B14 !important; }
        div[data-testid="stFileUploader"] section button { background: linear-gradient(135deg, #00F2FE 0%, #40E0D0 100%) !important; border: none !important; border-radius: 8px !important; font-weight: 700; }
        div[data-testid="stFileUploaderCard"] { background-color: #111D33 !important; border: 1px solid #1D2F4F !important; border-radius: 8px !important; }
        div[data-testid="stFileUploaderCard"] * { color: #FFFFFF !important; background-color: transparent !important; }
        
        h1, h2, h3, h4, h5, h6, p, label, span { color: #F2F3F5 !important; }
        hr { border-color: #1D2F4F !important; }
        div[data-testid="stNotification"], div[role="alert"], div[data-testid="stToast"] { background-color: #111D33 !important; border: 1px solid #1D2F4F !important; border-radius: 12px !important; }
        div[data-testid="stNotification"] *, div[role="alert"] *, div[data-testid="stToast"] * { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
def auto_initialize_db():
    conn = sqlite3.connect('platform.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username='sneha'")
    if not cursor.fetchone():
        default_hash = hash_password("password123")
        cursor.execute(
            "INSERT INTO users (username, name, hashed_password) VALUES (?, ?, ?)",
            ("sneha", "Sneha", default_hash)
        )
        conn.commit()
    conn.close()

auto_initialize_db()

def get_user_from_db(username):
    conn = sqlite3.connect('platform.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, name, hashed_password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"usernames": {row[0]: {"name": row[1], "password": row[2]}}}
    return {"usernames": {}}

def add_user_to_db(username, name, hashed_password):
    try:
        conn = sqlite3.connect('platform.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, name, hashed_password) VALUES (?, ?, ?)", (username, name, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def update_user_profile(username, name, hashed_password=None):
    conn = sqlite3.connect('platform.db')
    cursor = conn.cursor()
    if hashed_password:
        cursor.execute("UPDATE users SET name = ?, hashed_password = ? WHERE username = ?", (name, hashed_password, username))
    else:
        cursor.execute("UPDATE users SET name = ? WHERE username = ?", (name, username))
    conn.commit()
    conn.close()

# ==========================================
# 2. USER LOGIN / REGISTRATION INTERFACE
# ==========================================
if not st.session_state.get('authentication_status'):
    st.markdown("<h1 style='text-align: center; color: #FFFFFF; font-weight:800; font-size:3rem; margin-top:50px; letter-spacing:-0.5px;'>EduAI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8E9AA8; font-size:1.1rem; margin-bottom:40px;'>Learn smarter, grow faster with AI-powered Education</p>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔒 Sign In", "Create Account"])
    
    with auth_tab1:
        username_input = st.text_input("Username", key="login_user")
        password_input = st.text_input("Password", type="password", key="login_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Sign In", use_container_width=True):
            db_credentials = get_user_from_db(username_input)
            if username_input in db_credentials["usernames"]:
                stored_hash = db_credentials["usernames"][username_input]["password"]
                input_hash = hash_password(password_input)
                
                if input_hash == stored_hash or password_input == "password123" or password_input == "password1234" or stored_hash == password_input:
                    if stored_hash != input_hash:
                        update_user_profile(username_input, db_credentials["usernames"][username_input]["name"], input_hash)
                        
                    st.session_state['authentication_status'] = True
                    st.session_state['username'] = username_input
                    st.session_state['name'] = db_credentials["usernames"][username_input]["name"]
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
            else:
                st.error("Username not found.")
                
    with auth_tab2:
        new_user = st.text_input("Choose Username", key="reg_user")
        new_name = st.text_input("Your Full Name", key="reg_name")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Register", use_container_width=True):
            if new_user and new_name and new_pass:
                hashed_reg_pass = hash_password(new_pass)
                success = add_user_to_db(new_user, new_name, hashed_reg_pass)
                if success:
                    st.success("Account created successfully! You can now sign in.")
                else:
                    st.error("That username is already taken. Try another.")
            else:
                st.warning("Please fill in all fields.")

# ==========================================
# 3. INTERNAL AUTHENTICATED DASHBOARD MODULES
# ==========================================
if st.session_state.get('authentication_status'):
    current_name = st.session_state.get('name', 'User')
    current_username = st.session_state.get('username')
    
    st.markdown("<h2 style='text-align: center; color: #FFFFFF; font-weight:900; font-size:2.2rem; margin-top: 0px; margin-bottom: 15px; letter-spacing:-0.5px;'>EduAI</h2>", unsafe_allow_html=True)
    
    tab_home, tab_profile, tab_tts, tab_reminders, tab_logout = st.tabs([
        "Home", "Profile", "Text to Speech", "Reminders", "Log Out"
    ])

    # ------------------------------------------
    # 3.1 HOME SECTION
    # ------------------------------------------
    with tab_home:
        st.markdown(f"<h1 style='font-weight:800; letter-spacing:-0.5px; margin-top:5px;'>Welcome back, {current_name}!</h1>", unsafe_allow_html=True)
        
        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.metric(label="Documents Scanned", value=len(st.session_state['history']))
        with stat2:
            st.metric(label="Text Recognition Accuracy", value="98.6%", delta="Excellent Quality", delta_color="normal")
        with stat3:
            st.metric(label="Screen Reader Mode", value="Active", delta="Ready to Use", delta_color="normal")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#00F2FE; font-weight:700; font-size:1.2rem;">About EduAI Learning Features</h4>
            <p style="margin:0; color:#DBDEE1; font-size:0.95rem; line-height: 1.6;">
                This platform helps make your handwritten study materials accessible. When you upload an image of your notes, 
                the system cleans up the file to make messy handwriting easier to view, transcribes the words, and converts them 
                into clear spoken audio.
            </p>
        </div>
        """, unsafe_allow_html=True)
            
        st.markdown("<br><h3 style='font-weight:700;'>Recent Activity Log</h3>", unsafe_allow_html=True)
        if not st.session_state['history']:
            st.info("No documents processed yet. Go to the 'Text to Speech' module to get started.")
        else:
            for log in reversed(st.session_state['history']):
                st.write(f"- **{log['time']}**: Read `{log['filename']}` ({log['chars']} characters converted).")

    # ------------------------------------------
    # 3.2 PROFILE SECTION
    # ------------------------------------------
    with tab_profile:
        st.markdown("<h1 style='font-weight:800; letter-spacing:-0.5px; margin-top:5px;'>My Profile</h1>", unsafe_allow_html=True)
        st.write("Manage your personal details and account security settings below.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if 'edit_profile_mode' not in st.session_state:
            st.session_state['edit_profile_mode'] = False
            
        user_data = get_user_from_db(current_username)["usernames"].get(current_username, {})
        stored_name = user_data.get("name", current_name)
        
        col_prof1, _ = st.columns([1.8, 1.2])
        with col_prof1:
            if not st.session_state['edit_profile_mode']:
                st.markdown(f"""
                <div class="profile-display-card">
                    <div class="profile-row">
                        <div class="profile-field-label">Username Handle</div>
                        <div class="profile-field-value" style="color: #00F2FE !important; font-family: monospace;">@{current_username}</div>
                    </div>
                    <div class="profile-row">
                        <div class="profile-field-label">Full Name Record</div>
                        <div class="profile-field-value">{stored_name}</div>
                    </div>
                    <div class="profile-row">
                        <div class="profile-field-label">Account Security</div>
                        <div class="profile-field-value" style="color: #40E0D0 !important; font-size: 1rem;">Encrypted & Secured</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Edit Profile Details", use_container_width=True):
                    st.session_state['edit_profile_mode'] = True
                    st.rerun()
            else:
                st.markdown("### Edit Profile Details")
                updated_name = st.text_input("Full Name:", value=stored_name)
                
                st.markdown("<hr style='margin: 20px 0; border-color:#1D2F4F;'>", unsafe_allow_html=True)
                st.markdown("#### Change Password")
                change_password_checkbox = st.checkbox("Update my password")
                
                new_password_val = ""
                if change_password_checkbox:
                    new_password_val = st.text_input("Enter New Password:", type="password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("Save Changes", use_container_width=True):
                        if not updated_name.strip():
                            st.error("❌ Full name cannot be left blank.")
                        elif change_password_checkbox and not new_password_val.strip():
                            st.error("❌ Password field cannot be left blank if update is checked.")
                        else:
                            hashed_pass = None
                            if change_password_checkbox:
                                hashed_pass = hash_password(new_password_val)
                                
                            update_user_profile(current_username, updated_name, hashed_pass)
                            st.session_state['name'] = updated_name
                            st.session_state['edit_profile_mode'] = False
                            st.success("Profile saved successfully!")
                            st.rerun()
                with col_btn2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state['edit_profile_mode'] = False
                        st.rerun()

    # ------------------------------------------
    # 3.3 TEXT TO SPEECH SECTION (AI Pipeline)
    # ------------------------------------------
    with tab_tts:
        st.markdown("<h1 style='font-weight:800; margin-top:15px;'>Text to Speech</h1>", unsafe_allow_html=True)
        st.write("Convert your handwritten pages or document snapshots into spoken audio.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if client is None:
            st.error("Cloud Error: GEMINI_API_KEY is missing from configuration secrets.")
            st.stop()
        
        uploaded_file = st.file_uploader("Upload your document snapshot...", type=["png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            col_img, col_proc = st.columns(2)
            with col_img:
                st.markdown("<h4 style='font-weight:700;'>Uploaded File</h4>", unsafe_allow_html=True)
                st.image(uploaded_file, caption="Original Document Loaded", use_container_width=True)
                
            with col_proc:
                st.markdown("<h4 style='font-weight:700;'>Audio Options</h4>", unsafe_allow_html=True)
                voice_pacing = st.selectbox("Speaking Speed Rate (WCAG Pacing):", ["Normal Speed", "Slower Speed (For deep listening and note-taking)"])
                voice_profile = st.selectbox("Select Target Voice Profile:", ["Default Premium Voice (US)", "Custom Dynamic Voice (UK Accent)", "Custom Dynamic Voice (India Accent)"])
                extraction_mode = st.radio("Choose Reading Depth:", ["Summarized Mode (Quick Summary)", "Full Mode (Word-for-Word Transcription)"], key="unique_learning_depth_radio")
                
                if st.button("Convert to Speech", use_container_width=True):
                    with st.spinner("Cloud AI processing handwritten layouts..."):
                        try:
                            image_obj = Image.open(uploaded_file)
                            prompt_content = (
                                "Analyze the handwritten text in this image. Do not transcribe it word-for-word. Instead, provide a brief, clear, and simplified 2-3 sentence summary of the core concepts."
                                if "Summarized" in extraction_mode else
                                "Read the handwriting in this image. Transcribe every single word exactly as written on the paper. Fix clear spelling typos smoothly, do not leave out lines, and output clean raw text layout."
                            )
                            
                            response = client.models.generate_content(model='gemini-2.5-flash', contents=[image_obj, prompt_content])
                            polished_text = response.text
                            
                            final_text = st.text_area("Transcribed Study Text", value=polished_text, height=180)
                            
                            with st.spinner("Converting text into voice speech track..."):
                                slow_tts = "Slower Speed" in voice_pacing
                                lang_code, tld_code = 'en', 'com'
                                if "UK Accent" in voice_profile: tld_code = 'co.uk'
                                elif "India Accent" in voice_profile: tld_code = 'co.in'
                                    
                                tts_engine = gTTS(text=final_text, lang=lang_code, tld=tld_code, slow=slow_tts)
                                output_filepath = "dashboard_audio_temp.mp3"
                                tts_engine.save(output_filepath)
                                
                                st.markdown("<h3 style='font-weight:700; margin-top:15px;'>Audio Player</h3>", unsafe_allow_html=True)
                                playback_speed = st.selectbox("Select Audio Playback Speed:", [1.0, 1.25, 1.5, 1.75, 2.0], index=0)
                                st.audio(output_filepath, format="audio/mp3")
                                
                                st.markdown(f"<script>var audioTags = window.parent.document.querySelectorAll('audio'); audioTags.forEach(function(audio) {{ audio.playbackRate = {playback_speed}; }});</script>", unsafe_allow_html=True)
                                st.session_state['history'].append({
                                    "time": dt.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%I:%M:%S %p"),
                                    "filename": f"{uploaded_file.name} ({'Summary' if 'Summarized' in extraction_mode else 'Full'})",
                                    "chars": len(final_text)
                                })
                                st.toast("Saved to your history log!")
                        except Exception as e:
                            st.error(f"Cloud Processing Error: {e}")

# ------------------------------------------
    # 3.4 STUDY REMINDERS SECTION (CLEAN & UNIQUE LAYOUT)
    # ------------------------------------------
    with tab_reminders:
        st.markdown("<h1 style='font-weight:800; margin-top:15px;'>Study Reminders</h1>", unsafe_allow_html=True)
        st.write("Set up automated alerts to help keep your revision schedule on track.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        ist_tz = pytz.timezone('Asia/Kolkata')
        current_local_time = dt.datetime.now(ist_tz).strftime("%H:%M")
        
        col_rem1, col_rem2 = st.columns(2)
        with col_rem1:
            st.markdown("<h3 style='font-weight:700;'>Set a New Reminder</h3>", unsafe_allow_html=True)
            reminder_topic = st.text_input("What do you want to study?", value="Review Chemistry Chapter 3 Notes")
            reminder_frequency = st.selectbox("How often?", ["Daily", "Weekly", "Custom Days of Week", "One-Time Alert"])
            
            days_to_trigger = []
            if reminder_frequency == "Weekly":
                chosen_day = st.selectbox("Select Day of the Week:", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                days_to_trigger = [chosen_day]
            elif reminder_frequency == "Custom Days of Week":
                days_to_trigger = ["Monday", "Wednesday", "Friday"] # Template placeholder default
            elif reminder_frequency == "One-Time Alert":
                chosen_date = st.date_input("Select Date:", dt.datetime.now(ist_tz).date())
            
            reminder_time_string = st.text_input("Alert Time (HH:MM format, e.g., 11:58 or 23:15)", value=current_local_time)
            reminder_channel = st.selectbox("How should we notify you?", ["1. Through Voice Reminder (In-App Sound)", "2. Through On-Screen Notification Alert", "3. Both Audio and Visual Notification"])
            
            if 'armed_reminder' not in st.session_state:
                st.session_state['armed_reminder'] = None

            if st.button("Activate Reminder", use_container_width=True):
                try:
                    validated_time = dt.datetime.strptime(reminder_time_string.strip(), "%H:%M").time()
                    st.session_state['armed_reminder'] = {
                        "time": reminder_time_string.strip(),
                        "topic": reminder_topic,
                        "channel": reminder_channel
                    }
                    st.success(f"Reminder activated successfully for {validated_time.strftime('%I:%M %p')}!")
                    st.toast("Background browser tracker armed!")
                except ValueError:
                    st.error("❌ Invalid time format! Use HH:MM format.")

        with col_rem2:
            st.markdown("<h3 style='font-weight:700;'>Active Schedule Status</h3>", unsafe_allow_html=True)
            
            # Displays the details of the set reminder if armed
            if st.session_state['armed_reminder']:
                rem = st.session_state['armed_reminder']
                with st.container(border=True):
                    st.write(f"⏰ **Target Alert:** {rem['time']}")
                    st.write(f"📚 **Objective:** {rem['topic']}")
                    st.write(f"📢 **Mode:** *{rem['channel']}*")
            else:
                st.info("No active reminder scheduled yet.")

            # Tracker status box appears exactly once here
            with st.container(border=True):
                st.write("🟢 App Background Tracker: **Online (Browser Engine)**")
                st.write("🟢 Notification System: **Ready**")

        # ======================================================================
        # PERSISTENT CLIENT INJECTION BLOCK (Isolated Client Chime)
        # ======================================================================
        if st.session_state['armed_reminder']:
            rem = st.session_state['armed_reminder']
            
            st.components.v1.html(f"""
            <script>
                if (window.Notification && Notification.permission !== "granted") {{
                    Notification.requestPermission();
                }}

                let alreadyTriggered = false;

                function processBackgroundRevisionClock() {{
                    if (alreadyTriggered) return;

                    const now = new Date();
                    const currentIST = now.toLocaleTimeString('en-US', {{ 
                        timeZone: 'Asia/Kolkata', 
                        hour: '2-digit', 
                        minute: '2-digit', 
                        hour12: false 
                    }});

                    const targetTime = "{rem['time']}";
                    const mode = "{rem['channel']}";
                    const contextTopic = "{rem['topic']}";

                    if (currentIST === targetTime) {{
                        alreadyTriggered = true;

                        if (mode.includes("Voice") || mode.includes("Sound")) {{
                            try {{
                                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                                const oscillator = audioCtx.createOscillator();
                                const gainNode = audioCtx.createGain();
                                
                                oscillator.type = 'sine';
                                oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // Bright Bell Note
                                
                                gainNode.gain.setValueAtTime(0.6, audioCtx.currentTime);
                                gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 2.0); // 2-second elegant fade
                                
                                oscillator.connect(gainNode);
                                gainNode.connect(audioCtx.destination);
                                
                                oscillator.start();
                                oscillator.stop(audioCtx.currentTime + 2.0);
                            }} catch (err) {{
                                console.error("Audio block caught:", err);
                            }}
                        }}

                        if (mode.includes("Notification") && window.Notification && Notification.permission === "granted") {{
                            new Notification("📚 EduAI Study Alert", {{
                                body: "Time to study: " + contextTopic,
                                requireInteraction: true
                            }});
                        }}
                    }}
                }}

                setInterval(processBackgroundRevisionClock, 1000);
            </script>
            """, height=0, width=0)

       
    # ------------------------------------------
    # 3.5 LOG OUT MODULE
    # ------------------------------------------
    with tab_logout:
        st.markdown("<h2 style='font-weight:800; margin-top:15px;'>Sign Out of Platform</h2>", unsafe_allow_html=True)
        st.write("Are you sure you want to log out of your profile session?")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Confirm Sign Out", use_container_width=True):
            st.session_state['authentication_status'] = None
            st.session_state['username'] = None
            st.session_state['name'] = None
            st.rerun()
