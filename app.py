from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# API keys from .env file
RAGIE_API_KEY = os.getenv("RAGIE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Function to query Ragie.AI for document retrieval
def query_ragie(user_query):
    url = "https://api.ragie.ai/retrievals"
    headers = {
        "Authorization": f"Bearer {RAGIE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "query": user_query,
        "filters": {"source": "Google Drive"},
        "top_k": 3  # Retrieve the top 3 most relevant results
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error if response is not 200
        return response.json().get("results", [])
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
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that provides insights from the user's Google Drive documents."},
            {"role": "user", "content": context}
        ]
    }

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

    # Step 1: Query Ragie.AI
    ragie_results = query_ragie(user_query)

    # Step 2: Extract relevant context from Ragie results
    context = "\n".join([r.get("snippet", "No relevant text found") for r in ragie_results if isinstance(r, dict)])

    # Step 3: Use OpenAI to generate a response
    response_text = generate_response(context)

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(debug=True)

