from fastapi import APIRouter, HTTPException, status
from ...schemas.assessment import CodeExecuteRequest, CodeExecuteResponse
from ...services.judge0_client import judge0_client

router = APIRouter(prefix="/api/code", tags=["code-execution"])


@router.post("/execute", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest):
    """
    Execute code for Monaco "Run Code" button
    
    - Runs code against custom input or visible test case
    - Returns stdout, stderr, execution time, memory
    - Does NOT affect final evaluation
    """
    try:
        result = await judge0_client.execute_code(
            code=request.code,
            language=request.language,
            stdin=request.stdin
        )
        
        return CodeExecuteResponse(
            stdout=result.get("stdout"),
            stderr=result.get("stderr"),
            status=result.get("status", "Unknown"),
            time=result.get("time"),
            memory=result.get("memory")
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )
