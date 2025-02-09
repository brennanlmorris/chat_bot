from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# API keys from .env file
RAGIE_API_KEY = os.getenv("RAGIE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Function to query Ragie.AI for document retrieval
import json  # Import json module to format the output

def query_ragie(user_query):
    url = "https://api.ragie.ai/retrievals"
    headers = {
        "Authorization": f"Bearer {RAGIE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "query": user_query,
        "filters": { "scope": "tutorial" },
        "top_k": 5
    }

    print("Sending Request to Ragie:", data)

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()

        # Extract text chunks instead of generic "results"
        chunk_texts = [chunk["text"] for chunk in data.get("scored_chunks", [])]

        print("Extracted Chunk Texts:", chunk_texts)
        return chunk_texts
    except requests.exceptions.RequestException as e:
        print("Error querying Ragie:", e)
        return []

# Function to generate a response using OpenAI
def generate_response(context):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # New system prompt formatting from Ragie
    system_prompt = f"""You are "Ragie AI", a professional but friendly AI chatbot assisting the user.

Your task is to help the user based on the provided information.
Organize responses into clear, structured points.
If no relevant information is found, tell the user you couldn't find anything.

Here is the retrieved information that may answer the user's question:
===
{context[:4000]}  # Trim to avoid exceeding token limits
===
"""

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
    }

    print("Sending OpenAI Request:", data)

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print("Error calling OpenAI:", e)
        return "Error generating response."

# Route to serve a basic web interface
@app.route("/")
def home():
    return render_template("index.html")  # Ensure index.html is inside the 'templates' folder

# API route to handle chatbot queries
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    print("Received request:", data)  # Debugging: check incoming request

    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    # Step 1: Query Ragie.AI and retrieve text chunks
    chunk_texts = query_ragie(user_query)  # Now using chunk_texts instead of ragie_results

    # Step 2: Extract relevant context from Ragie results
    if chunk_texts:
        context = "\n".join(chunk_texts)  # Use the text extracted from Ragie
    else:
        context = "No relevant information was found in the documents."

    print("Extracted Context:", context)  # Debugging output

    # Step 3: Use OpenAI to generate a response
    response_text = generate_response(context)

    return jsonify({"response": response_text})

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)


