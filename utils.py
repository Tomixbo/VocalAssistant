from openai import OpenAI
import streamlit as st
import base64
import time

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
model = "gpt-4o"

assistant = None
thread = None

def init_model(assistant_id, thread_id=None):
    global assistant  # Déclare la variable assistant comme globale
    global thread    # Déclare la variable thread comme globale

    assistant=client.beta.assistants.retrieve(assistant_id=assistant_id)
    print(f"ASSISTANT::: {assistant.id}")
    if not thread_id:
        thread=client.beta.threads.create()
    else:
        thread=client.beta.threads.retrieve(thread_id=thread_id)
    print(f"THREAD::: {thread.id}")
    return thread


def speech_to_text(audio_data):
    try:
        with open(audio_data, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                response_format="text",
                file=audio_file
            )
        return transcript
    except Exception as e:
        print(e)
        return

def text_to_speech(input_text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=input_text
    )
    webm_file_path = "temp_audio_play.mp3"
    with open(webm_file_path, "wb") as f:
        response.stream_to_file(webm_file_path)
    return webm_file_path

def get_answer(message, thread_):
    
    # === Create a Message ===
    message = client.beta.threads.messages.create(
        thread_id=thread_.id,
        role="user",
        content=message
    )

    # === Run our Assistant ===
    run = client.beta.threads.runs.create(
        thread_id=thread_.id,
        assistant_id=assistant.id,
        instructions=""
    )

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_.id, run_id=run.id)
        print(f"\n RUN STATUS : ---> {run.status}")
        try:
            if run.status == "completed":
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_.id)
                return messages.data[0].content[0].text.value
        except Exception as e:
            print(f"An error occurred while retrieving the run : {e}")
            break


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio controls autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

def sticky_header():

    # make header sticky.
    st.markdown(
        f"""
            <div class='fixed-header'/>
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
                    position: sticky;
                    top: 2.875rem;
                    background-color: white;
                    z-index: 999;
                }}
                .fixed-header {{
                    border-bottom: 1px solid black;
                }}
            </style>
        """,
        unsafe_allow_html=True
    )



# Function to make footer fixed at the bottom
def sticky_footer():
    st.markdown(
        """ <div class='fixed-footer'/>
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-footer) {
                    position: sticky;
                    bottom: 0;
                    width: 100%;
                    background-color: white;
                    z-index: 999;
                }
                .fixed-footer {
                    top:100px;
                    border-top: 1px solid black;
                    padding: 10px 0;
                    text-align: center;
                }
            </style>
        """,
        unsafe_allow_html=True
    )