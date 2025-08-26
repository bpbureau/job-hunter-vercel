# Job Hunter Vercel Function

This serverless function processes job searches for the Job Hunter application, handling the heavy API work that would overwhelm rural internet connections.

## What it does:
1. Receives job search parameters from your local system
2. Calls JSearch API to get real job listings
3. Uses Claude AI to score each job against your resume and preferences  
4. Returns only qualifying jobs above your threshold
5. All processing happens in the cloud - your local system just gets results

## Environment Variables Needed:
- `RAPIDAPI_KEY`: Your RapidAPI key for JSearch
- `CLAUDE_API_KEY`: Your Claude API key for job scoring

## Usage:
POST to `/api/process-jobs` with:
```json
{
  "search_terms": ["UX Designer", "Product Designer"],
  "location": "United States", 
  "resume_text": "Your resume content...",
  "preferences": "Your job preferences...",
  "score_threshold": 75
}
```