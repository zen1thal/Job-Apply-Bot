import json
import time
import datetime
from datetime import datetime
import random
import logging
import re
import os
from pathlib import Path
from typing import List

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import ollama
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm
from PyPDF2 import PdfReader


KEYWORDS = ["junior developer", "fullstack", "backend", "frontend"]

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

DB_PATH = "./chroma_db"
COLLECTION_NAME = "pdf_chunks"


# Load config
with open("config.json", "r") as file:
    config = json.load(file)

# Logging setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 1. Load & Chunk PDF
# --------------------------------------------------------------------------- #


def load_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(f"Extracted {len(text):,} characters from {len(reader.pages)} pages.")
    return text


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    print(f"Created {len(chunks)} chunks.")
    return chunks


# --------------------------------------------------------------------------- #
# 2. Embed & Store in Chroma
# --------------------------------------------------------------------------- #


def get_embedding_function():
    return embedding_functions.OllamaEmbeddingFunction(
        model_name=config["ollama_embed"], url="http://localhost:11434"
    )


def build_vector_db(pdf_path: str):
    text = load_pdf_text(pdf_path)
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

    client = chromadb.PersistentClient(path=DB_PATH)
    embedding_fn = get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    log.info("Embedding and storing chunks...")
    for i, chunk in enumerate(tqdm(chunks)):
        collection.add(
            ids=[f"chunk_{i}"],
            documents=[chunk],
            metadatas=[{"source": "pdf", "chunk_id": i}],
        )
    log.info(f"Stored {collection.count()} chunks.")


# --------------------------------------------------------------------------- #
# 3. Browser Setup & Login
# --------------------------------------------------------------------------- #


def human_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))


def browser_setup():
    # -------- Configure Chrome Profile --------
    opts = webdriver.ChromeOptions()
    opts.add_argument(rf"--user-data-dir={config['chrome_user_data_dir']}")
    opts.add_argument(rf"--profile-directory={config['chrome_profile']}")

    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--remote-debugging-port=9222")

    browser = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=opts
    )

    print("Chrome options configured.")
    return browser


def login(browser, username, password):
    browser.get("https://www.linkedin.com/login")
    try:
        user_field = browser.find_element("id", "username").send_keys(username)
        # user_field = browser.find_element(By.ID,"username").send_keys(username)
        pw_field = browser.find_element("id", "password").send_keys(password)
        time.sleep(2)
        login_button = browser.find_element(
            By.XPATH, "//button[@type='submit']"
        ).click()
        time.sleep(15)
    except Exception as e:
        print(f" Username/password field or login button not found, {e}")


# --------------------------------------------------------------------------- #
# 4. Retrieve & Answer
# --------------------------------------------------------------------------- #


def retrieve_context(question: str, top_k: int = 4) -> str:
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    results = collection.query(query_texts=[question], n_results=top_k)
    context = "\n\n".join(results["documents"][0])
    return context


def generate_answers(question: str, job_title, job_company, job_description) -> str:
    context = retrieve_context(question)
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a professional job applicant writing a concise answer to a LinkedIn job question."
                "Answer the question using ONLY the provided context from the PDF. "
                "Use first person if needed"
                "CRITICAL INSTRUCTION: When asked for the specific number of years of experience or any other specific number, provide an exact number in integer based on the context without adding any extra words."
                f"Job Title: {job_title} Company: {job_company} Description: {job_description}.\n"
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        },
    ]

    log.info(f"Asking {config['ollama_model']} in chat mode...")
    response = ollama.chat(
        model=config["ollama_model"],
        messages=prompt,
        options={"temperature": 0.2, 'top_p': 0.9},
    )
    
    raw_answer = response["message"]["content"].strip()
    
    match = re.search(r'\b(\d+)\b', raw_answer)
    response = match.group(1) 

    return response


def generate_cover_letter(
    question: str, fullname, email, phone, job_title, job_company, job_description
) -> str:
    context = retrieve_context(question, top_k=6)
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a professional job applicant. Your task is to write a cover letter using the provided context and applicant data. "
                "The letter must be enthusiastic, professional, and tailored to the job. "
                "CRITICAL INSTRUCTION: You MUST use the exact data from the 'APPLICANT_DATA' section. Do NOT use any placeholders like '[Your Name]' or '[Email Address]'.\n\n"
                "--- APPLICANT_DATA ---\n"
                f"Full Name: {fullname}\n"
                f"Email: {email}\n"
                f"Phone: {phone}\n"
                f"Date: {datetime.now().strftime('%B %d, %Y')}\n"
                "--- END APPLICANT_DATA ---\n\n"
                f"The application is for the role of {job_title} at {job_company}."
            ),
        },
        {
            "role": "user",
            "content": f"Use the provided context below to write a compelling cover letter. Sign the letter with the applicant's full name provided in the system prompt.\n\nContext:\n{context}",
        },
    ]

    log.info(f"Asking {config['ollama_model']} to generate cover letter...")
    response = ollama.chat(
        model=config["ollama_model"],
        messages=prompt,
        options={"temperature": 0.3, 'top_p': 0.9}
    )
    return response["message"]["content"].strip()


def handle_questions(browser):
    questions = []
    question_elements = browser.find_elements(
        By.CSS_SELECTOR, "div[@data-test-form-element]"
    )
    for container in question_elements:
        try:
            # Text inputs
            labels = container.find_elements(
                By.CSS_SELECTOR, "label.artdeco-text-input--label"
            ).text.strip()
            inputs = container.find_elements(
                By.CSS_SELECTOR, "input.artdeco-text-input--input"
            )
            if labels and inputs.is_enabled():
                for label, input in zip(labels, inputs):
                    questions.append({"label": label, "element": input})

            # Radio buttons
            spans = container.find_elements(
                By.CSS_SELECTOR, "span.fb-dash-form-element__label"
            ).text.strip()
            radio_buttons = container.find_elements(
                By.CSS_SELECTOR, "input.[type='radio']"
            )
            if spans and radio_buttons:
                for legend in spans:
                    questions.append({"label": legend, "element": radio_buttons})

        except:
            continue

    return questions


def start_apply(browser):

    try:
        for keyword in config["keywords"]:
            print(f"Searching for jobs with keyword: {keyword}")

            browser.get(
                f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}f_AL=true&location={config['location']}&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0"
            )
            human_delay(3, 7)
            # TODO: Finish the logic of job application

            # Lisf of jobs
            links = browser.find_elements(By.XPATH, "//div[@data-job-id]")
            print(f"Processing job listing: {links}")

            for job in links:
                try:
                    browser.execute_script("arguments[0].scrollIntoView();", job)
                    human_delay(1, 3)

                    job_title_element = job.find_element(
                        By.CSS_SELECTOR, "a.job-card-list__title"
                    ).click()
                    job_title = job_title_element.text.strip()
                    human_delay(2, 5)

                    job_company_element = job.find_element(
                        By.CSS_SELECTOR, "a.job-card-container__company-name"
                    )
                    job_company = job_company_element.text.strip()
                    print(f"Applying to job at: {job_company}")

                    job_description_element = browser.find_element(
                        By.CLASS_NAME, "jobs-description__container"
                    )
                    job_description = job_description_element.text.strip()

                    # generate_cover_letter(job_title, job_company, job_description)

                    # "Easy Apply" button
                    browser.find_element(By.ID, "jobs-apply-button-id").click()
                    human_delay(2, 4)

                    # Click "Next" if it exists
                    next_button = browser.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Continue to next step']"
                    )
                    while next_button:
                        next_button.click()
                        human_delay(2, 5)

                        handle_questions(browser)

                        try:
                            next_button = browser.find_element(
                                By.CSS_SELECTOR,
                                "button[aria-label='Continue to next step']",
                            )
                        except:
                            next_button = None

                    # Review and submit
                    review_button = browser.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Review your application']"
                    )
                    review_button.click()
                    human_delay(2, 5)

                    submit_button = browser.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Submit application']"
                    )
                    submit_button.click()
                    print("Application submitted (simulation).")

                    # Close the application modal
                    close_button = browser.find_element(
                        By.CLASS_NAME, "artdeco-modal__dismiss"
                    )
                    close_button.click()
                    human_delay(1, 2)

                except Exception as e:
                    print(f"Could not process a job listing: {e}")
                    try:
                        close_button = browser.find_element(
                            By.CLASS_NAME, "artdeco-modal__dismiss"
                        )
                        close_button.click()
                        human_delay(1, 2)
                    except:
                        pass

    except Exception as e:
        print(f"Could not complete the search for keyword '{keyword}': {e}")

    browser.quit()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main():
    pdf_path = Path(config["pdf_path"])
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {config['pdf_path']}")

    if not os.path.exists(DB_PATH):
        build_vector_db(config["pdf_path"])
    else:
        log.info("Using existing vector DB.")

    # browser = browser_setup()
    # print("Browser opened with profile")

    # login(browser, config['username'], config['password'])
    # questions = get_questions(browser)
    response = generate_answers(
        "How many years of experience does the person from pdf have as a developer?",
        "Junior Developer",
        "Tech Company",
        "An exciting opportunity to work as a Junior Developer at Tech Company.",
    )
    print(f"\nA: {response}\n")
    letter = generate_cover_letter(
        question="Write down a cover letter",
        fullname=config["fullname"],
        email=config["email"],
        phone=config["phone"],
        job_title="Junior Developer",
        job_company="Tech Company",
        job_description="An exciting opportunity to work as a Junior Developer at Tech Company.",
    )
    print(f"\nA: {letter}\n")
    # start_apply(browser)


if __name__ == "__main__":
    main()
