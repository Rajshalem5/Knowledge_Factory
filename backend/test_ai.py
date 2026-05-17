"""Check if AI gen uses local pool or AI."""
import asyncio
import sys
sys.path.insert(0, ".")

from app.features.questions.ai_service import generate_question, LOCAL_QUESTIONS

async def main():
    q = await generate_question("arrays", "easy")
    print(f"Title: {q.title}")
    
    # Check if title exists in local pool
    all_local = []
    for pool in LOCAL_QUESTIONS.values():
        for lq in pool:
            all_local.append(lq.get("title", ""))
    
    if q.title in all_local:
        print("SOURCE: Local fallback pool")
        print(f"Found in local pool: {q.title}")
    else:
        print(f"SOURCE: AI generated (not in local pool of {len(all_local)} questions)")

asyncio.run(main())
