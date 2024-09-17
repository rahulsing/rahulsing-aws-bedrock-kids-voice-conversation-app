import base64
import time
from typing import Optional

import streamlit as st
from audio_recorder_streamlit import audio_recorder

import bedrock_ops as bdo
import send_audio_get_transcibe as stt
import text2speech as tts
from constants import (
    AUDIO_FILE_NAME,
    OUTPUT_AUDIO_FILE,
    S3_BUCKET,
    S3_AUDIO_KEY,
    S3_TRANSCRIPTION_KEY,
    LANGUAGE_CODE,
)

st.markdown(
    """
    <style>
    .center-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def autoplay_audio(file_path: str) -> None:
    """
    Create an auto-playing audio element in Streamlit.
    
    Args:
        file_path (str): Path to the audio file.
    """
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio controls autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

def save_audio(audio_bytes: bytes, file_name: str) -> None:
    """
    Save audio bytes to a file.
    
    Args:
        audio_bytes (bytes): Audio data.
        file_name (str): Name of the file to save.
    """
    with open(file_name, "wb") as f:
        f.write(audio_bytes)

def process_audio(audio_bytes: bytes) -> Optional[str]:
    """
    Process the recorded audio and return the AI response.
    
    Args:
        audio_bytes (bytes): Recorded audio data.
    
    Returns:
        Optional[str]: AI-generated response or None if processing fails.
    """
    save_audio(audio_bytes, AUDIO_FILE_NAME)

    if not stt.upload_file(AUDIO_FILE_NAME, S3_BUCKET, S3_AUDIO_KEY):
        st.error("File upload failed")
        return None

    job_name = f"TranscribeJob-{int(time.time())}"
    job_uri = f"s3://{S3_BUCKET}/{S3_AUDIO_KEY}"

    audio2txt_s3_url = stt.transcribe_text_to_voice(
        st, job_name, job_uri, S3_BUCKET, S3_TRANSCRIPTION_KEY, LANGUAGE_CODE
    )

    bucket, key = bdo.extract_s3_bucket_and_key(audio2txt_s3_url)
    prompt = bdo.read_transcribe_output(bucket, key)
    
    return bdo.invoke_bedrock_model(prompt)

def main():
    with st.container():
        st.title("🧑 TaleWeaver: Unleash the Magic of Storytelling!")
        st.write("Hello there, young adventurer! 🌟 Are you ready to embark on an enchanting storytelling journey? Just click on the voice recorder below and whisper your heart's desire. Let me know what kind of story you'd like to hear today, and I'll weave a tale just for you! ✨")
        audio_bytes = audio_recorder()

        if audio_bytes:
            st.snow()
            model_output = process_audio(audio_bytes)

            if model_output:
                success = tts.text_to_speech(model_output, OUTPUT_AUDIO_FILE)

                if success:
                    st.balloons()
                    st.write(model_output)
                    autoplay_audio(OUTPUT_AUDIO_FILE)
                    st.success("Text-to-speech conversion completed successfully.")
                else:
                    st.error("Text-to-speech conversion failed.")

if __name__ == "__main__":
    main()
