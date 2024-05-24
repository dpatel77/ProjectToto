import http.server
import socketserver
import json
import time
import os

PORT = 8000
FILE_NAME = 'demo_data.json'

class StreamHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Get the directory of the current script
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, FILE_NAME)

        # Load the JSON data for the full day
        try:
            with open(file_path, 'r') as f:
                full_day_data = json.load(f)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')
            return

        # Sort the data by time in descending order
        full_day_data = sorted(full_day_data, key=lambda x: x['time'], reverse=False)
        
        # Send headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Stream the data record by record
        for record in full_day_data:
            self.wfile.write(json.dumps(record).encode('utf-8'))
            self.wfile.write(b'\n')
            self.wfile.flush()
            time.sleep(.1)  # Simulate a delay for streaming effect

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), StreamHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
