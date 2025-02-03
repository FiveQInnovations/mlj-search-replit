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

def format_sermon_results(response_data):
    """Format the sermon results into markdown"""
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
        sermons[doc_name]['excerpts'].append(chunk['text'].strip())

    # Format each sermon's content
    for doc_name, sermon in sermons.items():
        formatted_content += f"## [{doc_name}]({sermon['url']})\n\n"
        for excerpt in sermon['excerpts']:
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
            "top_k": 12,
            "rerank": True,
            "max_chunks_per_document": 3
        }

        response = requests.post(RAGIE_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        results = response.json()
        formatted_content = format_sermon_results(results)
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