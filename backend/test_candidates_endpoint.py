#!/usr/bin/env python3
"""Test candidates endpoint."""

import requests

def test_candidates_endpoint():
    print('Testing candidates endpoint...')
    response = requests.get('http://localhost:8000/api/candidates/')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f'✅ Candidates endpoint working - found {len(items)} candidates')
        if items:
            candidate = items[0]
            print(f'Sample candidate: {candidate.get("name", "N/A")} - CGPA: {candidate.get("cgpa", "N/A")}')
    else:
        print(f'❌ Error: {response.text}')

if __name__ == "__main__":
    test_candidates_endpoint()