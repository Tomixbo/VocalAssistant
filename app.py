import streamlit as st
import time
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text, sticky_footer, sticky_header, init_model
import os
from audio_recorder_streamlit import audio_recorder
import base64
import uuid
from streamlit_option_menu import option_menu

# Utiliser st.selectbox pour imiter les onglets dans la barre latérale
# option = st.sidebar.selectbox(":small_red_triangle_down: Choisissez un assistant ", ("INTITIUM", "HUGO"))
option = option_menu(
    menu_title=None,
    options=["HUGO", "INTITIUM"],
    icons=["box-fill","box-seam"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "nav": {"width" : "100%"},
        "nav-link": {"--hover-color" : "#d1cfcfd3"},
        "nav-link-selected": {"background-color" : "#ee5c22d3"}
    }
)


# Define initial messages
message_init_intitium = "Bonjour, comment je peux vous assister?"
message_init_hugo = "Ton assistant vocal spécialisé en comptabilité et fiscalité"

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

def display_assistant(session_key, title, welcome_message, assistant_id, message_init):
    # HEADER STICKY
    with st.container():
        st.title(title)
        st.write(welcome_message)
        sticky_header()
    initialize_session_state(message_init, assistant_id, session_key)

    # PLACEHOLDER FOR MESSAGES
    chat_placeholder = st.container()

    with chat_placeholder:
        for message in st.session_state[f"{session_key}_messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # RERUN APP
    if not st.session_state[f"{session_key}_loaded"]:
        # Introduce a small delay
        time.sleep(1.5)
        st.session_state[f"{session_key}_loaded"] = True
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
            if prompt := st.chat_input("Write your message here...", key=f"{session_key}_input"):
                st.session_state[f"{session_key}_messages"].append({"role": "user", "content": prompt})
                message_status = 1
                with chat_placeholder:
                    with st.chat_message("user"):
                        st.write(prompt)
        with col2:
            st.session_state[f"{session_key}_audio_bytes"] = audio_recorder(text="", icon_size="2x", key=f"{session_key}_audio")

    # SPEECH TO TEXT
    with chat_placeholder: 
        if st.session_state[f"{session_key}_audio_bytes"] and not message_status:
            # Conteneur pour le spinner spécifique
            with st.spinner("Transcribing..."):
                # Write the audio bytes to a temporary file
                webm_file_path = f"temp_audio_{st.session_state[f'{session_key}_session_id']}.mp3"
                with open(webm_file_path, "wb") as f:
                    f.write(st.session_state[f"{session_key}_audio_bytes"])

                # Convert the audio to text using the speech_to_text function
                transcript = speech_to_text(webm_file_path)
                if transcript:
                    with st.chat_message("user"):
                        st.session_state[f"{session_key}_messages"].append({"role": "user", "content": transcript})
                        message_status = 1
                        st.write(transcript)
                        os.remove(webm_file_path)
                st.session_state[f"{session_key}_audio_bytes"] = None

    # RESPONSE
    if st.session_state[f"{session_key}_messages"][-1]["role"] != "assistant":
        with chat_placeholder:
            with st.chat_message("assistant"):
                with st.spinner("Thinking🤔..."):
                    final_response = get_answer(st.session_state[f"{session_key}_messages"][-1]['content'], st.session_state[f"{session_key}_thread"])
                with st.spinner("Generating audio response..."):
                    audio_file = text_to_speech(final_response)
                    autoplay_audio(audio_file)
                st.write(final_response)
                st.session_state[f"{session_key}_messages"].append({"role": "assistant", "content": final_response})
                os.remove(audio_file)
                message_status = None

if option == "INTITIUM":
    display_assistant("intitium", "INTITIUM - Assistant Vocal 🤖", 
                      """
                      Bienvenue, \n
                      Je suis l'assistant vocal qui vous assiste pour l'exécution des actions suivante :\n
                      - Lister les dossiers du cabinet\n
                      - Ajouter un nouveau dossier à traiter pour le cabinet\n
                      \n
                      Appuyez sur l'icone d'enregistrement ou écrire dans la zone de texte pour interagir avec votre assistant.
                      """, st.secrets["ASSISTANT_ID_INTITIUM"], message_init_intitium)

elif option == "HUGO":
    display_assistant("hugo", "HUGO - Assistant Vocal 🤖", 
                      """
                      Bienvenue, \n
                      Je suis votre assistant vocal spécialisé en comptabilité et fiscalité.\n
                      Documents de référence :\n
                      - ACT_180424_120912.pdf => Actualité BOFIP du 12/09/2012 au 18/04/2024\n
                      - MC_2024_XXXX.docx => Mémento 2024 Editions Francis Lefebvre - Comptabilité\n
                      - MF_2024_XXXX.docx => Mémento 2024 Editions Francis Lefebvre - Fiscalité\n
                      Appuyez sur l'icone d'enregistrement ou écrire dans la zone de texte pour interagir avec votre assistant.
                      """, st.secrets["ASSISTANT_ID_HUGO"], message_init_hugo)
