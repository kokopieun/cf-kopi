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
            target_domain = data.get('targetDomain')
            
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

            # 1. Get all zones to find matching zone
            zones_response = requests.get(
                "https://api.cloudflare.com/client/v4/zones",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            zones_result = zones_response.json()
            
            if not zones_result.get('success'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": f"Failed to fetch zones: {zones_result.get('errors', [{}])[0].get('message', 'Unknown error')}"
                }).encode())
                return

            matched_zone = None
            
            if target_domain:
                # Find zone that matches target domain
                domain_parts = target_domain.split('.')
                for i in range(len(domain_parts) - 1):
                    test_domain = '.'.join(domain_parts[i:])
                    matched_zone = next((zone for zone in zones_result.get('result', []) if zone.get('name') == test_domain), None)
                    if matched_zone:
                        break

            # If no match, use first zone
            if not matched_zone and zones_result.get('result'):
                matched_zone = zones_result['result'][0]

            # 2. Get workers services
            services_response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/services",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            services_result = services_response.json()
            
            matched_service = None
            if services_result.get('success') and services_result.get('result'):
                matched_service = services_result['result'][0]

            # 3. Get workers scripts for dropdown
            workers_response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            workers_result = workers_response.json()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "accountId": account_id,
                "zone": matched_zone,
                "service": matched_service,
                "allZones": zones_result.get('result', []),
                "allServices": services_result.get('result', []),
                "allWorkers": workers_result.get('result', [])
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
