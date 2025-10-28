from http.server import BaseHTTPRequestHandler
import json
import requests
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
            worker_name = data.get('workerName')
            worker_script_url = data.get('workerScriptUrl')
            account_id = data.get('accountId')
            template = data.get('template')
            
            if not email or not global_api_key or not worker_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Email, API key, and worker name are required"
                }).encode())
                return

            # Determine script URL
            script_url = worker_script_url
            templates = {
                'proxy': 'https://raw.githubusercontent.com/gopaybis/cf/refs/heads/main/worker.js',
                'nautica-mod': 'https://raw.githubusercontent.com/gopaybis/cf/refs/heads/main/worker.js',
                'nautica': 'https://raw.githubusercontent.com/FoolVPN-ID/Nautica/refs/heads/main/_worker.js',
                'html': 'https://raw.githubusercontent.com/example/html-worker/main/worker.js',
                'api': 'https://raw.githubusercontent.com/example/api-worker/main/worker.js',
                'redirect': 'https://raw.githubusercontent.com/example/redirect-worker/main/worker.js'
            }
            
            if template and template != 'custom':
                script_url = templates.get(template, templates['proxy'])
            elif not script_url:
                script_url = "https://raw.githubusercontent.com/gopaybis/cf/refs/heads/main/worker.js"

            # Step 1: Create worker using external API
            create_response = requests.post(
                "https://api.cflifetime.workers.dev/",
                json={
                    "email": email,
                    "globalAPIKey": global_api_key,
                    "workerName": worker_name,
                    "githubUrl": script_url
                }
            )

            result = create_response.json()
            
            transformed_result = {
                "success": result.get('success', False),
                "message": "Worker created successfully" if result.get('success') else result.get('message', 'Failed to create worker'),
                "url": result.get('sub'),
                "vless": result.get('vless'),
                "trojan": result.get('trojan')
            }

            # Step 2: Update with proxy IP for NAUTICA templates
            if template in ['nautica', 'nautica-mod'] and result.get('success'):
                try:
                    proxy_ip = await self.get_random_proxy_ip()
                    
                    # Get original script
                    script_response = requests.get(
                        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}",
                        headers={
                            "X-Auth-Email": email,
                            "X-Auth-Key": global_api_key,
                            "Content-Type": "application/javascript"
                        }
                    )

                    if script_response.ok:
                        script_content = script_response.text
                        
                        # Replace ALL1 with proxy IP
                        modified_script = script_content.replace('ALL1', proxy_ip)
                        
                        # Update worker with modified script
                        update_response = requests.put(
                            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}",
                            headers={
                                "X-Auth-Email": email,
                                "X-Auth-Key": global_api_key,
                                "Content-Type": "application/javascript"
                            },
                            data=modified_script
                        )

                        if update_response.ok:
                            transformed_result["proxyIP"] = proxy_ip
                            transformed_result["message"] = f"Worker created successfully with random proxy IP: {proxy_ip}"
                        else:
                            update_error = update_response.json()
                            transformed_result["message"] = f"Worker created but failed to update proxy IP: {update_error.get('errors', [{}])[0].get('message', 'Unknown error')}"
                    else:
                        script_error = script_response.json()
                        transformed_result["message"] = f"Worker created but failed to fetch script for proxy IP update: {script_error.get('errors', [{}])[0].get('message', 'Unknown error')}"
                except Exception as error:
                    transformed_result["message"] = f"Worker created but failed to update proxy IP: {str(error)}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(transformed_result).encode())
            
        except Exception as error:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Internal server error: {str(error)}"
            }).encode())
    
    async def get_random_proxy_ip(self):
        try:
            response = requests.get(
                'https://raw.githubusercontent.com/gopaybis/Proxylist/refs/heads/main/proxyiplengkap3.txt'
            )
            
            if not response.ok:
                raise Exception(f'Failed to fetch proxy list: {response.status_code}')
            
            text = response.text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if not lines:
                raise Exception('No proxy IPs found in the list')
            
            random_line = random.choice(lines)
            parts = random_line.split(',')
            if len(parts) >= 2:
                ip = parts[0].strip()
                port = parts[1].strip()
                return f"{ip}-{port}"
            else:
                raise Exception(f'Invalid proxy IP format in line: {random_line}')
        except Exception as error:
            return '43.218.77.16-443'
