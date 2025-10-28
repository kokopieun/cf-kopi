from http.server import BaseHTTPRequestHandler
import json
import random

class Handler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        try:
            email = data.get('email')
            global_api_key = data.get('globalAPIKey')
            account_id = data.get('accountId')
            worker_name = data.get('workerName')
            
            if not email or not global_api_key or not account_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Email, API key, and account ID are required"
                }).encode())
                return

            # Generate mock analytics data
            analytics_data = {
                "requests": {
                    "total": random.randint(1000, 10000),
                    "cached": random.randint(500, 5000),
                    "uncached": random.randint(500, 5000),
                    "success": random.randint(800, 9000),
                    "error": random.randint(100, 1000),
                    "byCountry": {
                        'US': random.randint(1000, 3000),
                        'ID': random.randint(500, 2000),
                        'IN': random.randint(300, 1500),
                        'BR': random.randint(200, 1000),
                        'Others': random.randint(500, 2500)
                    }
                },
                "bandwidth": {
                    "served": random.randint(500000000, 1000000000),
                    "cached": random.randint(250000000, 500000000)
                },
                "performance": {
                    "avgResponseTime": random.randint(50, 100),
                    "p95": random.randint(100, 200),
                    "p99": random.randint(150, 300)
                },
                "cpuTime": {
                    "total": random.randint(50000, 100000),
                    "average": random.randint(5, 10)
                }
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "analytics": analytics_data
            }).encode())
            
        except Exception as error:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Internal server error: {str(error)}"
            }).encode())
