# Mock AI Microservice
# This service simulates the real AI agent for development and testing.

from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }), 200

@app.route('/api/rag_query', methods=['POST'])
def rag_query():
    """Mock RAG query endpoint."""
    data = request.get_json()
    query = data.get('query', '')
    print(f"Received RAG query: {query}")
    response_text = f"This is a mock response to your query: '{query}'. The real AI service would provide a detailed answer."
    return jsonify({'response': response_text})

@app.route('/api/analyze_config', methods=['POST'])
def analyze_config():
    """Mock configuration analysis endpoint."""
    data = request.get_json()
    config_text = data.get('config_text', '')
    device_name = data.get('device_name', 'Unknown Device')
    print(f"Received config for analysis from {device_name}. Length: {len(config_text)}")
    analysis_text = f"This is a mock analysis for {device_name}'s configuration. It appears to be valid. The real AI service would provide a detailed security and best-practice audit."
    return jsonify({'analysis': analysis_text})

if __name__ == '__main__':
    # Run on port 5004 to match the AI_AGENT_URL config
    app.run(host='0.0.0.0', port=5004, debug=False)
