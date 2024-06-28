from openai import OpenAI
import streamlit as st
import base64

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
model = "gpt-3.5-turbo"

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

def get_answer(messages):
    system_message = [{"role": "system", "content": "You are an helpful AI chatbot, that answers questions asked by User. Limit your answers to 1 to 3 sentences, and keep your answers as short as possible because you are a voice assistant."}]
    messages = system_message + messages
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

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
        """
            <div class='fixed-header'/>
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                    position: sticky;
                    top: 2.875rem;
                    background-color: white;
                    z-index: 999;
                }
                .fixed-header {
                    border-bottom: 1px solid black;
                }
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