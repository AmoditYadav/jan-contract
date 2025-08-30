#!/usr/bin/env python3
"""
Jan-Contract App Launcher
This script helps you run the Streamlit app with proper configuration.
"""

import os
import sys
import subprocess
import webbrowser
import time


def check_dependencies():
    """Check if all required dependencies are installed"""
    # Map human/package names to actual importable module names
    required_modules = [
        ("streamlit", "streamlit"),
        ("streamlit-webrtc", "streamlit_webrtc"),
        ("opencv-python-headless", "cv2"),  # import cv2, not opencv_python_headless
        ("av", "av"),
        ("SpeechRecognition", "speech_recognition"),
        ("gTTS", "gtts"),
        ("numpy", "numpy"),
    ]

    missing = []
    for package_label, module_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_label)

    if missing:
        print("❌ Missing dependencies:")
        for package in missing:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False

    print("✅ All dependencies are installed!")
    return True


def check_directories():
    """Check if required directories exist"""
    required_dirs = ['video_consents', 'pdfs_demystify']

    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")

    print("✅ All directories are ready!")


def main():
    print("🚀 Jan-Contract App Launcher")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before running the app.")
        return

    # Check directories
    check_directories()

    print("\n🌐 Starting Streamlit app...")
    print("💡 The app will open in your default browser.")
    print("💡 If it doesn't open automatically, go to: http://localhost:8501")
    print("\n📋 Tips for best experience:")
    print("   - Use Chrome, Firefox, or Edge")
    print("   - Allow camera and microphone permissions")
    print("   - Record videos for at least 2-3 seconds")
    print("   - Speak clearly for voice input")

    # Start the Streamlit app using `python -m streamlit` so PATH is not required
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8501')

        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Run Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'main_streamlit.py',
            '--server.port', '8501',
            '--server.address', 'localhost'
        ])

    except KeyboardInterrupt:
        print("\n👋 App stopped by user.")
    except Exception as e:
        print(f"\n❌ Error starting app: {e}")
        print("💡 Try running manually: python -m streamlit run main_streamlit.py")


if __name__ == "__main__":
    main()
