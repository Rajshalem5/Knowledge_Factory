# API Documentation

Base URL: `http://localhost:8000`

## Authentication

**Note**: JWT authentication middleware should be added. For now, APIs use `candidate_id` parameter.

## Endpoints

### 1. Start Assessment

Generate unique assessment for candidate.

**Endpoint**: `POST /api/assessment/start`

**Query Parameters**:
- `candidate_id` (integer, required): Unique candidate identifier

**Response** (200 OK):
```json
{
  "assessment_id": 1,
  "candidate_id": 123,
  "duration_minutes": 40,
  "started_at": "2024-01-15T10:30:00Z"
}
```

**Errors**:
- `400`: Assessment already submitted

**Example**:
```bash
curl -X POST "http://localhost:8000/api/assessment/start?candidate_id=123"
```

---

### 2. Get Assessment Questions

Fetch Monaco-compatible questions (no hidden test cases).

**Endpoint**: `GET /api/assessment/{assessment_id}/questions`

**Path Parameters**:
- `assessment_id` (integer, required)

**Response** (200 OK):
```json
{
  "coding": [
    {
      "id": "coding_1",
      "title": "Two Sum",
      "description": "Given an array...",
      "boilerplate": "def two_sum(nums, target):\n    pass",
      "visible_test_cases": [
        {
          "input": "2 7 11 15\n9",
          "output": "0 1"
        }
      ],
      "default_language": "python"
    }
  ],
  "mcq": [
    {
      "id": "mcq_1",
      "question": "What is the time complexity of binary search?",
      "options": [
        {"id": "A", "text": "O(n)"},
        {"id": "B", "text": "O(log n)"}
      ]
    }
  ]
}
```

**Errors**:
- `404`: Assessment not found
- `400`: Assessment already submitted

---

### 3. Execute Code (Monaco Run Button)

Run code against custom input or test case.

**Endpoint**: `POST /api/code/execute`

**Request Body**:
```json
{
  "code": "print('Hello World')",
  "language": "python",
  "stdin": ""
}
```

**Supported Languages**:
- `python` (Python 3)
- `java` (Java 11)
- `cpp` (C++ GCC 9.2.0)

**Response** (200 OK):
```json
{
  "stdout": "Hello World\n",
  "stderr": null,
  "status": "Accepted",
  "time": "0.023",
  "memory": "3456"
}
```

**Errors**:
- `400`: Invalid language
- `500`: Execution failed

**Example**:
```bash
curl -X POST "http://localhost:8000/api/code/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "nums = list(map(int, input().split()))\nprint(sum(nums))",
    "language": "python",
    "stdin": "1 2 3 4 5"
  }'
```

---

### 4. Submit Assessment

Submit final answers and trigger evaluation.

**Endpoint**: `POST /api/assessment/submit`

**Query Parameters**:
- `assessment_id` (integer, required)

**Request Body**:
```json
{
  "coding": [
    {
      "question_id": "coding_1",
      "code": "def two_sum(nums, target):\n    # solution",
      "language": "python"
    },
    {
      "question_id": "coding_2",
      "code": "def is_palindrome(s):\n    # solution",
      "language": "python"
    }
  ],
  "mcq_answers": {
    "mcq_1": "B",
    "mcq_2": "A",
    "mcq_3": "C"
  }
}
```

**Response** (200 OK):
```json
{
  "message": "Assessment submitted successfully",
  "assessment_id": 1,
  "status": "evaluated"
}
```

**Errors**:
- `404`: Assessment not found
- `400`: Assessment already submitted

**Note**: Evaluation runs synchronously and completes in < 5 seconds.

---

### 5. Get Assessment Result

Retrieve evaluation results.

**Endpoint**: `GET /api/assessment/result`

**Query Parameters**:
- `candidate_id` (integer, required)

**Response** (200 OK):
```json
{
  "total_score": 78.5,
  "coding_score": 85.0,
  "mcq_score": 7,
  "verdict": "PASS",
  "evaluation_details": {
    "coding_results": [
      {
        "question_id": "coding_1",
        "passed": 4,
        "total": 5,
        "percentage": 80.0
      }
    ],
    "mcq_correct": 7,
    "mcq_total": 10
  }
}
```

**Errors**:
- `404`: Result not found

---

## Scoring Formula

### Phase 1 (Current)

```
coding_score = average(test_case_pass_percentage for each problem)
mcq_score = count(correct_answers)
total_score = (coding_score * 0.7) + (mcq_score * 3)
verdict = "PASS" if total_score >= 70 else "FAIL"
```

**Example**:
- Coding Problem 1: 80% test cases passed
- Coding Problem 2: 100% test cases passed
- MCQ: 7/10 correct

```
coding_score = (80 + 100) / 2 = 90
mcq_score = 7
total_score = (90 * 0.7) + (7 * 3) = 63 + 21 = 84
verdict = "PASS"
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Common Status Codes**:
- `200`: Success
- `400`: Bad Request (validation error, already submitted)
- `404`: Not Found (assessment/result not found)
- `500`: Internal Server Error

---

## Rate Limits

**Development**: No limits

**Production** (recommended):
- Code execution: 10 requests/minute per candidate
- Assessment start: 1 request per candidate
- Submit: 1 request per assessment

---

## WebSocket Support (Future)

For real-time proctoring integration:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/assessment/123');
ws.onmessage = (event) => {
  console.log('Proctoring event:', event.data);
};
```

---

## Testing with Postman

Import this collection:

```json
{
  "info": {
    "name": "Knowledge Factory API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Start Assessment",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/assessment/start?candidate_id=123"
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    }
  ]
}
```
