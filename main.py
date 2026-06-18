import streamlit as st
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXCERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.excercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import os
from services.vision.excercise_video_processor import VideoProcessorClass
import time
from services.tracking.metrics import sync_metrics_update
from services.persistence.excercise_repository import _get_users_excercises
import pandas as pd
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
def main():
    st.set_page_config(
        page_icon="🏋️‍♂️",
        page_title="Ai Real time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered",
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")
    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY","")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]

            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            st.session_state.voice_pipeline = None

    header_col1, header_col2 = st.columns([8,2])

    with header_col1:
        st.title("AI Real-time GYM Coach")

    with header_col2:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("AI Coach")

        if st.session_state.username:
            st.caption(f"Logged in as: {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_excercise = st.selectbox("Excercise", EXCERCISE_OPTIONS, key="plan_exercise")
            plan_sets = st.number_input("Number of Sets", min_value=1, max_value=10, key="plan_sets", step=1)
            plan_reps = st.number_input("Reps per Set", min_value=1, max_value=100, key="plan_reps", step=1)

            st.markdown("")

            start_session_button=st.button("Start Session", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.excercise_type=plan_excercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        excercise=plan_excercise,
                        metrics={}
                    )

                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_completed = False
                st.rerun()
        else:
            excercise = st.session_state.get("excercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{excercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", width="stretch", key="end_session_button")

            if end_session_button:
                st.session_state["workout_started"] = False
                
                if  st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        excercise=plan_excercise,
                        metrics={}
                    )

                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()
        
        if workout_started:
            st.divider()

            excercise = st.session_state.get("excercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")
            st.subheader("Current Workout Status")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if excercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric(
                    "Knee Angle",
                    st.session_state.get("knee_angle", 0)
                )
                st.metric(
                    "Back Angle",
                    st.session_state.get("back_angle", 0)
                )
                st.metric(
                    "Depth Status",
                    st.session_state.get("depth_status", 0)
                )
#                 st.metric(
#     "Knee Angle",
#     f"{st.session_state.knee_angle}"
# )
                # st.metric("Back Angle", f"{st.session_state.back_angle}")
                # st.metric("Depth Status", st.session_state.depth_status)

            elif excercise == "Push-ups":
                st.subheader("Push-ups Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif excercise == "Biceps Curls(Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)
            
            elif excercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif excercise == "Lunges":
                st.subheader("Lungs Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}")
                st.metric("Torso Angle", st.session_state.torso_angle)
                st.metric("Balance Status", st.session_state.balance_status)

   

    st.markdown("### Real-time pose detection with proactive AI voice coaching")

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"**Coach:** {st.session_state.coach_feedback}")


    if not workout_started:
        st.markdown(
            """"
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
            ">
            <h2 style="color: #ccc; margin-bottom:8px">Set your workout plan</h2>
            <p style="font-size:1.05rem;">Choose your excercise, sets and reps in the sidebar, <br>
                    then click <strong>Start Workout</strong> to activate the camera and AI Coaching Assistant
            </p>
            </div>
            """, unsafe_allow_html=True,
        )

    else:
        context = webrtc_streamer(
            key="excercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers":[{"urls":["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video":True,
                "audio":False
            },
            async_processing=True
            
        )
        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()
        inject_webrtc_styles()

    st.divider()
    
    st.markdown("### Workout History")

    user_id = st.session_state.get("user_id",0)

    if isinstance(user_id, int) and user_id > 0:
        history_rows = _get_users_excercises(user_id)

        arr=[
            {
                "Excercise":row['excercise_name'],
                "Reps":row['reps'],
                "Sets":row['sets'],
                "Time (sec)":row['time'],
                "Date":row['created_at'],
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Excercise", "Date"]).agg({
                "Reps":'sum',
                "Sets":'sum',
                "Time (sec)":"sum"
            }).reset_index()
            agg_df.index += 1
            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found")
if __name__ =="__main__":
    main()
