import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta
import tempfile
import streamlit as st

# ---------------------------------------------------------
# Path Setup: Add backend to sys.path and set working dir
# ---------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    os.chdir(BACKEND_DIR)
except Exception as e:
    pass

# Ensure captures directory exists
CAPTURES_DIR = os.path.join(BACKEND_DIR, "captures")
os.makedirs(CAPTURES_DIR, exist_ok=True)

# ---------------------------------------------------------
# Database & Backend Imports
# ---------------------------------------------------------
from app.database.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.incident import Incident
from app.models.emergency_contact import EmergencyContact
from app.auth.hashing import hash_password, verify_password
from app.services.alert_service import send_fall_alert_email

from app.services.contact_service import create_contact, get_contacts, delete_contact, update_contact
from app.services.incident_service import create_incident, get_incidents

# Ensure Database Tables Exist
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error(f"Database initialization warning: {e}")

# ---------------------------------------------------------
# Streamlit Page Config & Custom Glassmorphism CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="GuardianAI | Fall Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Dark Theme Core Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Gradient Banner */
    .header-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .header-title {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .header-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 4px;
    }

    /* Metric Cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .metric-val {
        font-size: 28px;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 8px;
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Status Badges */
    .status-badge-active {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    .status-badge-alert {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* Custom Alert Box */
    .alert-banner {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 2px solid #ef4444;
        color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.5);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# Load AI Models with Streamlit Caching
# ---------------------------------------------------------
@st.cache_resource
def load_ai_models():
    """Load YOLO Person Detector and MediaPipe Pose Estimator models"""
    try:
        from app.ai.detector import PersonDetector
        from app.ai.pose import PoseEstimator
        detector = PersonDetector()
        pose = PoseEstimator()
        return detector, pose
    except Exception as e:
        st.error(f"Error loading AI detection models: {e}")
        return None, None

detector, pose = load_ai_models()

# ---------------------------------------------------------
# Session State & DB Helper Functions
# ---------------------------------------------------------
if "user_id" not in st.session_state:
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        # Create default demo user if DB is empty
        user = User(
            full_name="Ashish Kumar",
            email="ashish@gmail.com",
            hashed_password=hash_password("NewPassword@123"),
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)
    st.session_state.user_id = user.id
    st.session_state.user_name = user.full_name
    st.session_state.user_email = user.email
    db.close()

if "last_fall_time" not in st.session_state:
    st.session_state.last_fall_time = 0

def get_current_user(db):
    return db.query(User).filter(User.id == st.session_state.user_id).first()

# ---------------------------------------------------------
# Header & Navigation Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ **GuardianAI**")
    st.caption("AI-Powered Real-time Fall Detection")
    st.divider()

    nav_option = st.radio(
        "Navigation",
        [
            "📹 Live Fall Detection",
            "📊 Dashboard & Analytics",
            "🖼️ Incident Snapshots",
            "☎️ Emergency Contacts",
            "⚙️ Detection Settings",
            "👤 Account Profile"
        ],
        index=0
    )

    st.divider()
    st.markdown("### ⚙️ Live Model Tuning")
    angle_thresh = st.slider("Body Angle Threshold (°)", 30.0, 75.0, 55.0, 1.0)
    speed_thresh = st.slider("Hip Speed Threshold", 0.05, 0.60, 0.20, 0.01)
    fall_time_thresh = st.slider("Fall Duration Time (s)", 0.3, 3.0, 0.8, 0.1)
    conf_thresh = st.slider("YOLO Confidence", 0.3, 0.9, 0.5, 0.05)

    st.divider()
    show_box = st.checkbox("Draw YOLO Bounding Box", value=True)
    show_skeleton = st.checkbox("Draw MediaPipe Skeleton", value=True)
    show_hud = st.checkbox("Show Posture Stats Overlay", value=True)

# Header Display
st.markdown(
    f"""
    <div class="header-banner">
        <div>
            <div class="header-title">GuardianAI Safeguard Console</div>
            <div class="header-subtitle">Continuous Real-Time Fall Monitoring & Automated Emergency Response</div>
        </div>
        <div>
            <span class="status-badge-active">● SYSTEM ACTIVE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# PAGE 1: 📹 LIVE FALL DETECTION
# ---------------------------------------------------------
if nav_option == "📹 Live Fall Detection":
    st.markdown("### 📹 Real-Time Fall Detection Stream")
    
    col_input, col_stats = st.columns([3, 1])

    with col_input:
        source_mode = st.radio(
            "Select Video Source",
            ["System Webcam (Local)", "Browser Webcam (Web)", "Upload Video File"],
            horizontal=True
        )

        video_path = None
        if source_mode == "Upload Video File":
            uploaded_file = st.file_uploader("Upload video file (MP4, AVI, MOV)", type=["mp4", "avi", "mov"])
            if uploaded_file:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(uploaded_file.read())
                video_path = tfile.name

        run_stream = st.toggle("🔴 Activate Continuous Fall Monitoring", value=False, key="run_stream_toggle")

    with col_stats:
        st.markdown("#### Live Telemetry")
        status_box = st.empty()
        status_box.info("System Ready")
        
        telemetry_box = st.empty()

    st_frame = st.empty()
    alert_placeholder = st.empty()

    from app.ai.fall_detector import FallDetector

    if source_mode == "Browser Webcam (Web)":
        st.info("📷 Use the browser camera widget below to take snapshots or continuously test fall detection.")
        camera_img = st.camera_input("Browser Camera Feed", key="browser_cam_input")

        if camera_img:
            file_bytes = np.asarray(bytearray(camera_img.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if frame is not None:
                fall_detector = FallDetector()
                fall_detector.ANGLE_THRESHOLD = angle_thresh
                fall_detector.SPEED_THRESHOLD = speed_thresh
                fall_detector.FALL_TIME = fall_time_thresh

                annotated = frame.copy()
                confidence = 0.9

                if detector:
                    results = detector.detect(cv2.resize(frame, (320, 240)))
                    if show_box and results and len(results[0].boxes) > 0:
                        box = results[0].boxes[0]
                        confidence = float(box.conf[0])
                        if confidence >= conf_thresh:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            x1, y1, x2, y2 = x1 * 2, y1 * 2, x2 * 2, y2 * 2
                            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)

                pose_results = pose.process(frame) if pose else None
                if show_skeleton and pose_results:
                    annotated = pose.draw(annotated, pose_results)

                if pose_results:
                    fall_detected, info = fall_detector.detect(pose_results, image_shape=frame.shape[:2])
                else:
                    fall_detected, info = False, {}

                if show_hud and info:
                    angle = info.get("body_angle", 0.0)
                    ydiff = info.get("vertical_distance", 0.0)
                    lying = info.get("lying", False)
                    duration = info.get("duration", 0.0)

                    cv2.putText(annotated, f"Angle: {angle:.1f} deg", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(annotated, f"YDiff: {ydiff:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    color = (0, 0, 255) if lying else (0, 255, 0)
                    cv2.putText(annotated, f"Lying: {lying}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                if fall_detected:
                    cv2.putText(annotated, "FALL DETECTED!", (140, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    status_box.markdown('<div class="status-badge-alert">🚨 FALL DETECTED!</div>', unsafe_allow_html=True)
                    alert_placeholder.markdown(
                        """
                        <div class="alert-banner">
                            <h2 style="margin:0;">🚨 CRITICAL FALL DETECTED!</h2>
                            <p style="margin:4px 0 0 0;">Immediate emergency response protocol activated.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    status_box.markdown('<span class="status-badge-active">● Pose Analyzed: Normal</span>', unsafe_allow_html=True)

                if info:
                    telemetry_box.markdown(
                        f"""
                        **Body Angle:** {info.get('body_angle', 0.0):.1f}°  
                        **Hip Velocity:** {info.get('hip_speed', 0.0):.2f}  
                        **Posture:** {"🔴 Lying Down" if info.get('lying') else "🟢 Upright"}
                        """
                    )

                st_frame.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

    elif run_stream:
        fall_detector = FallDetector()
        fall_detector.ANGLE_THRESHOLD = angle_thresh
        fall_detector.SPEED_THRESHOLD = speed_thresh
        fall_detector.FALL_TIME = fall_time_thresh

        # Helper function for opening system webcam
        def init_camera():
            if source_mode == "Upload Video File":
                if not video_path:
                    return None
                return cv2.VideoCapture(video_path)
            
            # Try DirectShow on Windows first for fast startup
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap or not cap.isOpened():
                cap = cv2.VideoCapture(0)
            if not cap or not cap.isOpened():
                cap = cv2.VideoCapture(1)
            
            if cap and cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap

        cap = init_camera()

        if not cap or not cap.isOpened():
            st.error("❌ Failed to open video source/webcam. Make sure your camera is connected and not in use by another app (e.g. Zoom/Teams). Try switching to 'Browser Webcam (Web)'.")
        else:
            frame_count = 0
            last_results = None
            prev_time = time.time()

            db = SessionLocal()
            user = get_current_user(db)
            contacts = get_contacts(db, user)

            st.toast("🚀 Fall Detection Stream Activated!")

            while st.session_state.get("run_stream_toggle", False) and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    st.info("Video stream completed.")
                    break

                frame = cv2.resize(frame, (640, 480))
                frame_count += 1

                # Run YOLO detector every 5 frames for high FPS
                if detector and (frame_count % 5 == 0 or last_results is None):
                    small_frame = cv2.resize(frame, (320, 240))
                    last_results = detector.detect(small_frame)

                annotated = frame.copy()
                confidence = 0.9

                if show_box and last_results and len(last_results[0].boxes) > 0:
                    box = last_results[0].boxes[0]
                    confidence = float(box.conf[0])
                    if confidence >= conf_thresh:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        x1, y1, x2, y2 = x1 * 2, y1 * 2, x2 * 2, y2 * 2
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)

                # MediaPipe Pose Processing
                pose_results = pose.process(frame) if pose else None
                if show_skeleton and pose_results:
                    annotated = pose.draw(annotated, pose_results)

                # Fall Detection Logic
                if pose_results:
                    fall_detected, info = fall_detector.detect(pose_results, image_shape=frame.shape[:2])
                else:
                    fall_detected, info = False, {}

                # Render Telemetry Overlay on Image
                if show_hud and info:
                    angle = info.get("body_angle", 0.0)
                    ydiff = info.get("vertical_distance", 0.0)
                    lying = info.get("lying", False)
                    duration = info.get("duration", 0.0)

                    cv2.putText(annotated, f"Angle: {angle:.1f} deg", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(annotated, f"YDiff: {ydiff:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    color = (0, 0, 255) if lying else (0, 255, 0)
                    cv2.putText(annotated, f"Lying: {lying}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(annotated, f"Duration: {duration:.1f}s", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                # FPS counter
                curr_time = time.time()
                fps = 1 / max(1e-5, curr_time - prev_time)
                prev_time = curr_time
                cv2.putText(annotated, f"FPS: {fps:.1f}", (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                # Trigger Fall Action
                if fall_detected:
                    cv2.putText(annotated, "FALL DETECTED!", (140, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    status_box.markdown('<div class="status-badge-alert">🚨 FALL DETECTED!</div>', unsafe_allow_html=True)
                    
                    alert_placeholder.markdown(
                        """
                        <div class="alert-banner">
                            <h2 style="margin:0;">🚨 CRITICAL FALL DETECTED!</h2>
                            <p style="margin:4px 0 0 0;">Immediate emergency response protocol activated. Notifying emergency contacts.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Save snapshot & record incident if interval passed (10s debounce)
                    if curr_time - st.session_state.last_fall_time > 10.0:
                        st.session_state.last_fall_time = curr_time
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"fall_{timestamp_str}.jpg"
                        image_path = os.path.join(CAPTURES_DIR, filename)

                        cv2.imwrite(image_path, annotated)

                        try:
                            inc = create_incident(db=db, user=user, confidence=confidence, image_path=image_path)
                            st.toast(f"✅ Incident recorded in database! (ID: #{inc.id})")

                            # Dispatch Emergency Emails
                            for contact in contacts:
                                if contact.email:
                                    send_fall_alert_email(
                                        to_email=contact.email,
                                        recipient_name=contact.name,
                                        user_name=user.full_name,
                                        incident_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        confidence=confidence,
                                        image_path=image_path
                                    )
                                    st.toast(f"📩 Alert email sent to {contact.name} ({contact.email})")
                        except Exception as e:
                            st.error(f"Error handling fall incident: {e}")
                else:
                    status_box.markdown('<span class="status-badge-active">● Monitoring Normal</span>', unsafe_allow_html=True)

                # Update Telemetry Sidebar Box
                if info:
                    telemetry_box.markdown(
                        f"""
                        **Body Angle:** {info.get('body_angle', 0.0):.1f}°  
                        **Hip Velocity:** {info.get('hip_speed', 0.0):.2f}  
                        **Posture:** {"🔴 Lying Down" if info.get('lying') else "🟢 Upright"}  
                        **Duration:** {info.get('duration', 0.0):.1f}s  
                        **FPS:** {fps:.1f}
                        """
                    )

                # Display Frame in Streamlit
                st_frame.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

            cap.release()
            db.close()


# ---------------------------------------------------------
# PAGE 2: 📊 DASHBOARD & ANALYTICS
# ---------------------------------------------------------
elif nav_option == "📊 Dashboard & Analytics":
    st.markdown("### 📊 GuardianAI Overview & Analytics")

    db = SessionLocal()
    user = get_current_user(db)
    incidents = get_incidents(db, user)
    contacts = get_contacts(db, user)

    today = datetime.utcnow().date()
    today_incidents = [i for i in incidents if i.detected_at.date() == today]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-lbl">Total Incidents</div>
                <div class="metric-val">{len(incidents)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-lbl">Incidents Today</div>
                <div class="metric-val">{len(today_incidents)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-lbl">Emergency Contacts</div>
                <div class="metric-val">{len(contacts)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-lbl">AI System Status</div>
                <div class="metric-val" style="color:#10b981; font-size:22px;">ONLINE 🟢</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("#### 🕒 Recent Incidents Feed")
    if incidents:
        inc_data = []
        for inc in incidents[:10]:
            inc_data.append({
                "Incident ID": f"#{inc.id}",
                "Time": inc.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
                "AI Confidence": f"{inc.confidence * 100:.1f}%",
                "Snapshot Saved": "Yes 🖼️" if inc.image_path and os.path.exists(inc.image_path) else "No"
            })
        st.dataframe(pd.DataFrame(inc_data), use_container_width=True)
    else:
        st.info("No fall incidents recorded yet. System state is clear.")

    db.close()

# ---------------------------------------------------------
# PAGE 3: 🖼️ INCIDENT SNAPSHOTS GALLERY
# ---------------------------------------------------------
elif nav_option == "🖼️ Incident Snapshots":
    st.markdown("### 🖼️ Captured Fall Incident Snapshots")

    db = SessionLocal()
    user = get_current_user(db)
    incidents = get_incidents(db, user)

    valid_incidents = [i for i in incidents if i.image_path and os.path.exists(i.image_path)]

    if not valid_incidents:
        st.info("No snapshot captures available yet.")
    else:
        cols = st.columns(3)
        for idx, inc in enumerate(valid_incidents):
            col = cols[idx % 3]
            with col:
                img = Image.open(inc.image_path)
                st.image(img, caption=f"Incident #{inc.id} | {inc.detected_at.strftime('%Y-%m-%d %H:%M:%S')}", use_container_width=True)
                st.caption(f"Confidence: {inc.confidence*100:.1f}%")
                
                with open(inc.image_path, "rb") as file:
                    st.download_button(
                        label="💾 Download Snapshot",
                        data=file,
                        file_name=os.path.basename(inc.image_path),
                        mime="image/jpeg",
                        key=f"dl_{inc.id}"
                    )

    db.close()

# ---------------------------------------------------------
# PAGE 4: ☎️ EMERGENCY CONTACTS
# ---------------------------------------------------------
elif nav_option == "☎️ Emergency Contacts":
    st.markdown("### ☎️ Emergency Contacts Management")
    st.caption("GuardianAI will dispatch instant email/SMS alerts to these contacts whenever a fall is detected.")

    db = SessionLocal()
    user = get_current_user(db)

    tab_list, tab_add = st.tabs(["📋 Registered Contacts", "➕ Add New Contact"])

    with tab_list:
        contacts = get_contacts(db, user)
        if not contacts:
            st.warning("No emergency contacts registered yet. Add one below to receive fall alerts.")
        else:
            for contact in contacts:
                with st.expander(f"👤 {contact.name} ({contact.relationship or 'Contact'}) - Priority {contact.priority}"):
                    st.write(f"**Phone:** {contact.phone or 'N/A'}")
                    st.write(f"**Email:** {contact.email or 'N/A'}")
                    st.write(f"**Priority Level:** {contact.priority}")

                    col_del, col_test = st.columns([1, 2])
                    with col_del:
                        if st.button(f"🗑️ Delete", key=f"del_{contact.id}"):
                            delete_contact(db, user, contact.id)
                            st.success(f"Deleted contact {contact.name}")
                            st.rerun()
                    with col_test:
                        if contact.email and st.button(f"📩 Send Test Email Alert", key=f"test_{contact.id}"):
                            res = send_fall_alert_email(
                                to_email=contact.email,
                                recipient_name=contact.name,
                                user_name=user.full_name,
                                incident_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                confidence=0.98,
                                image_path=None
                            )
                            if res:
                                st.success(f"Test email sent successfully to {contact.email}!")
                            else:
                                st.error("Failed to send test email. Check .env SMTP credentials.")

    with tab_add:
        with st.form("add_contact_form"):
            name = st.text_input("Full Name *")
            relationship = st.text_input("Relationship (e.g. Spouse, Son, Doctor)")
            phone = st.text_input("Phone Number")
            email = st.text_input("Email Address *")
            priority = st.number_input("Priority Order (1 = Highest)", min_value=1, max_value=10, value=1)

            submitted = st.form_submit_button("Save Contact")
            if submitted:
                if not name or not email:
                    st.error("Name and Email are required!")
                else:
                    class ContactSchema:
                        pass
                    c_obj = ContactSchema()
                    c_obj.name = name
                    c_obj.relationship = relationship
                    c_obj.phone = phone
                    c_obj.email = email
                    c_obj.priority = priority

                    create_contact(db, user, c_obj)
                    st.success(f"Emergency contact '{name}' added successfully!")
                    st.rerun()

    db.close()

# ---------------------------------------------------------
# PAGE 5: ⚙️ DETECTION SETTINGS
# ---------------------------------------------------------
elif nav_option == "⚙️ Detection Settings":
    st.markdown("### ⚙️ Fall Detection AI Engine Configuration")
    
    st.info("GuardianAI utilizes a dual-stage architecture combining Ultralytics YOLO (Person Bounding Box Tracking) and MediaPipe Pose (33 3D Skeleton Keypoints).")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Algorithmic Parameters")
        st.write(f"• **Body Angle Threshold:** {angle_thresh}°")
        st.write(f"• **Hip Downward Velocity Threshold:** {speed_thresh}")
        st.write(f"• **Fall Confirmation Window:** {fall_time_thresh}s")
        st.write(f"• **YOLO Minimum Confidence:** {conf_thresh}")

    with col2:
        st.markdown("#### Hardware acceleration")
        import torch
        device_name = "NVIDIA CUDA GPU 🚀" if torch.cuda.is_available() else "CPU Execution 💻"
        st.write(f"• **Execution Engine:** {device_name}")
        st.write("• **Model Weights Loaded:** `yolo11n.pt` & `MediaPipe Pose`")

# ---------------------------------------------------------
# PAGE 6: 👤 ACCOUNT PROFILE
# ---------------------------------------------------------
elif nav_option == "👤 Account Profile":
    st.markdown("### 👤 User Account Profile")
    
    db = SessionLocal()
    user = get_current_user(db)
    
    if user:
        st.write(f"**Name:** {user.full_name}")
        st.write(f"**Email:** {user.email}")
        st.write(f"**Account Status:** Active 🟢")
        st.write(f"**Created At:** {user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'}")
    db.close()

st.divider()
st.caption("GuardianAI Fall Detection System © 2026. Built with Streamlit, FastAPI, YOLO & MediaPipe.")
