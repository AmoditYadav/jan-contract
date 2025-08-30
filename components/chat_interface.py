# D:\jan-contract\components/chat_interface.py

import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import io
import av
import queue
import wave
import threading
import time
import numpy as np
from typing import Optional

from streamlit_webrtc import webrtc_streamer, WebRtcMode

# --- Setup ---
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8

def text_to_speech(text: str) -> bytes:
    """Converts text to an in-memory MP3 file bytes."""
    try:
        audio_io = io.BytesIO()
        tts = gTTS(text=text, lang='en', slow=False)
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return audio_io.read()
    except Exception as e:
        st.error(f"Error during Text-to-Speech: {e}")
        return None

def chat_interface(handler_function, session_state_key: str):
    """
    A reusable component that provides a full Text and Voice chat interface.

    Args:
        handler_function: The function to call with the user's text input.
        session_state_key (str): A unique key to store chat history AND to use
                                 as a base for widget keys.
    """
    st.subheader("💬 Chat via Text")
    
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = []

    for message in st.session_state[session_state_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask a question...", key=f"chat_input_{session_state_key}"):
        st.session_state[session_state_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = handler_function(prompt)
                st.markdown(response)
        
        st.session_state[session_state_key].append({"role": "assistant", "content": response})

    st.divider()

    st.subheader("🎙️ Chat via Voice")
    st.info("🎤 **Instructions:** Click START to begin recording, speak your question clearly, then click STOP.")

    # Initialize session state for voice recording
    voice_key = f"voice_{session_state_key}"
    if f"{voice_key}_frames" not in st.session_state:
        st.session_state[f"{voice_key}_frames"] = []
    if f"{voice_key}_processing" not in st.session_state:
        st.session_state[f"{voice_key}_processing"] = False
    if f"{voice_key}_recording_start" not in st.session_state:
        st.session_state[f"{voice_key}_recording_start"] = None
    if f"{voice_key}_bytes" not in st.session_state:
        st.session_state[f"{voice_key}_bytes"] = 0
    if f"{voice_key}_component_key" not in st.session_state:
        st.session_state[f"{voice_key}_component_key"] = f"voice-chat-{session_state_key}-{int(time.time())}"

    def audio_frame_callback(frame: av.AudioFrame):
        """Callback to collect audio frames during recording"""
        if st.session_state[f"{voice_key}_processing"]:
            try:
                # Resample every frame to 16kHz mono, 16-bit PCM for SR
                resampled = frame.reformat(format="s16", layout="mono", rate=16000)
                chunk = resampled.planes[0].to_bytes()
                st.session_state[f"{voice_key}_frames"].append(chunk)
                st.session_state[f"{voice_key}_bytes"] += len(chunk)
            except Exception as e:
                st.error(f"Error processing audio frame: {e}")

    def process_voice_input():
        """Process the collected audio frames and get response"""
        # Short-audio threshold (~0.5s at 16kHz, 16-bit mono)
        total_bytes = st.session_state.get(f"{voice_key}_bytes", 0)
        if total_bytes < int(16000 * 2 * 0.5):
            st.error("❌ No audio captured or recording too short. Please speak for at least 1 second and try again.")
            st.session_state[f"{voice_key}_frames"] = []
            st.session_state[f"{voice_key}_processing"] = False
            st.session_state[f"{voice_key}_bytes"] = 0
            return

        status_placeholder = st.empty()
        status_placeholder.info("🔄 Processing audio...")

        try:
            # Combine all audio frames (already PCM s16 mono 16kHz)
            audio_data = b"".join(st.session_state[f"{voice_key}_frames"])
            
            # Create WAV file in memory with proper format
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(16000)  # 16kHz
                    wf.writeframes(audio_data)
                wav_buffer.seek(0)
                
                # Use speech recognition with better error handling
                with sr.AudioFile(wav_buffer) as source:
                    # Adjust for ambient noise quickly; avoid long pauses
                    recognizer.adjust_for_ambient_noise(source, duration=0.1)
                    audio = recognizer.record(source)
                
                # Recognize speech with multiple fallbacks
                try:
                    user_input = recognizer.recognize_google(audio, language="en-US")
                except sr.UnknownValueError:
                    try:
                        user_input = recognizer.recognize_google(audio, language="en-GB")
                    except sr.UnknownValueError:
                        st.error("❌ Could not understand the audio. Please speak more clearly and try again.")
                        return
                
                if not user_input.strip():
                    st.error("❌ No speech detected. Please try again.")
                    return
                
                st.write(f"🎤 **You said:** *{user_input}*")
                
                # Get response from handler
                with st.spinner("🤔 Getting response..."):
                    response_text = handler_function(user_input)
                
                st.write(f"🤖 **Assistant says:** *{response_text}*")
                
                # Generate audio response
                with st.spinner("🔊 Generating audio response..."):
                    audio_response = text_to_speech(response_text)
                    if audio_response:
                        st.audio(audio_response, format="audio/mp3", start_time=0)
                        st.success("✅ Audio response generated!")
                
                # Add to chat history
                st.session_state[session_state_key].append({"role": "user", "content": user_input})
                st.session_state[session_state_key].append({"role": "assistant", "content": response_text})

        except sr.RequestError as e:
            st.error(f"❌ Speech recognition service error: {e}")
        except Exception as e:
            st.error(f"❌ Error processing audio: {str(e)}")
        finally:
            # Clear the audio frames
            st.session_state[f"{voice_key}_frames"] = []
            st.session_state[f"{voice_key}_processing"] = False
            st.session_state[f"{voice_key}_bytes"] = 0
            status_placeholder.empty()

    # Create a unique key for each component instance to avoid registration issues
    component_key = st.session_state[f"{voice_key}_component_key"]
    
    # WebRTC streamer with proper error handling and component lifecycle
    try:
        ctx = webrtc_streamer(
            key=component_key,
            mode=WebRtcMode.SENDONLY,
            rtc_configuration={
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                    {"urls": ["stun:stun1.l.google.com:19302"]}
                ]
            },
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={
                "video": False,
                "audio": {
                    "echoCancellation": True,
                    "noiseSuppression": True,
                    "autoGainControl": True
                }
            },
            async_processing=True,
            on_change=lambda: None,  # Prevent component registration issues
        )
        
        # Handle recording state with better feedback
        bytes_captured = st.session_state.get(f"{voice_key}_bytes", 0)
        
        if ctx.state.playing and not st.session_state.get(f"{voice_key}_processing", False):
            st.session_state[f"{voice_key}_processing"] = True
            st.session_state[f"{voice_key}_recording_start"] = time.time()
            st.session_state[f"{voice_key}_frames"] = []
            st.session_state[f"{voice_key}_bytes"] = 0
            st.success("🔴 **Recording started!** Speak your question now...")
            
        elif ctx.state.playing and st.session_state.get(f"{voice_key}_processing", False):
            # Show recording progress
            if st.session_state.get(f"{voice_key}_recording_start"):
                elapsed = time.time() - st.session_state[f"{voice_key}_recording_start"]
                approx_seconds = bytes_captured / (16000 * 2) if bytes_captured else 0
                st.caption(f"🎤 Recording... ~{approx_seconds:.1f}s captured")
        
        # Process audio when recording stops
        if not ctx.state.playing and st.session_state.get(f"{voice_key}_processing", False):
            process_voice_input()
            
    except Exception as e:
        st.error(f"❌ WebRTC Error: {str(e)}")
        st.info("💡 Try refreshing the page or using a different browser (Chrome recommended).")
        
        # Fallback: manual audio input
        st.subheader("🔄 Fallback: Manual Audio Input")
        if st.button("Try Alternative Audio Method", key=f"fallback_{voice_key}"):
            st.info("This feature requires WebRTC support. Please ensure your browser supports WebRTC and try again.")