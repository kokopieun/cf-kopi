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
                "https://api.cloudflare.com/client/v4/accounts",
                headers={
                    "X-Auth-Email": email,
                    "X-Auth-Key": global_api_key,
                    "Content-Type": "application/json"
                }
            )

            result = response.json()
            
            if result.get('success') and result.get('result'):
                detailed_accounts = []
                
                for account in result['result']:
                    try:
                        # Get account details
                        account_detail_response = requests.get(
                            f"https://api.cloudflare.com/client/v4/accounts/{account['id']}",
                            headers={
                                "X-Auth-Email": email,
                                "X-Auth-Key": global_api_key,
                                "Content-Type": "application/json"
                            }
                        )
                        
                        account_detail = account_detail_response.json()
                        
                        # Get account subscription info
                        subscription_response = requests.get(
                            f"https://api.cloudflare.com/client/v4/accounts/{account['id']}/subscriptions",
                            headers={
                                "X-Auth-Email": email,
                                "X-Auth-Key": global_api_key,
                                "Content-Type": "application/json"
                            }
                        )
                        
                        subscription_data = subscription_response.json()
                        
                        # Get account members
                        members_response = requests.get(
                            f"https://api.cloudflare.com/client/v4/accounts/{account['id']}/members",
                            headers={
                                "X-Auth-Email": email,
                                "X-Auth-Key": global_api_key,
                                "Content-Type": "application/json"
                            }
                        )
                        
                        members_data = members_response.json()
                        
                        detailed_account = {
                            **account,
                            "detailed_info": account_detail.get('result') if account_detail.get('success') else None,
                            "subscription": subscription_data.get('result', [{}])[0] if subscription_data.get('success') and subscription_data.get('result') else None,
                            "member_count": len(members_data.get('result', [])) if members_data.get('success') else 0,
                            "members": members_data.get('result', [])[:5] if members_data.get('success') else []
                        }
                        detailed_accounts.append(detailed_account)
                        
                    except Exception:
                        detailed_accounts.append(account)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "result": detailed_accounts
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
