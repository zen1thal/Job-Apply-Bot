<div align="center">

# [Linkedin](#) AI Job Apply Bot

<p>
<a href="#installation">Install</a> •
<a href="#setup">Setup</a> •
<a href="#run-the-code">Run the code</a> 
</p>

[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-blue.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![Please Star](https://img.shields.io/badge/⭐_If_you_like_this_project%2C_please_star!-gray)](https://github.com/zen1thal/AI-Job-Apply)
[![Follow Me](https://img.shields.io/badge/Follow%20Me%20on%20GitHub-181717?logo=github&logoColor=white)](https://github.com/zen1thal)

No time to be sitting for the entire day applying for jobs? No problem, this script might help you with the issue.

</div>

## Development Progress

This is my first serious project that is being made with tons of investigation and learning(since that's what hypes me up). The code development is still in progress and it's made only for research reasons. It is planned to add later local AI functionality model to respond custom questions that are outside of the algorithm. Any contributions would be pretty appreciated since the idea of this project consists of learning Python libraries while working with AI models.

## Requirements

- Install the same version of Chrome and ChromeDriver. Watch compatibilities here: https://developer.chrome.com/docs/chromedriver/downloads
- Python version 3.9+

## Installation

Used Python 3.9.4 on MacOS via Virtual Environment/Conda

Before running, install the necessary libraries

```bash
pip3 install -r requirements.txt
```

Later download the Ollama models

```bash
ollama pull llama3.1:8b
ollama pull mxbai-embed-large 
```

## Setup

Update the config.json:

```yaml
{
    "username": "Your username here",
    "password": "Your password here",
    "fullname": "Your Full name",
    "email": "email",
    "phone": "phone number",
    "keywords": ["
                - # positions you want to search for
                - # Another position you want to search for
                - # A third position you want to search for
                "],
    "location": ["Madrid"],
    "chrome_user_data_dir": " 
                            - # Windows: C:/Users/name_of_the_user/AppData/Local/Google/Chrome/User Data"
                            - # MacOS: /Users/name_of_the_user/Library/Application Support/Google/Chrome"
                            - # MacOS: /Users/name_of_the_user/Library/Application Support/Google/Chrome",
    "chrome_profile": "Current Chrome Profile. Example: Profile 1",
    "ollama_model": "llama3.1:8b", # You can use any local model from ollama, the better ones, the stronger hardware you should have
    "ollama_embed": "mxbai-embed-large", # The ollama embed model to switch text for ai model to understand it
    "pdf_path": "cv.pdf" # You can use any custom cv path or directly place it in the folder and call it cv.pdf
}

```

## Run the code

To execute the bot run the following in your terminal

```bash
python3 main.py
```
