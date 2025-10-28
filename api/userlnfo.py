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
            
            if not email or not global_api_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Email and API key are required"
                }).encode())
                return

            response = requests.get(
                "https://api.cloudflare.com/client/v4/user",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            result = response.json()
            
            if result.get('success'):
                user_data = result['result']
                
                extended_user_info = {
                    "id": user_data.get('id'),
                    "email": user_data.get('email'),
                    "username": user_data.get('username'),
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name'),
                    "telephone": user_data.get('telephone'),
                    "country": user_data.get('country'),
                    "zipcode": user_data.get('zipcode'),
                    "created_on": user_data.get('created_on'),
                    "modified_on": user_data.get('modified_on'),
                    "two_factor_authentication": user_data.get('two_factor_authentication', {}).get('enabled', False),
                    "suspended": user_data.get('suspended', False),
                    "organizations": user_data.get('organizations', []),
                    "has_pro_zones": user_data.get('has_pro_zones', False),
                    "has_business_zones": user_data.get('has_business_zones', False),
                    "has_enterprise_zones": user_data.get('has_enterprise_zones', False),
                    "betas": user_data.get('betas', []),
                    "total_zone_count": user_data.get('total_zone_count', 0)
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "result": extended_user_info
                }).encode())
            else:
                self.send_response(response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
        except Exception as error:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Internal server error: {str(error)}"
            }).encode())
