import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db
from database.seed_data import seed_database

init_db()
seed_database()

if 'portal' not in st.session_state:
    st.session_state.portal = None

if st.session_state.portal == 'user':
    from frontend.user_portal import run_user_portal
    run_user_portal()
elif st.session_state.portal == 'admin':
    from frontend.admin_portal import run_admin_portal
    run_admin_portal()
else:
    st.set_page_config(
        page_title="AutoSenseAI",
        page_icon="🚗",
        layout="wide"
    )
    
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 40px 20px;
    }
    .main-title {
        font-size: 48px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .main-subtitle {
        font-size: 20px;
        color: #7f8c8d;
        margin-bottom: 40px;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .portal-btn {
        text-align: center;
        padding: 20px;
    }

    .model-list {
    color: #ffffff;
    border-radius: 10px;
    padding: 22px;
    margin: 18px 0;
    border-left: 4px solid #764ba2;


    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <div class="main-title">AutoSenseAI</div>
        <div class="main-subtitle">
            Autonomous Predictive Maintenance & Smart Breakdown Management Platform
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### Predictive Maintenance
        AI-powered service predictions based on vehicle health, usage patterns, and breakdown history.
        """)
    
    with col2:
        st.markdown("""
        ### Smart Scheduling
        Automatic slot booking with intelligent garage recommendations and alternative date suggestions.
        """)
    
    with col3:
        st.markdown("""
        ### Breakdown Assistance
        Real-time location tracking, nearby garage finder, ETA estimates, and cost predictions.
        """)
    
    with col4:
        st.markdown("""
        ### Analytics Dashboard
        Comprehensive insights on breakdowns, services, garage performance, and fleet health.
        """)
    
    st.markdown("---")
    
    st.markdown("## Select Your Portal")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        portal_col1, portal_col2 = st.columns(2)
        
        with portal_col1:
            st.markdown("""
            ### User Portal
            For vehicle owners to:
            - View vehicle health dashboard
            - Get AI-driven service predictions
            - Schedule services
            - Report breakdowns
            - Track repair status
            """)
            
            if st.button("Enter User Portal", type="primary", use_container_width=True):
                st.session_state.portal = 'user'
                st.rerun()
            
            st.info("Demo: john_user / password123")
        
        with portal_col2:
            st.markdown("""
            ### Admin Portal
            For OEMs & service managers to:
            - Monitor all vehicles & services
            - Manage garages & slots
            - Update parts & pricing
            - View analytics & insights
            - Track agent activity
            """)
            
            if st.button("Enter Admin Portal", type="primary", use_container_width=True):
                st.session_state.portal = 'admin'
                st.rerun()
            
            st.info("Demo: admin / admin123")
    
    # -------------------------------------------------
    # AI MODELS & DATASETS (ADDED – NO OTHER CHANGES)
    # -------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="main-subtitle">AI Models & Datasets</div>', unsafe_allow_html=True)

    model_files = [
        ("Universal Vehicle Dataset", "universal_dataset.csv",
         "Vehicle telematics, maintenance & failure history.",
         "https://drive.google.com/file/d/16KX3wA0OznXbdclD4Do0mGIj7Nf12vYm/view?usp=sharing"),

        ("Risk Score Model", "risk_score_model.pkl",
         "Vehicle risk scoring model.",
         "https://drive.google.com/file/d/1scEeN-V0cXYGZ-w8szfdljkUKEW8xwW4/view?usp=sharing"),

        ("30-Day Engine Failure Model", "engine_failure_30d_model.pkl",
         "Predicts engine failure within 30 days.",
         "https://drive.google.com/file/d/10Ibirt1W5Zv10Dh1-zb2R9hrP6Izh_0j/view?usp=sharing"),

        ("Complete Agent System", "complete_agent_system.pkl",
         "Integrated multi-agent AI system.",
         "https://drive.google.com/file/d/17_puXV0GplEqObBIvUVpvO-1yGcOkIz_/view?usp=sharing"),

        ("Clustering Model", "clustering_model.pkl",
         "Vehicle behavior clustering.",
         "https://drive.google.com/file/d/1q6tS47fFbYRozMI3taWL6uBGGzuffQu2/view?usp=sharing"),

        ("Anomaly Detection Model", "anomaly_detection_model.pkl",
         "Detects abnormal sensor patterns.",
         "https://drive.google.com/file/d/1pqLzWAuQyL_GbCOSSICTIhlHDu1mggZ5/view?usp=sharing"),

        ("Health Score Model", "health_score_model.pkl",
         "Computes overall vehicle health.",
         "https://drive.google.com/file/d/1SUynzGtZu182x_4K3tsTWYoeGaR6hS6I/view?usp=sharing")
    ]

    for name, file, desc, url in model_files:
        st.markdown(f"""
        <div class="model-list">
            <h4>{name}</h4>
            <p><strong>{file}</strong></p>
            <p>{desc}</p>
            <p><a href="{url}" target="_blank">Download Model</a></p>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------
    # AGENTS (UNCHANGED)
    # -------------------------------------------------
    st.markdown("---")
    
    st.markdown("## Agent-Based Architecture")
    
    agents = [
        ("Prediction Agent", "Predicts next service date using ML + rules"),
        ("Alert Agent", "Generates proactive alerts automatically"),
        ("Scheduling Agent", "Finds optimal slots and books services"),
        ("Breakdown Agent", "Handles emergency workflows"),
        ("Location Agent", "Tracks vehicle & garage locations"),
        ("Garage Recommendation", "Finds nearest suitable garages"),
        ("ETA Agent", "Estimates arrival & repair times"),
        ("Pricing Agent", "Calculates repair costs"),
        ("Visualization Agent", "Creates dynamic charts"),
        ("Feedback Agent", "Analyzes service quality")
    ]
    
    cols = st.columns(5)
    for i, (name, desc) in enumerate(agents):
        with cols[i % 5]:
            st.markdown(f"""
            **{name}**
            
            {desc}
            """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 20px;">
        <p>AutoSenseAI - EY Techathon 6.0 | Team Arjuna Automotive</p>
        <p>Built with Streamlit, Flask, SQLAlchemy, and AI Agents</p>
    </div>
    """, unsafe_allow_html=True)
