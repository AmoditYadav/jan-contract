# 🎥 Audio/Video Troubleshooting Guide

## Common Issues and Solutions

### 1. Video Recording Issues

**Problem:** Video recording creates 0-second files or doesn't work at all.

**Solutions:**
- **Browser Compatibility**: Use Chrome, Firefox, or Edge. Safari may have issues.
- **Camera Permissions**: Make sure to allow camera access when prompted.
- **HTTPS Required**: Some browsers require HTTPS for camera access. Use `streamlit run --server.address 0.0.0.0 --server.port 8501` for local testing.
- **Refresh Page**: If buttons don't respond, try refreshing the page.

### 2. Audio Recording Issues

**Problem:** Voice input doesn't work or produces no audio.

**Solutions:**
- **Microphone Permissions**: Allow microphone access when prompted.
- **Browser Settings**: Check browser settings for microphone permissions.
- **Clear Browser Cache**: Clear browser cache and cookies.
- **Try Different Browser**: Some browsers handle WebRTC better than others.

### 3. Dependencies Issues

**Problem:** Import errors or missing modules.

**Solutions:**
```bash
# Install all dependencies
pip install -r requirements.txt

# If you get errors, try installing individually:
pip install streamlit-webrtc
pip install opencv-python-headless
pip install av
pip install SpeechRecognition
pip install gTTS
pip install PyAudio
```

### 4. Windows-Specific Issues

**Problem:** PyAudio installation fails on Windows.

**Solutions:**
```bash
# Try installing PyAudio with pipwin
pip install pipwin
pipwin install pyaudio

# Or download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

### 5. Performance Issues

**Problem:** Slow video/audio processing.

**Solutions:**
- **Reduce Video Quality**: The app uses 640x480 resolution by default.
- **Close Other Apps**: Close other applications using camera/microphone.
- **Check System Resources**: Ensure sufficient RAM and CPU available.

## Testing Your Setup

Run the test script to verify everything is working:

```bash
streamlit run test_audio_video.py
```

This will check:
- ✅ All dependencies are installed
- ✅ Directories are writable
- ✅ Basic functionality

## Browser Requirements

- **Chrome**: Best compatibility
- **Firefox**: Good compatibility
- **Edge**: Good compatibility
- **Safari**: Limited compatibility (not recommended)

## Network Requirements

- **Local Development**: Works fine on localhost
- **Production**: HTTPS required for camera/microphone access
- **Firewall**: Ensure ports 8501 (or your chosen port) is accessible

## Error Messages and Solutions

| Error | Solution |
|-------|----------|
| "Camera not found" | Check camera permissions and browser settings |
| "Microphone not found" | Check microphone permissions and browser settings |
| "WebRTC not supported" | Update browser or try different browser |
| "Permission denied" | Allow camera/microphone access in browser |
| "Video file too small" | Record for at least 2-3 seconds |

## Getting Help

If you're still having issues:

1. Check the browser console for JavaScript errors
2. Run the test script: `streamlit run test_audio_video.py`
3. Check if your camera/microphone work in other applications
4. Try a different browser
5. Restart the Streamlit server

## Development Tips

- Use `st.debug()` to add debugging information
- Check `st.session_state` for state management issues
- Monitor browser console for WebRTC errors
- Test on different devices and browsers
