import httpx
import asyncio
from typing import Dict, Optional
from ..core.config import settings


class Judge0Client:
    """Client for Judge0 API integration"""
    
    LANGUAGE_IDS = {
        "python": 71,  # Python 3
        "java": 62,    # Java
        "cpp": 54      # C++ (GCC 9.2.0)
    }
    
    def __init__(self):
        self.base_url = settings.JUDGE0_API_URL
        self.headers = {
            "X-RapidAPI-Key": settings.JUDGE0_API_KEY,
            "X-RapidAPI-Host": settings.JUDGE0_API_HOST,
            "Content-Type": "application/json"
        }
    
    async def execute_code(
        self,
        code: str,
        language: str,
        stdin: str = "",
        expected_output: Optional[str] = None
    ) -> Dict:
        """
        Execute code using Judge0 API
        
        Args:
            code: Source code to execute
            language: Programming language (python, java, cpp)
            stdin: Standard input
            expected_output: Expected output for comparison
            
        Returns:
            Dict with execution results
        """
        language_id = self.LANGUAGE_IDS.get(language.lower())
        if not language_id:
            raise ValueError(f"Unsupported language: {language}")
        
        # Create submission
        submission_data = {
            "source_code": code,
            "language_id": language_id,
            "stdin": stdin,
        }
        
        if expected_output:
            submission_data["expected_output"] = expected_output
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Submit code
            response = await client.post(
                f"{self.base_url}/submissions",
                json=submission_data,
                headers=self.headers,
                params={"base64_encoded": "false", "wait": "false"}
            )
            response.raise_for_status()
            token = response.json()["token"]
            
            # Poll for result
            max_attempts = 10
            for _ in range(max_attempts):
                await asyncio.sleep(1)
                
                result_response = await client.get(
                    f"{self.base_url}/submissions/{token}",
                    headers=self.headers,
                    params={"base64_encoded": "false"}
                )
                result_response.raise_for_status()
                result = result_response.json()
                
                # Check if processing is complete
                status_id = result.get("status", {}).get("id")
                if status_id not in [1, 2]:  # 1=In Queue, 2=Processing
                    return self._format_result(result)
            
            # Timeout
            return {
                "stdout": None,
                "stderr": "Execution timeout",
                "status": "Timeout",
                "time": None,
                "memory": None
            }
    
    def _format_result(self, result: Dict) -> Dict:
        """Format Judge0 result for API response"""
        status = result.get("status", {})
        
        return {
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr") or result.get("compile_output"),
            "status": status.get("description", "Unknown"),
            "time": result.get("time"),
            "memory": result.get("memory"),
            "status_id": status.get("id")
        }
    
    async def run_test_cases(
        self,
        code: str,
        language: str,
        test_cases: list
    ) -> Dict:
        """
        Run code against multiple test cases
        
        Returns:
            Dict with passed/total counts and details
        """
        results = []
        passed = 0
        
        for i, test_case in enumerate(test_cases):
            result = await self.execute_code(
                code=code,
                language=language,
                stdin=test_case["input"],
                expected_output=test_case["output"]
            )
            
            # Check if output matches (status_id 3 = Accepted)
            is_passed = result.get("status_id") == 3
            if is_passed:
                passed += 1
            
            results.append({
                "test_case": i + 1,
                "passed": is_passed,
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
                "status": result.get("status")
            })
        
        return {
            "passed": passed,
            "total": len(test_cases),
            "percentage": (passed / len(test_cases) * 100) if test_cases else 0,
            "details": results
        }


# Singleton instance
judge0_client = Judge0Client()
