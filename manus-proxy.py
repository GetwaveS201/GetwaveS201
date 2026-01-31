from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/manus':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            # Get API key from request body
            api_key = data.get('apiKey')
            
            # Forward to Manus API
            req = urllib.request.Request(
                'https://api.manus.app/v1/agent',
                data=json.dumps({
                    'message': data.get('message'),
                    'mode': data.get('mode'),
                    'stream': data.get('stream', False)
                }).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key
                }
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    result = response.read()
                    
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    print('========================================')
    print('  MANUS CORS PROXY SERVER')
    print('========================================')
    print('')
    print('Server running on http://localhost:8080')
    print('KEEP THIS WINDOW OPEN!')
    print('')
    print('Press Ctrl+C to stop')
    print('========================================')
    print('')
    
    server = HTTPServer(('localhost', 8080), CORSProxyHandler)
    server.serve_forever()
