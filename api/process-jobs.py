"""
Vercel serverless function to process job searches
This handles the heavy API work that would overwhelm rural internet
"""
import json
import requests
from http.server import BaseHTTPRequestHandler
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract query parameters
            search_terms = data.get('search_terms', ['UX Designer'])
            location = data.get('location', 'United States')
            resume_text = data.get('resume_text', '')
            preferences = data.get('preferences', '')
            score_threshold = data.get('score_threshold', 70)
            
            # Process jobs (simplified for testing)
            results = self.process_job_search_simple(search_terms, location)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success',
                'results': results,
                'total_processed': len(results)
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """Handle GET requests for testing"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'success',
            'message': 'Job Hunter Vercel Function is running!'
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def process_job_search_simple(self, search_terms, location):
        """Simplified job search for testing"""
        # For now, return mock data to test deployment
        return [
            {
                'job_title': f'{search_terms[0]} - Remote',
                'company': 'Test Company',
                'location': location,
                'match_score': 85,
                'source': 'vercel_function_test'
            }
        ]