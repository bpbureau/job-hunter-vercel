#!/usr/bin/env python3
"""
Simple test to verify local backend can call Vercel function
"""
import requests
import json

def test_local_to_vercel_integration():
    """Test that local system can call Vercel function"""
    
    # Sample data (like what your local backend would send)
    test_data = {
        "search_terms": ["UX Designer"],
        "location": "United States",
        "resume_text": "UX Designer with 10+ years experience in design systems",
        "preferences": "Remote work preferred, enterprise experience",
        "score_threshold": 60
    }
    
    print("🚀 Testing local-to-Vercel integration...")
    print(f"Sending data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            "https://job-hunter-vercel-rho.vercel.app/api/process-jobs",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ SUCCESS! Vercel returned:")
        print(f"Status: {result.get('status')}")
        print(f"Total jobs: {result.get('total_processed', 0)}")
        
        jobs = result.get('results', [])
        for i, job in enumerate(jobs[:2], 1):
            print(f"\n📋 Job {i}:")
            print(f"  Title: {job.get('job_title', 'N/A')}")
            print(f"  Company: {job.get('company', 'N/A')}")  
            print(f"  Score: {job.get('match_score', 'N/A')}")
            print(f"  Location: {job.get('location', 'N/A')}")
        
        print(f"\n🎉 Integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    test_local_to_vercel_integration()