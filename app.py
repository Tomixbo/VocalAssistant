import streamlit as st
import time
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text, sticky_footer, sticky_header, init_model
import os
from audio_recorder_streamlit import audio_recorder
import base64
import uuid

# FUNCTION INITIALIZE session_state : messages, audio_bytes, loaded
def initialize_session_state(message_init, assistant_id, session_key):
    if f"{session_key}_session_id" not in st.session_state:
        st.session_state[f"{session_key}_session_id"] = str(uuid.uuid4())
    
    if f"{session_key}_messages" not in st.session_state:    
        st.session_state[f"{session_key}_messages"] = [{"role": "assistant", "content": message_init}]   
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
    
    if f"{session_key}_thread" not in st.session_state:
        st.session_state[f"{session_key}_thread"] = init_model(assistant_id)
    else:
        st.session_state[f"{session_key}_thread"] = init_model(assistant_id, st.session_state[f"{session_key}_thread"].id)
    
    if f"{session_key}_audio_bytes" not in st.session_state:
        st.session_state[f"{session_key}_audio_bytes"] = None
    if f"{session_key}_loaded" not in st.session_state:
        st.session_state[f"{session_key}_loaded"] = False

# Create tabs
tab1, tab2 = st.tabs(["Assistant Intitium", "Assistant Hugo"])

# Define initial messages
message_init_intitium = "Bonjour, comment je peux vous aider?"
message_init_hugo = "Ton assistant vocal spécialisé en comptabilité et fiscalité"

with tab1:
    st.title("INITIUM Vocal Assistant 🤖")
    st.write("""
             Bienvenue, \n
             Je suis là en tant qu'assistant vocal qui vous assiste dans l'exécution de quelques actions telles que :\n
             - Lister les dossiers du cabinet\n
             - Ajouter un nouveau dossier à traiter pour le cabinet\n
             \n
             Appuyez sur l'icone d'enregistrement ou écrire dans la zone de texte pour interagir avec votre assistant.
             """)
    sticky_header()
    initialize_session_state(message_init_intitium, st.secrets["ASSISTANT_ID_INTITIUM"], "intitium")

    # PLACEHOLDER FOR MESSAGES
    chat_placeholder = st.container()

    with chat_placeholder:
        for message in st.session_state["intitium_messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # RERUN APP
    if not st.session_state["intitium_loaded"]:
        # Introduce a small delay
        time.sleep(1)
        st.session_state["intitium_loaded"] = True
        st.experimental_rerun()

    # FOOTER CONTAINER
    footer = st.container()
    # init message status
    message_status = None

    # FOOTER STICKY - MESSAGE INPUT - AUDIO RECORDER
    with footer:
        sticky_footer()
        col1, col2 = st.columns([11, 1], vertical_alignment="center")
        with col1:
            if prompt := st.chat_input("Write your message here...", key="intitium_input"):
                st.session_state["intitium_messages"].append({"role": "user", "content": prompt})
                message_status = 1
                with chat_placeholder:
                    with st.chat_message("user"):
                        st.write(prompt)
        with col2:
            st.session_state["intitium_audio_bytes"] = audio_recorder(text="", icon_size="2x", key="intitium_audio")

    # SPEECH TO TEXT
    with chat_placeholder: 
        if st.session_state["intitium_audio_bytes"] and not message_status:
            # Conteneur pour le spinner spécifique
            with st.spinner("Transcribing..."):
                # Write the audio bytes to a temporary file
                webm_file_path = f"temp_audio_{st.session_state['intitium_session_id']}.mp3"
                with open(webm_file_path, "wb") as f:
                    f.write(st.session_state["intitium_audio_bytes"])

                # Convert the audio to text using the speech_to_text function
                transcript = speech_to_text(webm_file_path)
                if transcript:
                    with st.chat_message("user"):
                        st.session_state["intitium_messages"].append({"role": "user", "content": transcript})
                        message_status = 1
                        st.write(transcript)
                        os.remove(webm_file_path)
                st.session_state["intitium_audio_bytes"] = None

    # RESPONSE
    if st.session_state["intitium_messages"][-1]["role"] != "assistant":
        with chat_placeholder:
            with st.chat_message("assistant"):
                with st.spinner("Thinking🤔..."):
                    final_response = get_answer(st.session_state["intitium_messages"][-1]['content'], st.session_state["intitium_thread"])
                with st.spinner("Generating audio response..."):
                    audio_file = text_to_speech(final_response)
                    autoplay_audio(audio_file)
                st.write(final_response)
                st.session_state["intitium_messages"].append({"role": "assistant", "content": final_response})
                os.remove(audio_file)
                message_status = None

with tab2:
    st.title("Ton assistant vocal spécialisé en comptabilité et fiscalité 🤖")
    st.write("""
             Bienvenue, \n
             Je suis là en tant qu'assistant vocal spécialisé en comptabilité et fiscalité,
             Appuyez sur l'icone d'enregistrement ou écrire dans la zone de texte pour interagir avec votre assistant.
             """)
    sticky_header()
    initialize_session_state(message_init_hugo, st.secrets["ASSISTANT_ID_HUGO"], "hugo")

    # PLACEHOLDER FOR MESSAGES
    chat_placeholder = st.container()

    with chat_placeholder:
        for message in st.session_state["hugo_messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # RERUN APP
    if not st.session_state["hugo_loaded"]:
        # Introduce a small delay
        time.sleep(1)
        st.session_state["hugo_loaded"] = True
        st.experimental_rerun()

    # FOOTER CONTAINER
    footer = st.container()
    # init message status
    message_status = None

    # FOOTER STICKY - MESSAGE INPUT - AUDIO RECORDER
    with footer:
        sticky_footer()
        col1, col2 = st.columns([11, 1], vertical_alignment="center")
        with col1:
            if prompt := st.chat_input("Write your message here...", key="hugo_input"):
                st.session_state["hugo_messages"].append({"role": "user", "content": prompt})
                message_status = 1
                with chat_placeholder:
                    with st.chat_message("user"):
                        st.write(prompt)
        with col2:
            st.session_state["hugo_audio_bytes"] = audio_recorder(text="", icon_size="2x", key="hugo_audio")

    # SPEECH TO TEXT
    with chat_placeholder: 
        if st.session_state["hugo_audio_bytes"] and not message_status:
            # Conteneur pour le spinner spécifique
            with st.spinner("Transcribing..."):
                # Write the audio bytes to a temporary file
                webm_file_path = f"temp_audio_{st.session_state['hugo_session_id']}.mp3"
                with open(webm_file_path, "wb") as f:
                    f.write(st.session_state["hugo_audio_bytes"])

                # Convert the audio to text using the speech_to_text function
                transcript = speech_to_text(webm_file_path)
                if transcript:
                    with st.chat_message("user"):
                        st.session_state["hugo_messages"].append({"role": "user", "content": transcript})
                        message_status = 1
                        st.write(transcript)
                        os.remove(webm_file_path)
                st.session_state["hugo_audio_bytes"] = None

    # RESPONSE
    if st.session_state["hugo_messages"][-1]["role"] != "assistant":
        with chat_placeholder:
            with st.chat_message("assistant"):
                with st.spinner("Thinking🤔..."):
                    final_response = get_answer(st.session_state["hugo_messages"][-1]['content'], st.session_state["hugo_thread"])
                with st.spinner("Generating audio response..."):
                    audio_file = text_to_speech(final_response)
                    autoplay_audio(audio_file)
                st.write(final_response)
                st.session_state["hugo_messages"].append({"role": "assistant", "content": final_response})
                os.remove(audio_file)
                message_status = None
