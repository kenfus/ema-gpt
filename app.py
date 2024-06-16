import os
import traceback
from datetime import datetime

import google.generativeai as genai
import gradio as gr
import pandas as pd
from google.api_core import retry

from gpt_utils import GPT_PROMPT, get_text_from_url, google_search

# Initialize the dataframe to store questions, answers, and feedback
interaction_log = "interaction_log.csv"
model_name = "gemini-1.5-flash"

# Initialize the dataframe to store questions, answers, feedback, and datetime
if os.path.exists(interaction_log):
    feedback_data = pd.read_csv(interaction_log)
else:
    feedback_data = pd.DataFrame(columns=["datetime", "question", "answer", "feedback"])


# Function to save feedback
def save_interaction(question, answer, feedback):
    global feedback_data
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_entry = pd.DataFrame(
        [
            {
                "datetime": current_time,
                "question": question,
                "answer": answer,
                "feedback": feedback,
            }
        ]
    )

    feedback_data = pd.concat([feedback_data, new_entry], ignore_index=True)
    feedback_data.to_csv("interaction_log.csv", index=False)


# Function to interact with the LLM
def query_llm(user_input):
    ordering_system = [google_search, get_text_from_url]

    model = genai.GenerativeModel(
        model_name, tools=ordering_system, system_instruction=GPT_PROMPT
    )

    convo = model.start_chat(enable_automatic_function_calling=True)

    @retry.Retry(initial=30)
    def send_message(message):
        return convo.send_message(message)

    try:
        answer = send_message(user_input)
    except Exception as E:
        print(E)
        traceback.print_exc()
    return answer.text


# Gradio interface
def gradio_interface(user_input):
    answer = query_llm(user_input)
    return answer, "", gr.update(visible=True)


# Gradio app
with gr.Blocks() as demo:
    with gr.Column():
        user_input = gr.Textbox(label="Ask a question", lines=2)
        answer_display = gr.Markdown()
        submit_button = gr.Button("Submit")
        feedback = gr.Radio(
            choices=["👍", "👎"], label="Was this answer helpful?", visible=False
        )

    submit_button.click(
        gradio_interface,
        inputs=user_input,
        outputs=[answer_display, user_input, feedback],
    )
    feedback.change(
        save_interaction, inputs=[user_input, answer_display, feedback], outputs=[]
    )

demo.launch()
