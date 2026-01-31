# D:\jan-contract\components\video_recorder.py

import os
import streamlit as st
import datetime
import streamlit.components.v1 as components

VIDEO_CONSENT_DIR = "video_consents"
os.makedirs(VIDEO_CONSENT_DIR, exist_ok=True)

def record_consent_video():
    """
    Production-grade Video Recorder using RecordRTC.
    Features:
    - Camera Selection (Fixes 'wrong camera' issues)
    - RecordRTC Library (Handles cross-browser compatibility)
    - Client-side Encoding (Works on Vercel/Heroku)
    """

    st.markdown("### 📹 Record Video Consent")
    st.info("Ensure you grant camera permissions when prompted by your browser.")

    # We use RecordRTC via CDN for maximum robustness
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <script src="https://www.WebRTC-Experiment.com/RecordRTC.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: transparent; }
            .container { text-align: center; max-width: 640px; margin: auto; }
            
            video { 
                width: 100%; 
                border-radius: 8px; 
                background: #000; 
                margin-bottom: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            
            select {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ccc;
                margin-bottom: 15px;
                width: 100%;
                font-size: 14px;
            }
            
            .btn-group { display: flex; gap: 10px; justify-content: center; margin-top: 10px; }
            
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: 600;
                cursor: pointer;
            }
            
            #btn-start { background: #28a745; }
            #btn-stop { background: #dc3545; }
            #btn-download { background: #007bff; display: none; }
            
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            #status { margin-top: 10px; font-size: 13px; color: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            <select id="video-source"><option value="">Loading cameras...</option></select>
            <video id="preview" autoplay muted playsinline></video>
            
            <div class="btn-group">
                <button id="btn-start">Start Recording</button>
                <button id="btn-stop" disabled>Stop</button>
                <button id="btn-download">Save Video</button>
            </div>
            <div id="status">Ready. Select camera and click Start.</div>
        </div>

        <script>
            const videoElement = document.getElementById('preview');
            const videoSelect = document.getElementById('video-source');
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            const btnDownload = document.getElementById('btn-download');
            const status = document.getElementById('status');
            
            let recorder;
            let stream;

            // 1. Enumerate Cameras
            async function getCameras() {
                try {
                    await navigator.mediaDevices.getUserMedia({ video: true }); // Request permission first
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const videoDevices = devices.filter(device => device.kind === 'videoinput');
                    
                    videoSelect.innerHTML = '';
                    videoDevices.forEach(device => {
                        const option = document.createElement('option');
                        option.value = device.deviceId;
                        option.text = device.label || `Camera ${videoSelect.length + 1}`;
                        videoSelect.appendChild(option);
                    });
                    
                    if(videoDevices.length === 0) {
                         videoSelect.innerHTML = '<option>No cameras found</option>';
                         status.innerText = "Error: No camera devices detected.";
                    }
                } catch (err) {
                    status.innerText = "Error: Permission denied or no camera. " + err.message;
                    videoSelect.innerHTML = '<option>Camera Access Denied</option>';
                }
            }
            getCameras();

            // 2. Start Recording
            btnStart.onclick = async () => {
                const deviceId = videoSelect.value;
                const constraints = {
                    video: { deviceId: deviceId ? { exact: deviceId } : undefined },
                    audio: true
                };

                try {
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    videoElement.srcObject = stream;
                    videoElement.muted = true; // Avoid feedback
                    
                    recorder = new RecordRTC(stream, {
                        type: 'video',
                        mimeType: 'video/webm;codecs=vp8',
                        disableLogs: false
                    });
                    
                    recorder.startRecording();
                    
                    btnStart.disabled = true;
                    btnStop.disabled = false;
                    btnDownload.style.display = 'none';
                    status.innerText = "Recording... Speak clearly.";
                    
                } catch (err) {
                    status.innerText = "Failed to start: " + err.message;
                    console.error(err);
                }
            };

            // 3. Stop Recording
            btnStop.onclick = () => {
                recorder.stopRecording(() => {
                    const blob = recorder.getBlob();
                    const url = URL.createObjectURL(blob);
                    
                    btnStart.disabled = false;
                    btnStop.disabled = true;
                    btnDownload.style.display = 'inline-block';
                    status.innerText = "Recording finished. Download to save.";
                    
                    // Stop stream
                    stream.getTracks().forEach(track => track.stop());
                    videoElement.srcObject = null;
                    
                    // Setup Download
                    btnDownload.onclick = () => {
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = 'recorded_consent.webm';
                        document.body.appendChild(a);
                        a.click();
                        setTimeout(() => {
                            document.body.removeChild(a);
                            window.URL.revokeObjectURL(url);
                        }, 100);
                        status.innerText = "File kept. Now upload below.";
                    };
                });
            };
        </script>
    </body>
    </html>
    """
    
    # Height 600 to accommodate camera dropdown
    components.html(html_code, height=600)

    st.write("---")
    st.markdown("### 📤 Upload Your Recording")
    st.caption("Once you've saved the video above, upload it here to confirm.")
    
    uploaded_file = st.file_uploader("Drop your recorded video here", type=["webm", "mp4", "mov"])
    if uploaded_file is not None:
        try:
             # Process the uploaded file
             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
             ext = os.path.splitext(uploaded_file.name)[1] or ".webm"
             video_filename = os.path.join(VIDEO_CONSENT_DIR, f"consent_upload_{timestamp}{ext}")
             
             with open(video_filename, "wb") as f:
                 f.write(uploaded_file.getbuffer())
             
             st.success("✅ Consent Video Received!")
             st.video(video_filename)
             return video_filename
        except Exception as e:
            st.error(f"Error saving file: {e}")
            return None
            
    return None
