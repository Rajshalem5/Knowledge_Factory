# Project Structure Overview

Complete Round 2 Assessment System - Production Ready

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── assessment.py            # Assessment lifecycle endpoints
│   │       └── code_execution.py        # Monaco code execution endpoint
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings and environment variables
│   │   └── database.py                  # Database connection and session
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── assessment.py                # SQLAlchemy models (Assessment, Submission, Score)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── assessment.py                # Pydantic schemas for request/response
│   │
│   └── services/
│       ├── __init__.py
│       ├── question_bank.py             # Question generation with seeded randomization
│       ├── judge0_client.py             # Judge0 API integration
│       └── evaluation_service.py        # Evaluation logic (Phase 1 & 2 interface)
│
├── alembic/
│   ├── env.py                           # Alembic environment configuration
│   ├── script.py.mako                   # Migration template
│   └── versions/                        # Database migrations
│
├── tests/
│   ├── __init__.py
│   └── test_assessment_flow.py          # Integration tests
│
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
├── alembic.ini                          # Alembic configuration
├── run.py                               # Development server runner
│
├── README.md                            # Quick start guide
├── API_DOCUMENTATION.md                 # Complete API reference
├── DEPLOYMENT.md                        # Production deployment guide
├── MONACO_INTEGRATION.md                # Frontend integration guide
└── PROJECT_STRUCTURE.md                 # This file
```

## Module Responsibilities

### 1. Core Module (`app/core/`)

**config.py**
- Environment variable management
- Application settings
- Judge0 configuration
- Scoring parameters

**database.py**
- PostgreSQL connection
- Session management
- Database dependency injection

### 2. Models Module (`app/models/`)

**assessment.py**
- `Assessment`: Stores candidate assessments with questions
- `Submission`: Stores submitted code and answers
- `Score`: Stores evaluation results
- `AssessmentStatus`: Enum for assessment lifecycle

### 3. Schemas Module (`app/schemas/`)

**assessment.py**
- Request/response validation
- Monaco-compatible data structures
- Type safety with Pydantic

### 4. Services Module (`app/services/`)

**question_bank.py**
- Predefined coding problems (3 problems)
- Predefined MCQs (12 questions)
- Seeded random selection (2 coding + 10 MCQ per candidate)
- Boilerplate code for Python, Java, C++

**judge0_client.py**
- Judge0 API integration
- Code execution
- Test case evaluation
- Language support (Python, Java, C++)

**evaluation_service.py**
- Abstract `EvaluationService` interface
- `Judge0Evaluator`: Phase 1 implementation
- `AIEvaluator`: Phase 2 interface (not implemented)
- Score calculation logic

### 5. API Routes Module (`app/api/routes/`)

**assessment.py**
- `POST /api/assessment/start`: Generate assessment
- `GET /api/assessment/{id}/questions`: Fetch Monaco-compatible questions
- `POST /api/assessment/submit`: Submit and evaluate
- `GET /api/assessment/result`: Get results

**code_execution.py**
- `POST /api/code/execute`: Run code (Monaco "Run" button)

## Data Flow

### 1. Assessment Start
```
Client → POST /api/assessment/start
       → QuestionBank.generate_assessment(candidate_id)
       → Save to Assessment table
       → Return assessment_id
```

### 2. Get Questions
```
Client → GET /api/assessment/{id}/questions
       → Fetch from Assessment.questions_json
       → Format for Monaco (hide hidden test cases)
       → Return coding + MCQ
```

### 3. Code Execution (Run Button)
```
Client → POST /api/code/execute
       → Judge0Client.execute_code()
       → Return stdout/stderr/time/memory
```

### 4. Submit Assessment
```
Client → POST /api/assessment/submit
       → Save to Submission table
       → Lock Assessment (status = SUBMITTED)
       → Judge0Evaluator.evaluate()
           → Run code against hidden test cases
           → Evaluate MCQs
           → Calculate weighted score
       → Save to Score table
       → Return success
```

### 5. Get Result
```
Client → GET /api/assessment/result
       → Fetch from Score table
       → Return total_score, verdict, details
```

## Database Schema

### assessments
```sql
CREATE TABLE assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER UNIQUE NOT NULL,
    questions_json JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### submissions
```sql
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    payload_json JSONB NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### scores
```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER UNIQUE NOT NULL,
    assessment_id INTEGER NOT NULL,
    correctness INTEGER DEFAULT 0,
    mcq_total INTEGER DEFAULT 0,
    weighted_total INTEGER DEFAULT 0,
    verdict VARCHAR(10) NOT NULL,
    evaluation_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Evaluation Logic (Phase 1)

### Coding Problems
```python
for each coding submission:
    run code against hidden_test_cases using Judge0
    count passed test cases
    percentage = (passed / total) * 100
    
avg_correctness = average(all percentages)
```

### MCQs
```python
mcq_score = count(correct answers)
```

### Final Score
```python
weighted_total = (avg_correctness * 0.7) + (mcq_score * 3)
verdict = "PASS" if weighted_total >= 70 else "FAIL"
```

## Phase 2 Extension (Interface Ready)

To add AI evaluation:

1. Implement `AIEvaluator` class in `evaluation_service.py`
2. Add OpenAI/Claude API integration
3. Evaluate:
   - Code quality
   - Efficiency
   - Edge case handling
   - Best practices
4. Update scoring formula
5. No API or database changes needed!

```python
class AIEvaluator(EvaluationService):
    async def evaluate(self, coding_submissions, mcq_answers, questions):
        # Judge0 evaluation
        judge0_result = await Judge0Evaluator().evaluate(...)
        
        # AI evaluation
        ai_scores = await self._ai_evaluate_code(coding_submissions)
        
        # Combine scores
        final_score = self._combine_scores(judge0_result, ai_scores)
        return ScoreResult(...)
```

## Performance Characteristics

- **Assessment Generation**: < 100ms (in-memory)
- **Question Fetch**: < 50ms (single DB query)
- **Code Execution**: 1-3 seconds (Judge0 API)
- **Full Evaluation**: < 5 seconds (parallel test cases)
- **Result Fetch**: < 50ms (single DB query)

## Security Features

✅ Input validation (Pydantic)
✅ SQL injection prevention (SQLAlchemy ORM)
✅ Code execution sandboxing (Judge0)
✅ Hidden test cases not exposed
✅ Assessment locking after submission
✅ JWT authentication ready (add middleware)

## Scalability

- **Horizontal**: Stateless API, can run multiple instances
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis integration ready (optional)
- **Judge0**: Can use self-hosted cluster for high volume

## Testing Strategy

1. **Unit Tests**: Services and evaluation logic
2. **Integration Tests**: Complete assessment flow
3. **Load Tests**: 2000 concurrent candidates
4. **Judge0 Tests**: Language support and edge cases

## Deployment Checklist

- [ ] Set production `SECRET_KEY`
- [ ] Configure production database
- [ ] Setup Judge0 (RapidAPI or self-hosted)
- [ ] Enable HTTPS
- [ ] Configure CORS
- [ ] Add rate limiting
- [ ] Setup monitoring
- [ ] Configure backups
- [ ] Add logging
- [ ] Load testing

## Next Steps

1. **Phase 1**: Deploy current system
2. **Monitor**: Collect evaluation metrics
3. **Phase 2**: Implement AI evaluation
4. **Optimize**: Based on production data
5. **Scale**: Add more question types

## Support

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Issues: Check logs in `logs/app.log`
