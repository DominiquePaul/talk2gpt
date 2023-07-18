import os
import time
import tempfile
import openai
import streamlit as st
from audiorecorder import audiorecorder

openai.api_key = os.environ["OPENAI_API_KEY"]

system_instructions = "You are a useful assistant who helps transcribed notes become more useful. Use a clear and concise language that is easy to understand. Remove filling words and use short sentences."


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


if check_password():

    st.title("Audio Recorder")
    audio = audiorecorder("Click to record", "Recording...")

    if len(audio) > 0:
        # To play audio in frontend:
        st.audio(audio.tobytes())
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            name = temp_file.name
            temp_file.write(audio.tobytes())
        with open(name, "rb") as f:
            whisper_obj = openai.Audio.transcribe("whisper-1", f)

        # add a prompt
        st.subheader("Now add your prompt for GPT here:")
        with st.form(key='my_form'):
            text_input = st.text_input(
                label='Your prompt', value="Summarise the following text into bullets:")
            st.write(whisper_obj.text)
            submit = st.form_submit_button(label='Submit')

        if submit:
            start = time.time()
            resp = openai.ChatCompletion.create(
                model=os.environ["OPENAI_GPT_MODEL"],
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": text_input +
                        "\n\n" + whisper_obj.text},
                ],
                max_tokens=3000,
                temperature=0.2,
                stream=False,
            )
            print(f"API call took {time.time() - start} seconds.")

            summary = resp["choices"][0]["message"]["content"]
            # Do something with the text
            st.markdown(summary)
