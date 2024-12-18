import os
import logging
from flask import Flask, render_template, request, jsonify
import requests
import markdown
from markupsafe import Markup

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mlj_sermons_secret_key")

# Ragie API configuration
RAGIE_API_URL = "https://api.ragie.ai/retrievals"
RAGIE_API_TOKEN = "tnt_BPBxTqQudZm_yEfynu5h53B0xDQyRYnWUmSlXZMTO3JNxXyk3tzduRg"

def format_api_response(response_data):
    """Format the API response into markdown"""
    if not response_data or 'scored_chunks' not in response_data:
        return "No results found."
    
    formatted_text = "# Search Results\n\n"
    for chunk in response_data['scored_chunks']:
        text = chunk['text'].strip()
        doc_name = chunk['document_name']
        formatted_text += f"## From {doc_name}\n\n{text}\n\n---\n\n"
    
    return formatted_text

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
            "max_chunks_per_document": 2
        }

        response = requests.post(RAGIE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        results = response.json()
        formatted_results = format_api_response(results)
        html_results = Markup(markdown.markdown(formatted_results))
        
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
