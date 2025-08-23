# D:\jan-contract\components\video_recorder.py

import os
import streamlit as st
import datetime
import av

from streamlit_webrtc import webrtc_streamer, WebRtcMode

VIDEO_CONSENT_DIR = "video_consents"
os.makedirs(VIDEO_CONSENT_DIR, exist_ok=True)

def record_consent_video():
    """
    Encapsulates the video recording logic using the component's internal state.
    
    The video is automatically saved when the user clicks the "STOP" button
    on the webrtc component.
    
    Returns:
        str | None: The file path of the saved video, or None if not saved yet.
    """
    # Instructions for the new, more intuitive workflow
    st.info("Instructions: Click START, record your consent, then click STOP to finalize.")

    webrtc_ctx = webrtc_streamer(
        key="video-consent-recorder",
        mode=WebRtcMode.SENDRECV, # SENDRECV mode is needed for the stop-button-triggered callback
        media_stream_constraints={"video": True, "audio": True},
        video_receiver_size=256,
        async_processing=True,
    )

    # This block executes ONLY when the component is running (after START is clicked)
    if webrtc_ctx.state.playing and webrtc_ctx.video_receiver:
        # Inform the user that recording is in progress
        st.success("🔴 Recording in progress...")
        
        # If the 'frames_buffer' is not in session state, initialize it
        if "frames_buffer" not in st.session_state:
            st.session_state.frames_buffer = []
        
        # Append each new frame to our session state buffer
        while True:
            try:
                frame = webrtc_ctx.video_receiver.get_frame(timeout=1)
                st.session_state.frames_buffer.append(frame)
            except av.error.TimeoutError:
                break # Break the loop when the stream ends (user clicks STOP)

    # This block executes after the user clicks STOP
    if not webrtc_ctx.state.playing and st.session_state.get("frames_buffer"):
        with st.spinner("Saving your recording..."):
            try:
                video_frames = st.session_state.frames_buffer
                
                # Generate a unique filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = os.path.join(VIDEO_CONSENT_DIR, f"consent_{timestamp}.mp4")

                # Use the av library to write the buffered frames to a video file
                with av.open(video_filename, mode="w") as container:
                    stream = container.add_stream("libx264", rate=24)
                    stream.width = video_frames[0].width
                    stream.height = video_frames[0].height
                    stream.pix_fmt = "yuv420p"

                    for frame in video_frames:
                        packet = stream.encode(frame)
                        container.mux(packet)
                    
                    # Flush the stream
                    packet = stream.encode()
                    container.mux(packet)
                
                # Clear the buffer from session state and return the path
                st.session_state.frames_buffer = [] 
                st.session_state.video_filename = video_filename
                return video_filename

            except Exception as e:
                st.error(f"An error occurred while saving the video: {e}")
                st.session_state.frames_buffer = [] # Clear buffer on error
                return None
    
    return None