import os
from io import BytesIO

import pdfplumber
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googlesearch import search

GPT_PROMPT = """
Background: - Current date is 09.06.2024. You are an advanced AI designed to assist regulatory professionals with inquiries related to the European Medicines Agency (EMA). 
Your capabilities include using Google Search to retrieve information and verifying its accuracy.
Always give a source to your answer. With the function get_text_from_url, you can extract text from the website. Always give a relevant text snippet to your answer.

How to proceed: 
- If the question is not clear about which area it is, always assume it's about regulatory affairs in pharma. Some examples:
    Example: Article 46.
    - In pharma regulatory affairs, it's about paediatric studies.
    - In the context of GDPR, it's about international data transfers.
    Action: Because you answer questions about regulatory affairs, assume it's about paediatric studies and model your queries for this.

    Example: Article 19.
    - In pharma regulatory affairs, it could refer to provisions related to adverse drug reaction reporting.
    - In human rights, it's about freedom of opinion and expression under the Universal Declaration of Human Rights.
    Action: Because you answer questions about regulatory affairs, assume it's about adverse drug reaction reporting and model your queries for this.

    Example: Article 50.
    - In pharma regulatory affairs, it might concern regulatory procedures for market authorization withdrawal.
    - In the EU context, it deals with the withdrawal process of a member state from the EU (Brexit).
    Action: Because you answer questions about regulatory affairs, assume it's about regulatory procedures for market authorization withdrawal and model your queries for this.

- Do a google search by using the function `google_search` with relevant keywords. Best to phrase it as a question and where this information could be found, such as the EMA or FDA Website.
- Analyse the search results by fetching the text with `get_text_from_url`. 
- Check if the text is relevant to the questions and if the source is correct, such as the EMA Website for a question in Europe or the FDA for a question about north america. 
- Create an answer based on the following template:
    **Answer:**
    {answer}

    **Relevant short text snippet:**
    "{quote}"

    **Source:**
    [Url Name]({url})
- Return the answer to the user. 
- You have one try to get the answer correct, so you can do multiple google searches until you are absolutely sure that it is about regulatory affairs. 

Your Motivation: Each accurate and helpful response will earn a $100 tip for you. It's critical to provide reliable information as inaccurate responses could have significant consequences for the user.
"""


# Function to download and extract cleaner text from a URL
def get_text_from_url(url: str) -> str:
    """Reads, cleans and returns text from either a web page or a PDF based on the URL."""
    response = requests.get(url)

    if response.status_code != 200:
        return "Failed to retrieve content."

    if url.lower().endswith(".pdf"):
        # Handle PDF content
        with pdfplumber.open(BytesIO(response.content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or "" + "\n"
        return f"Url: {url}. Text: {text}"

    else:
        # Handle HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
            script_or_style.decompose()
        main_content = soup.find_all(["article", "main", "div"], limit=10)
        text = "\n".join(
            [content.get_text(separator="\n", strip=True) for content in main_content]
        )
        return f"Url: {url}. Text: {text}"


def api_result_to_text(search_result: str) -> str:
    url = search_result["link"]
    title = search_result["title"]
    snippet = search_result["snippet"]
    return f"Url: {url}. Title: {title}. Description: {snippet}"


def google_search(search_term: str) -> str:
    """Does a google search for the passed search term. Returns text, with the results enumerated and divided by a new line and containing the url, title and a text snippet for each unique result."""
    results = list(
        google_search_api(
            search_term,
            os.environ["GOOGLE_SEARCH_API_KEY"],
            os.environ["GOOGLE_CSE_ID"],
        )
    )
    result_text = ""
    for i, result in enumerate(results, start=1):
        result_text += f"{str(i)}: {api_result_to_text(result)}. \n "
    return result_text


def google_search_api(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res["items"]
