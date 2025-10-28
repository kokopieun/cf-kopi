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
            zone_id = data.get('zoneId')
            service_name = data.get('serviceName')
            
            if not email or not global_api_key or not account_id or not service_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Email, API key, account ID, and service name are required"
                }).encode())
                return

            final_zone_id = zone_id

            # Auto-discover if zoneId not provided
            if not final_zone_id:
                discover_response = requests.get(
                    "https://api.cloudflare.com/client/v4/zones",
                    headers={
                        "X-Auth-Email": email,
                        "X-Auth-Key": global_api_key,
                        "Content-Type": "application/json"
                    }
                )

                zones_result = discover_response.json()
                
                if zones_result.get('success') and zones_result.get('result') and not final_zone_id:
                    final_zone_id = zones_result['result'][0]['id']

            if not final_zone_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Could not auto-discover Zone ID"
                }).encode())
                return

            # Get zone info
            zone_response = requests.get(
                f"https://api.cloudflare.com/client/v4/zones/{final_zone_id}",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            zone_result = zone_response.json()
            root_domain = zone_result.get('result', {}).get('name', 'unknown') if zone_result.get('success') else 'unknown'

            # Get domains list
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/domains"
            response = requests.get(url, headers={
                "X-Auth-Email": email,
                "X-Auth-Key": global_api_key,
                "Content-Type": "application/json"
            })
            
            domains = []
            if response.status_code == 200:
                result = response.json()
                domains = [item['hostname'] for item in result.get('result', []) 
                          if item.get('service') == service_name]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "domains": domains,
                "config": {
                    "accountId": account_id,
                    "zoneId": final_zone_id,
                    "serviceName": service_name,
                    "rootDomain": root_domain
                }
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
