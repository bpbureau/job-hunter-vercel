"""
Vercel serverless function to process job searches
This handles the heavy API work that would overwhelm rural internet
"""
import json
import requests
import anthropic
from typing import Dict, List
import os

def handler(request):
    """
    Vercel function handler
    Receives job query data, processes with JSearch + Claude, returns results
    """
    try:
        # Parse request data
        if hasattr(request, 'json'):
            data = request.json
        else:
            data = json.loads(request.body)
        
        # Extract query parameters
        search_terms = data.get('search_terms', ['UX Designer'])
        location = data.get('location', 'United States')
        resume_text = data.get('resume_text', '')
        preferences = data.get('preferences', '')
        score_threshold = data.get('score_threshold', 70)
        
        # Process jobs
        results = process_job_search(
            search_terms=search_terms,
            location=location,
            resume_text=resume_text,
            preferences=preferences,
            score_threshold=score_threshold
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'results': results,
                'total_processed': len(results)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }

def process_job_search(search_terms: List[str], location: str, resume_text: str, 
                      preferences: str, score_threshold: int) -> List[Dict]:
    """
    Process job search with JSearch API + Claude AI scoring
    """
    # Get API keys from environment
    rapidapi_key = os.environ.get('RAPIDAPI_KEY')
    claude_api_key = os.environ.get('CLAUDE_API_KEY')
    
    if not rapidapi_key or not claude_api_key:
        raise Exception("Missing API keys")
    
    # Initialize Claude client
    claude_client = anthropic.Anthropic(api_key=claude_api_key)
    
    all_qualifying_jobs = []
    
    # Process each search term
    for search_term in search_terms[:3]:  # Limit to 3 terms
        # Call JSearch API
        jobs = fetch_jobs_from_jsearch(search_term, location, rapidapi_key)
        
        # Score each job with Claude AI
        for job in jobs[:10]:  # Limit to 10 jobs per term
            score = score_job_with_claude(job, resume_text, preferences, claude_client)
            
            if score >= score_threshold:
                job['match_score'] = score
                all_qualifying_jobs.append(job)
    
    return all_qualifying_jobs

def fetch_jobs_from_jsearch(search_term: str, location: str, api_key: str) -> List[Dict]:
    """
    Fetch jobs from JSearch API
    """
    url = "https://jsearch.p.rapidapi.com/search"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
        "query": search_term,
        "page": "1",
        "num_pages": "2",
        "date_posted": "week",
        "location": location
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data.get('data', [])

def score_job_with_claude(job: Dict, resume_text: str, preferences: str, 
                         claude_client) -> int:
    """
    Score job using Claude AI
    """
    prompt = f"""
Rate this job for a candidate based on their preferences and resume.

CANDIDATE RESUME:
{resume_text[:2000]}

CANDIDATE PREFERENCES:
{preferences}

JOB POSTING:
Title: {job.get('job_title', '')}
Company: {job.get('employer_name', '')}
Location: {job.get('job_city', '')}, {job.get('job_state', '')}
Description: {job.get('job_description', '')[:1000]}

Provide a score from 0-100 and return ONLY a JSON object:
{{"score": 85, "reasoning": "Good match because..."}}
"""

    try:
        message = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return int(result.get('score', 0))
        
        return 0
        
    except Exception as e:
        print(f"AI scoring error: {e}")
        return 50  # Default score if AI fails