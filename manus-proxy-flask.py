from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/manus', methods=['POST', 'OPTIONS'])
def manus_proxy():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        api_key = data.get('apiKey')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 400
        
        # Forward to Manus API
        response = requests.post(
            'https://api.manus.app/v1/agent',
            json={
                'message': data.get('message'),
                'mode': data.get('mode'),
                'stream': data.get('stream', False)
            },
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key
            }
        )
        
        if not response.ok:
            return jsonify({
                'error': f'API Error: {response.status_code}',
                'details': response.text
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f'Starting Manus CORS Proxy on port {port}')
    app.run(host='0.0.0.0', port=port)
