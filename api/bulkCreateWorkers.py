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
            accounts = data.get('accounts')
            worker_name = data.get('workerName')
            worker_script_url = data.get('workerScriptUrl')
            template = data.get('template')
            
            if not accounts or not isinstance(accounts, list) or not worker_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Accounts array and worker name are required"
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

            results = []
            for account in accounts:
                try:
                    # Step 1: Create worker using external API
                    response = requests.post(
                        "https://api.cflifetime.workers.dev/",
                        json={
                            "email": account.get('email'),
                            "globalAPIKey": account.get('apiKey'),
                            "workerName": worker_name,
                            "githubUrl": script_url
                        }
                    )

                    result = response.json()
                    
                    result_data = {
                        "email": account.get('email'),
                        "success": result.get('success', False),
                        "message": "Created successfully" if result.get('success') else result.get('message', 'Failed'),
                        "url": result.get('sub'),
                        "vless": result.get('vless'),
                        "trojan": result.get('trojan')
                    }

                    # Step 2: Update with proxy IP for NAUTICA templates
                    if template in ['nautica', 'nautica-mod'] and result.get('success'):
                        try:
                            proxy_ip = self.get_random_proxy_ip()
                            
                            # Get original script
                            script_response = requests.get(
                                f"https://api.cloudflare.com/client/v4/accounts/{account.get('accountId')}/workers/scripts/{worker_name}",
                                headers={
                                    "X-Auth-Email": account.get('email'),
                                    "X-Auth-Key": account.get('apiKey'),
                                    "Content-Type": "application/javascript"
                                }
                            )

                            if script_response.ok:
                                script_content = script_response.text
                                
                                # Replace ALL1 with proxy IP
                                modified_script = script_content.replace('ALL1', proxy_ip)
                                
                                # Update worker with modified script
                                update_response = requests.put(
                                    f"https://api.cloudflare.com/client/v4/accounts/{account.get('accountId')}/workers/scripts/{worker_name}",
                                    headers={
                                        "X-Auth-Email": account.get('email'),
                                        "X-Auth-Key": account.get('apiKey'),
                                        "Content-Type": "application/javascript"
                                    },
                                    data=modified_script
                                )

                                if update_response.ok:
                                    result_data["proxyIP"] = proxy_ip
                                    result_data["message"] = f"Created successfully with random proxy IP: {proxy_ip}"
                                else:
                                    update_error = update_response.json()
                                    result_data["message"] = f"Created but failed to update proxy IP: {update_error.get('errors', [{}])[0].get('message', 'Unknown error')}"
                            else:
                                script_error = script_response.json()
                                result_data["message"] = f"Created but failed to fetch script for proxy IP update: {script_error.get('errors', [{}])[0].get('message', 'Unknown error')}"
                        except Exception as error:
                            result_data["message"] = f"Created but failed to update proxy IP: {str(error)}"

                    results.append(result_data)
                    
                except Exception as error:
                    results.append({
                        "email": account.get('email'),
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
    
    def get_random_proxy_ip(self):
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
