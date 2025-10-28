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
            subdomain = data.get('subdomain')
            
            if not email or not global_api_key or not account_id or not subdomain or not service_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Email, API key, account ID, service name, and subdomain are required"
                }).encode())
                return

            # Auto-determine zoneId if not provided
            final_zone_id = zone_id
            final_root_domain = ''
            final_app_domain = ''

            if not final_zone_id:
                # Auto-discover configuration for zone
                discover_response = requests.get(
                    "https://api.cloudflare.com/client/v4/zones",
                    headers={
                        "X-Auth-Email": email,
                        "X-Auth-Key": global_api_key,
                        "Content-Type": "application/json"
                    }
                )

                zones_result = discover_response.json()
                
                if zones_result.get('success') and zones_result.get('result'):
                    # Find zone that matches subdomain
                    domain_parts = subdomain.split('.')
                    matched_zone = None
                    
                    for i in range(len(domain_parts) - 1):
                        test_domain = '.'.join(domain_parts[i:])
                        matched_zone = next((zone for zone in zones_result['result'] if zone.get('name') == test_domain), None)
                        if matched_zone:
                            final_zone_id = matched_zone['id']
                            final_root_domain = matched_zone['name']
                            break

                    # If no match, use first zone
                    if not final_zone_id and zones_result['result']:
                        final_zone_id = zones_result['result'][0]['id']
                        final_root_domain = zones_result['result'][0]['name']

            # If still no zoneId, return error
            if not final_zone_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Could not auto-discover Zone ID. Please check your Cloudflare configuration."
                }).encode())
                return

            # Determine app domain
            if not final_app_domain:
                domain_parts = subdomain.split('.')
                if len(domain_parts) > 2:
                    final_app_domain = '.'.join(domain_parts[1:])
                else:
                    final_app_domain = final_root_domain

            # Register domain using Cloudflare API
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/domains"
            domain_data = {
                "environment": "production",
                "hostname": subdomain.lower(),
                "service": service_name,
                "zone_id": final_zone_id,
            }
            
            response = requests.put(
                url,
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                },
                json=domain_data
            )

            status = response.status_code
            
            message = ""
            if status == 200:
                message = "✅ Wildcard domain registered successfully"
            elif status == 409:
                message = "⚠️ Domain already registered"
            elif status == 400:
                message = "❌ Invalid domain format"
            elif status == 403:
                message = "⛔ Contains forbidden words"
            elif status == 530:
                message = "🔒 Root domain not active"
            else:
                message = f"❌ Registration failed with status: {status}"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": status == 200,
                "status": status,
                "message": message,
                "domain": subdomain,
                "config": {
                    "accountId": account_id,
                    "zoneId": final_zone_id,
                    "serviceName": service_name,
                    "rootDomain": final_root_domain,
                    "appDomain": final_app_domain
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
