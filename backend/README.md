# Knowledge Factory - Round 2 Assessment Backend

Production-ready FastAPI backend for AI-powered coding assessments.

## Architecture

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── assessment.py      # Assessment lifecycle APIs
│   │       └── code_execution.py  # Monaco code execution
│   ├── core/
│   │   ├── config.py              # Settings management
│   │   └── database.py            # Database connection
│   ├── models/
│   │   └── assessment.py          # SQLAlchemy models
│   ├── schemas/
│   │   └── assessment.py          # Pydantic schemas
│   ├── services/
│   │   ├── question_bank.py       # Question generation
│   │   ├── judge0_client.py       # Judge0 integration
│   │   └── evaluation_service.py  # Evaluation logic
│   └── main.py                    # FastAPI app
├── requirements.txt
└── .env.example
```

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb knowledge_factory

# Run migrations
alembic upgrade head
```

### 4. Get Judge0 API Key

1. Go to [RapidAPI Judge0](https://rapidapi.com/judge0-official/api/judge0-ce)
2. Subscribe (free tier available)
3. Copy API key to `.env`

### 5. Run Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## API Endpoints

### Assessment Lifecycle

**Start Assessment**
```http
POST /api/assessment/start?candidate_id=123
```

**Get Questions (Monaco-compatible)**
```http
GET /api/assessment/{assessment_id}/questions
```

**Submit Assessment**
```http
POST /api/assessment/submit?assessment_id=1
{
  "coding": [
    {
      "question_id": "coding_1",
      "code": "def two_sum(nums, target): ...",
      "language": "python"
    }
  ],
  "mcq_answers": {
    "mcq_1": "B",
    "mcq_2": "A"
  }
}
```

**Get Result**
```http
GET /api/assessment/result?candidate_id=123
```

### Code Execution (Monaco)

**Run Code**
```http
POST /api/code/execute
{
  "code": "print('Hello')",
  "language": "python",
  "stdin": ""
}
```

## Database Schema

### assessments
- `id`: Primary key
- `candidate_id`: Unique candidate identifier
- `questions_json`: JSONB (coding + MCQ questions)
- `status`: Enum (not_started, in_progress, submitted, evaluated)
- `started_at`, `ended_at`: Timestamps

### submissions
- `id`: Primary key
- `assessment_id`: Foreign key
- `payload_json`: JSONB (code + answers)
- `submitted_at`: Timestamp

### scores
- `id`: Primary key
- `candidate_id`: Unique
- `assessment_id`: Foreign key
- `correctness`: Coding score (0-100)
- `mcq_total`: MCQ correct count
- `weighted_total`: Final score
- `verdict`: PASS/FAIL
- `evaluation_details`: JSONB

## Evaluation Logic

### Phase 1 (Current)
- **Coding**: Judge0 test case pass rate
- **MCQ**: Correct answer matching
- **Formula**: `(avg_correctness * 0.7) + (mcq_total * 3)`
- **Threshold**: 70 points

### Phase 2 (Interface Ready)
- Plug in `AIEvaluator` class
- Add code quality, efficiency, edge cases
- No API or DB changes needed

## Performance

- Evaluation completes in < 5 seconds
- Parallel Judge0 calls for test cases
- Optimized question fetching for Monaco

## Security

- JWT authentication (add middleware)
- Input validation via Pydantic
- Code execution sandboxed via Judge0
- No hidden test cases exposed to frontend

## Monaco Integration

Questions API returns:
- Boilerplate code per language
- Visible test cases only
- Default language selection
- Optimized JSON structure

## Testing

```bash
# Run tests
pytest

# Test Judge0 connection
python -m app.services.judge0_client
```

## Production Deployment

1. Set strong `SECRET_KEY`
2. Configure production database
3. Enable HTTPS
4. Add rate limiting
5. Setup monitoring
6. Configure CORS properly
