"""
Standalone test for Piston integration - doesn't require app imports.
This tests the Piston API directly without loading the FastAPI app.
"""

import asyncio
import httpx


class SimplePistonService:
    """Simplified Piston service for testing."""
    
    # Your ngrok Piston engine URL
    PISTON_URL = "https://diminish-overcook-venus.ngrok-free.dev/api/v2/execute"
    
    LANGUAGE_VERSIONS = {
        "python": "3.12.0",
        "java": "15.0.2",
        "cpp": "10.2.0",
        "javascript": "18.15.0",
        "c": "10.2.0",
    }
    
    async def execute_code(self, language: str, code: str, stdin: str = ""):
        """Execute code using Piston API."""
        payload = {
            "language": language,
            "version": self.LANGUAGE_VERSIONS.get(language, "*"),
            "files": [{"content": code}],
            "stdin": stdin
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.PISTON_URL, json=payload)
                response.raise_for_status()
                data = response.json()
                
                run_data = data.get("run", {})
                compile_data = data.get("compile", {})
                
                # Check for compilation errors
                if compile_data.get("stderr"):
                    return {
                        "status": "COMPILE_ERROR",
                        "stdout": compile_data.get("stdout", ""),
                        "stderr": compile_data.get("stderr", ""),
                    }
                
                # Check for runtime errors
                if run_data.get("stderr"):
                    return {
                        "status": "RUNTIME_ERROR",
                        "stdout": run_data.get("stdout", ""),
                        "stderr": run_data.get("stderr", ""),
                    }
                
                return {
                    "status": "SUCCESS",
                    "stdout": run_data.get("stdout", ""),
                    "stderr": run_data.get("stderr", ""),
                }
                
        except httpx.TimeoutException:
            return {
                "status": "TIMEOUT",
                "stdout": "",
                "stderr": "Execution timed out",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "stdout": "",
                "stderr": f"Error: {str(e)}",
            }


async def test_basic_execution():
    """Test basic code execution."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Python Execution")
    print("=" * 60)
    
    service = SimplePistonService()
    
    code = "print('Hello from Piston!')"
    result = await service.execute_code("python", code, "")
    
    print(f"Status: {result['status']}")
    print(f"Output: {result['stdout'].strip()}")
    
    if result['status'] == 'SUCCESS':
        print("✅ PASSED")
        return True
    else:
        print(f"❌ FAILED: {result['stderr']}")
        return False


async def test_with_input():
    """Test execution with input."""
    print("\n" + "=" * 60)
    print("TEST 2: Python with Input")
    print("=" * 60)
    
    service = SimplePistonService()
    
    code = "n = int(input())\nprint(n * 2)"
    result = await service.execute_code("python", code, "21")
    
    print(f"Status: {result['status']}")
    print(f"Input: 21")
    print(f"Output: {result['stdout'].strip()}")
    print(f"Expected: 42")
    
    if result['status'] == 'SUCCESS' and result['stdout'].strip() == '42':
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        return False


async def test_multiple_languages():
    """Test multiple programming languages."""
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Languages")
    print("=" * 60)
    
    service = SimplePistonService()
    
    tests = {
        "python": "n = int(input())\narr = list(map(int, input().split()))\nprint(sum(arr))",
        "java": """import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        long sum = 0;
        for(int i = 0; i < n; i++) {
            sum += sc.nextLong();
        }
        System.out.println(sum);
    }
}""",
        "cpp": """#include <iostream>
using namespace std;
int main() {
    int n;
    cin >> n;
    long long sum = 0, x;
    for(int i = 0; i < n; i++) {
        cin >> x;
        sum += x;
    }
    cout << sum;
    return 0;
}"""
    }
    
    stdin = "5\n1 2 3 4 5"
    expected = "15"
    
    all_passed = True
    
    for lang, code in tests.items():
        print(f"\nTesting {lang.upper()}...")
        result = await service.execute_code(lang, code, stdin)
        
        if result['status'] == 'SUCCESS' and result['stdout'].strip() == expected:
            print(f"  ✅ PASSED - Output: {result['stdout'].strip()}")
        else:
            print(f"  ❌ FAILED - Status: {result['status']}")
            if result['stderr']:
                print(f"  Error: {result['stderr'][:100]}")
            all_passed = False
    
    return all_passed


async def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("TEST 4: Error Handling")
    print("=" * 60)
    
    service = SimplePistonService()
    
    # Syntax error
    print("\nTesting syntax error...")
    code = "print('hello'"  # Missing closing parenthesis
    result = await service.execute_code("python", code, "")
    
    if result['status'] in ['RUNTIME_ERROR', 'COMPILE_ERROR']:
        print("  ✅ PASSED - Error detected correctly")
        error_passed = True
    else:
        print("  ❌ FAILED - Error not detected")
        error_passed = False
    
    # Runtime error
    print("\nTesting runtime error (division by zero)...")
    code = "x = int(input())\nprint(10 / x)"
    result = await service.execute_code("python", code, "0")
    
    if result['status'] == 'RUNTIME_ERROR':
        print("  ✅ PASSED - Runtime error detected")
        runtime_passed = True
    else:
        print("  ❌ FAILED - Runtime error not detected")
        runtime_passed = False
    
    return error_passed and runtime_passed


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 PISTON CODE EXECUTION TEST")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(await test_basic_execution())
        results.append(await test_with_input())
        results.append(await test_multiple_languages())
        results.append(await test_error_handling())
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nTests Passed: {passed}/{total}")
        
        if passed == total:
            print("\n✨ All tests passed! Piston integration is working correctly.\n")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("  1. You have internet connection (Piston API is online)")
        print("  2. httpx is installed: pip install httpx")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
