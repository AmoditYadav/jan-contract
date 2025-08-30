# D:\jan-contract\components\video_recorder.py

import os
import streamlit as st
import datetime
import av
import numpy as np
from typing import Optional

from streamlit_webrtc import webrtc_streamer, WebRtcMode

VIDEO_CONSENT_DIR = "video_consents"
os.makedirs(VIDEO_CONSENT_DIR, exist_ok=True)

def record_consent_video():
    """
    Improved video recording component with better error handling and reliability.
    
    Returns:
        str | None: The file path of the saved video, or None if not saved yet.
    """
    st.info("🎥 **Instructions:** Click START to begin recording, speak your consent, then click STOP to save.")
    
    # Initialize session state for video recording
    if "video_frames_buffer" not in st.session_state:
        st.session_state.video_frames_buffer = []
    if "video_recording" not in st.session_state:
        st.session_state.video_recording = False
    if "video_processed" not in st.session_state:
        st.session_state.video_processed = False
    if "recording_start_time" not in st.session_state:
        st.session_state.recording_start_time = None

    def video_frame_callback(frame: av.VideoFrame):
        """Callback to collect video frames during recording"""
        if st.session_state.video_recording:
            try:
                # Convert frame to numpy array for easier handling
                img = frame.to_ndarray(format="bgr24")
                st.session_state.video_frames_buffer.append(img)
            except Exception as e:
                st.error(f"Error processing video frame: {e}")

    # WebRTC streamer configuration
    webrtc_ctx = webrtc_streamer(
        key="video-consent-recorder",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]}
            ]
        },
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640},
                "height": {"ideal": 480},
                "frameRate": {"ideal": 30}
            },
            "audio": False
        },
        video_frame_callback=video_frame_callback,
        async_processing=True,
    )

    # Handle recording state
    if webrtc_ctx.state.playing and not st.session_state.video_recording:
        st.session_state.video_recording = True
        st.session_state.video_processed = False
        st.session_state.recording_start_time = datetime.datetime.now()
        st.session_state.video_frames_buffer = []  # Clear previous buffer
        st.success("🔴 **Recording started!** Speak your consent now...")
        
    elif webrtc_ctx.state.playing and st.session_state.video_recording:
        # Show recording progress
        frames_captured = len(st.session_state.video_frames_buffer)
        if st.session_state.recording_start_time:
            elapsed = (datetime.datetime.now() - st.session_state.recording_start_time).total_seconds()
            st.caption(f"📹 Recording... Frames: {frames_captured} | Duration: {elapsed:.1f}s")

    # Process video when recording stops
    if not webrtc_ctx.state.playing and st.session_state.video_recording and not st.session_state.video_processed:
        st.session_state.video_recording = False
        st.session_state.video_processed = True
        
        with st.spinner("💾 Processing and saving your recording..."):
            try:
                video_frames = st.session_state.video_frames_buffer.copy()
                
                # Enhanced validation
                if len(video_frames) < 30:  # At least 1 second at 30fps
                    st.warning(f"⚠️ Recording too short ({len(video_frames)} frames). Please record for at least 2-3 seconds.")
                    st.session_state.video_frames_buffer = []
                    return None
                
                # Generate unique filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = os.path.join(VIDEO_CONSENT_DIR, f"consent_{timestamp}.mp4")
                
                # Get video dimensions from first frame
                height, width = video_frames[0].shape[:2]
                fps = 30
                
                # Use OpenCV for more reliable video writing
                import cv2
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
                
                # Write frames
                for frame in video_frames:
                    out.write(frame)
                
                out.release()
                
                # Verify the video was created successfully
                if os.path.exists(video_filename) and os.path.getsize(video_filename) > 1000:
                    # Clear the buffer
                    st.session_state.video_frames_buffer = []
                    st.session_state.video_filename = video_filename
                    
                    # Calculate duration
                    duration = len(video_frames) / fps
                    st.success(f"✅ **Video saved successfully!**")
                    st.caption(f"📊 Duration: {duration:.1f}s | Frames: {len(video_frames)} | Size: {os.path.getsize(video_filename)/1024:.1f}KB")
                    
                    return video_filename
                else:
                    st.error("❌ Failed to save video file properly.")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Error saving video: {str(e)}")
                st.session_state.video_frames_buffer = []
                return None
    
    # Show recording status
    if st.session_state.video_recording:
        st.info("🎥 **Recording in progress...** Click STOP when finished.")
    
    return None