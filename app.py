import csv
from datetime import datetime

import gradio as gr

# Initialize or load existing CSV file for logging
csv_file = "interaction_log.csv"
with open(csv_file, "a", newline="") as file:
    writer = csv.writer(file)
    # Write header if file is new
    if file.tell() == 0:
        writer.writerow(["timestamp", "user_input", "llm_response", "user_feedback"])


# Function to simulate LLM response (replace with actual LLM call)
def llm_response(user_input):
    return "Simulated response to: " + user_input


# Function to handle interaction and logging
def handle_interaction(user_input, user_feedback):
    response = llm_response(user_input)
    # Log the interaction
    with open(csv_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), user_input, response, user_feedback])
    return response


# Gradio interface setup
iface = gr.Interface(
    fn=handle_interaction,
    inputs=[
        gr.Textbox(label="Ask me anything!"),
        gr.Radio(choices=["Thumbs up", "Thumbs down"], label="Feedback", type="index"),
    ],
    outputs=gr.Textbox(label="Response"),
    title="LLM Interaction Bot",
    description="Talk to the LLM and provide feedback on the responses.",
)

iface.launch()
