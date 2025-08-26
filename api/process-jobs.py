"""
Vercel serverless function to process job searches
This handles the heavy API work that would overwhelm rural internet
"""
import json
import requests
from http.server import BaseHTTPRequestHandler
import os
import re

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
            
            # Process jobs with real APIs
            results = self.process_job_search_real(search_terms, location, resume_text, preferences, score_threshold)
            
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
    
    def process_job_search_real(self, search_terms, location, resume_text, preferences, score_threshold):
        """Real job search with JSearch API + Claude AI scoring"""
        try:
            # Get API keys from environment
            rapidapi_key = os.environ.get('RAPIDAPI_KEY')
            claude_api_key = os.environ.get('CLAUDE_API_KEY')
            
            if not rapidapi_key:
                return [{'error': 'RAPIDAPI_KEY not configured'}]
            if not claude_api_key:
                return [{'error': 'CLAUDE_API_KEY not configured'}]
            
            qualifying_jobs = []
            
            # Process first search term only (to keep it simple for now)
            search_term = search_terms[0] if search_terms else 'UX Designer'
            
            # Fetch jobs from JSearch
            jobs = self.fetch_jobs_from_jsearch(search_term, location, rapidapi_key)
            
            # Score jobs with Claude (limit to first 3 jobs to avoid timeout)
            for job in jobs[:3]:
                try:
                    score = self.score_job_with_claude(job, resume_text, preferences, claude_api_key)
                    
                    if score >= score_threshold:
                        job_result = {
                            'job_title': job.get('job_title', ''),
                            'company': job.get('employer_name', ''),
                            'location': f"{job.get('job_city', '')}, {job.get('job_state', '')}",
                            'job_url': job.get('job_apply_link', ''),
                            'job_description': job.get('job_description', '')[:500],  # Limit description length
                            'match_score': score,
                            'source': 'jsearch_api',
                            'remote': job.get('job_is_remote', False),
                            'posted_date': job.get('job_posted_at', '')
                        }
                        qualifying_jobs.append(job_result)
                        
                except Exception as e:
                    print(f"Error scoring job {job.get('job_title', 'Unknown')}: {e}")
                    continue
            
            return qualifying_jobs
            
        except Exception as e:
            return [{'error': f'Job processing failed: {str(e)}'}]
    
    def fetch_jobs_from_jsearch(self, search_term, location, api_key):
        """Fetch jobs from JSearch API"""
        url = "https://jsearch.p.rapidapi.com/search"
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        params = {
            "query": search_term,
            "page": "1",
            "num_pages": "1",  # Keep it simple - one page only
            "date_posted": "week",
            "location": location
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def score_job_with_claude(self, job, resume_text, preferences, claude_api_key):
        """Score job using Claude AI"""
        # Simplified Claude API call without the anthropic library
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': claude_api_key,
            'anthropic-version': '2023-06-01'
        }
        
        prompt = f"""Rate this job for a candidate based on their preferences and resume.

CANDIDATE RESUME:
{resume_text[:1500]}

CANDIDATE PREFERENCES:
{preferences}

JOB POSTING:
Title: {job.get('job_title', '')}
Company: {job.get('employer_name', '')}
Location: {job.get('job_city', '')}, {job.get('job_state', '')}
Description: {job.get('job_description', '')[:1000]}

Provide a score from 0-100 and return ONLY a JSON object:
{{"score": 85, "reasoning": "Good match because..."}}"""

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 300,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['content'][0]['text']
            
            # Extract JSON score
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                score_data = json.loads(json_match.group())
                return int(score_data.get('score', 0))
            
            return 0
            
        except Exception as e:
            print(f"Claude API error: {e}")
            return 50  # Default score if AI fails

    def process_job_search_simple(self, search_terms, location):
        """Simplified job search for testing"""
        # Keep this as fallback
        return [
            {
                'job_title': f'{search_terms[0]} - Remote',
                'company': 'Test Company',
                'location': location,
                'match_score': 85,
                'source': 'vercel_function_test'
            }
        ]