"""
Quick test script to verify Piston integration is working.
Run this after starting the backend server.
"""

import asyncio
from app.features.code_execution.service import PistonExecutionService
from app.features.code_execution.schemas import TestCase


async def quick_test():
    """Quick smoke test for Piston integration."""
    print("\n🚀 Quick Piston Integration Test\n")
    
    service = PistonExecutionService()
    
    # Test 1: Simple Python execution
    print("1️⃣  Testing Python execution...")
    code = "print('Hello from Piston!')"
    result = await service.execute_code("python", code, "")
    
    if result.status == "SUCCESS":
        print(f"   ✅ SUCCESS: {result.stdout.strip()}")
    else:
        print(f"   ❌ FAILED: {result.stderr}")
        return
    
    # Test 2: Input/Output
    print("\n2️⃣  Testing with input...")
    code = "n = int(input())\nprint(n * 2)"
    result = await service.execute_code("python", code, "21")
    
    if result.status == "SUCCESS" and result.stdout.strip() == "42":
        print(f"   ✅ SUCCESS: Input 21 → Output {result.stdout.strip()}")
    else:
        print(f"   ❌ FAILED: Expected 42, got {result.stdout.strip()}")
        return
    
    # Test 3: Evaluation
    print("\n3️⃣  Testing evaluation...")
    code = "n = int(input())\nprint(n * n)"
    test_cases = [
        TestCase(input="5", expected_output="25"),
        TestCase(input="10", expected_output="100"),
    ]
    
    result = await service.evaluate_code("python", code, test_cases)
    
    if result.passed_tests == 2:
        print(f"   ✅ SUCCESS: {result.passed_tests}/{result.total_tests} tests passed ({result.score_percentage}%)")
    else:
        print(f"   ❌ FAILED: Only {result.passed_tests}/{result.total_tests} tests passed")
        return
    
    print("\n✨ All tests passed! Piston integration is working correctly.\n")


if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. You have internet connection (Piston API is online)")
        print("  2. httpx is installed: pip install httpx")
        print("  3. The backend dependencies are installed\n")
