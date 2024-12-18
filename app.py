import os
import logging
from flask import Flask, render_template, request, jsonify
import requests
import markdown
from markupsafe import Markup
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mlj_sermons_secret_key")

# API configuration
RAGIE_API_URL = "https://api.ragie.ai/retrievals"
RAGIE_API_TOKEN = "tnt_BPBxTqQudZm_yEfynu5h53B0xDQyRYnWUmSlXZMTO3JNxXyk3tzduRg"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_blog_post(query, sermon_chunks):
    """Generate a blog post using OpenAI based on sermon excerpts"""
    if not sermon_chunks:
        return "No content available for blog generation."
    
    # Combine all sermon excerpts
    combined_text = "\n\n".join([chunk['text'] for chunk in sermon_chunks])
    
    # Create prompt for OpenAI
    prompt = f"""As an expert on Martin Lloyd-Jones' teachings, write a detailed blog post about the following topic:
    
Query: {query}

Based on these sermon excerpts:
{combined_text}

Please write a comprehensive blog post that:
1. Explains MLJ's perspective on this topic
2. Includes relevant quotes from the provided excerpts
3. Provides theological context and practical applications
4. Maintains MLJ's pastoral and doctrinal emphasis
5. Structures the content with clear headings and subheadings

Format the response in Markdown with proper headings, quotes, and sections."""

    try:
        # Generate blog post using OpenAI
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "You are an expert on Martin Lloyd-Jones' theology and preaching, skilled at writing detailed blog posts that explain his teachings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None

def format_api_response(response_data):
    """Format the API response into markdown"""
    if not response_data or 'scored_chunks' not in response_data:
        return "No results found.", None
    
    # Format raw excerpts
    formatted_excerpts = "# Original Sermon Excerpts\n\n"
    for chunk in response_data['scored_chunks']:
        text = chunk['text'].strip()
        doc_name = chunk['document_name']
        source_url = chunk['document_metadata'].get('source_url', '#')
        formatted_excerpts += f"## From [{doc_name}]({source_url})\n\n{text}\n\n---\n\n"
    
    return formatted_excerpts, response_data['scored_chunks']

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
        formatted_excerpts, sermon_chunks = format_api_response(results)
        
        # Generate AI blog post
        blog_post = generate_blog_post(query, sermon_chunks)
        
        if blog_post:
            # Combine blog post and raw excerpts
            full_content = f"{blog_post}\n\n---\n\n{formatted_excerpts}"
            html_results = Markup(markdown.markdown(full_content, extensions=['extra']))
            return render_template('results.html', 
                                results=html_results,
                                query=query)
        else:
            # Fallback to just showing excerpts if blog generation fails
            html_results = Markup(markdown.markdown(formatted_excerpts, extensions=['extra']))
            return render_template('results.html',
                                results=html_results,
                                query=query,
                                error="Blog post generation failed. Showing raw excerpts only.")

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
