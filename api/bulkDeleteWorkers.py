from http.server import BaseHTTPRequestHandler
import json
import requests

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
            worker_names = data.get('workerNames')
            
            if not email or not global_api_key or not account_id or not worker_names or not isinstance(worker_names, list):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "All fields are required and workerNames must be an array"
                }).encode())
                return

            results = []
            for worker_name in worker_names:
                try:
                    response = requests.delete(
                        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}",
                        headers={
                            "X-Auth-Email": email,
                            "X-Auth-Key": global_api_key,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    result = response.json()
                    results.append({
                        "workerName": worker_name,
                        "success": result.get('success', False),
                        "message": result.get('errors', [{}])[0].get('message', 'Deleted successfully') if result.get('errors') else "Deleted successfully"
                    })
                except Exception as error:
                    results.append({
                        "workerName": worker_name,
                        "success": False,
                        "message": str(error)
                    })

            all_success = all(r['success'] for r in results)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": all_success,
                "results": results
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
