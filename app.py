import os
import logging
from flask import Flask, render_template, request
import requests
import markdown
from markupsafe import Markup

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mlj_sermons_secret_key")

# API configuration
RAGIE_API_URL = "https://api.ragie.ai/retrievals"
RAGIE_API_TOKEN = "tnt_BPBxTqQudZm_yEfynu5h53B0xDQyRYnWUmSlXZMTO3JNxXyk3tzduRg"

def highlight_relevant_content(text, query):
    """Add bold markdown to relevant phrases"""
    # Split query into words for matching
    query_words = query.lower().split()

    # Split text into sentences
    sentences = text.replace(". ", ".\n").split("\n")
    highlighted_sentences = []

    for sentence in sentences:
        # Check if sentence contains any query words
        if any(word in sentence.lower() for word in query_words):
            # Add bold markdown around the sentence
            highlighted_sentences.append(f"**{sentence.strip()}**")
        else:
            highlighted_sentences.append(sentence.strip())

    return " ".join(highlighted_sentences)

def truncate_text(text, max_length=300):
    """Truncate text to the nearest sentence boundary within max_length"""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_period = truncated.rfind('.')

    if last_period > 0:
        return text[:last_period + 1]
    return truncated + "..."

def format_sermon_results(response_data, query):
    """Format the sermon results into markdown with shorter sections and highlights"""
    if not response_data or 'scored_chunks' not in response_data:
        return "No sermons found for this topic."

    formatted_content = "# Relevant Sermon Excerpts\n\n"

    # Group chunks by sermon
    sermons = {}
    for chunk in response_data['scored_chunks']:
        doc_name = chunk['document_name']
        if doc_name not in sermons:
            sermons[doc_name] = {
                'url': chunk['document_metadata'].get('source_url', '#'),
                'excerpts': []
            }
        # Truncate and highlight the text
        truncated_text = truncate_text(chunk['text'].strip())
        highlighted_text = highlight_relevant_content(truncated_text, query)
        sermons[doc_name]['excerpts'].append(highlighted_text)

    # Format each sermon's content
    for doc_name, sermon in sermons.items():
        formatted_content += f"## [{doc_name}]({sermon['url']})\n\n"
        for excerpt in sermon['excerpts'][:2]:  # Limit to 2 excerpts per sermon
            formatted_content += f"{excerpt}\n\n"
        formatted_content += "---\n\n"

    return formatted_content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    if not query:
        return render_template('results.html', error="Please enter a search query")

    try:
        headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {RAGIE_API_TOKEN}',
            'content-type': 'application/json'
        }

        payload = {
            "query": query,
            "top_k": 8,  # Reduced from 12 to show fewer, more relevant results
            "rerank": True,
            "max_chunks_per_document": 2  # Reduced from 3 to show fewer excerpts
        }

        response = requests.post(RAGIE_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        results = response.json()
        formatted_content = format_sermon_results(results, query)
        html_results = Markup(markdown.markdown(formatted_content, extensions=['extra']))

        return render_template('results.html', 
                             results=html_results,
                             query=query)

    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return render_template('results.html', 
                             error="Sorry, there was an error processing your request")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template('results.html', 
                             error="An unexpected error occurred")

if __name__ == '__main__':
    app.run(debug=True)