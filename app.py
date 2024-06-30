import streamlit as st
import time
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text, sticky_footer, sticky_header
import os
from audio_recorder_streamlit import audio_recorder
import base64

# Initialize session state for managing chat messages
def initialize_session_state(message_init):
    if "messages" not in st.session_state:    
        st.session_state.messages = [{"role": "assistant", "content": message_init}]   
        audio_file = text_to_speech(message_init)
        with open(audio_file, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
        time.sleep(1)
        os.remove(audio_file)   
    if 'audio_bytes' not in st.session_state:
        st.session_state.audio_bytes = None
    if 'loaded' not in st.session_state:
        st.session_state.loaded = False

message_init = "Bonjour, comment je peux vous aider?"
initialize_session_state(message_init)

# Main content container
with st.container():
    st.title("Assistant Vocal 🤖")
    st.write("Bienvenue, appuyez sur l'icone d'enregistrement pour interagir avec votre assistant.")
    sticky_header()

# Placeholder for chat messages
chat_placeholder = st.container()

with chat_placeholder:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


# message status
message_status = None

# Create a container for the sticky footer
footer = st.container()

# Add content to the footer
with footer:
    sticky_footer()

    # Only display the audio recorder after the initial load
    if not st.session_state.loaded:
        # Introduce a small delay
        time.sleep(1)
        st.session_state.loaded = True
        # Ajouter un script JavaScript pour redimensionner la fenêtre après le chargement de la page
        
        st.rerun()
    
    col1, col2= st.columns([11, 1], vertical_alignment="center")
    with col1:
        if prompt := st.chat_input("Write your message here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            message_status = 1
            with chat_placeholder:
                with st.chat_message("user"):
                    st.write(prompt)
    with col2:
        st.session_state.audio_bytes = audio_recorder(text="", icon_size="2x")
    



# Process the recorded audio if available
with chat_placeholder: 
    if st.session_state.audio_bytes and not message_status:
        # Conteneur pour le spinner spécifique
        with st.spinner("Transcribing..."):
            # Write the audio bytes to a temporary file
            webm_file_path = "temp_audio.mp3"
            with open(webm_file_path, "wb") as f:
                f.write(st.session_state.audio_bytes)

            # Convert the audio to text using the speech_to_text function
            transcript = speech_to_text(webm_file_path)
            if transcript:
                with st.chat_message("user"):
                    st.session_state.messages.append({"role": "user", "content": transcript})
                    message_status = 1
                    st.write(transcript)
                    os.remove(webm_file_path)
            st.session_state.audio_bytes = None
             

# RESPONSE
if st.session_state.messages[-1]["role"] != "assistant":
    with chat_placeholder:
        with st.chat_message("assistant"):
            with st.spinner("Thinking🤔..."):
                final_response = get_answer(st.session_state.messages)
            with st.spinner("Generating audio response..."):
                audio_file = text_to_speech(final_response)
                autoplay_audio(audio_file)
            st.write(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            os.remove(audio_file)
            message_status = None


