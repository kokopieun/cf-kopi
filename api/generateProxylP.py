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
    
    def do_GET(self):
        try:
            proxy_ip = self.get_random_proxy_ip()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "proxyIP": proxy_ip
            }).encode())
            
        except Exception as error:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Failed to generate proxy IP: {str(error)}"
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
