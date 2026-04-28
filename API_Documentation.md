# Knowledge Factory API Documentation

## Overview

This document describes the REST API for the Knowledge Factory platform, an AI-powered intern hiring and evaluation system.

## API Endpoints

### Authentication Endpoints

#### Login
**POST** `/api/auth/login`

Authenticate a user or candidate and return a JWT token.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "string",
  "user": {
    "id": "uuid",
    "email": "string",
    "name": "string",
    "role": "string",
    "tenant_id": "uuid"
  }
}
```

#### Register Candidate
**POST** `/api/auth/register`

Register a new candidate for the active hiring cycle.

**Request Body:**
```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "college": "string",
  "branch": "string",
  "cgpa": 0,
  "passed_out_year": 0,
  "language_choice": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "string",
  "user": {
    "id": "uuid",
    "email": "string",
    "name": "string",
    "role": "string",
    "tenant_id": "uuid"
  }
}
```

#### Get Current User
**GET** `/api/auth/me`

Get current user profile from JWT.

**Response:**
```json
{
  "id": "uuid",
  "email": "string",
  "name": "string",
  "role": "string",
  "tenant_id": "uuid"
}
```

### Candidate Management Endpoints

#### List Candidates
**GET** `/api/candidates/`

List candidates for the current tenant with pagination.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of items per page (default: 50, max: 100)
- `status` (string, optional): Filter by candidate status

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "string",
      "email": "string",
      "college": "string",
      "branch": "string",
      "cgpa": 0,
      "passed_out_year": 0,
      "language_choice": "string",
      "status": "string",
      "created_at": "datetime",
      "tenant_id": "uuid",
      "cycle_id": "uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 0,
    "total_pages": 0
  }
}
```

#### Get Candidate Detail
**GET** `/api/candidates/{candidate_id}`

Get detailed profile of a candidate.

**Path Parameters:**
- `candidate_id` (UUID): The candidate's unique identifier

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "college": "string",
  "branch": "string",
  "cgpa": 0,
  "passed_out_year": 0,
  "language_choice": "string",
  "status": "string",
  "created_at": "datetime",
  "tenant_id": "uuid",
  "cycle_id": "uuid"
}
```

#### Update Candidate Status
**PATCH** `/api/candidates/{candidate_id}/status`

Manually override candidate status.

**Path Parameters:**
- `candidate_id` (UUID): The candidate's unique identifier

**Request Body:**
```json
{
  "status": "string"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "college": "string",
  "branch": "string",
  "cgpa": 0,
  "passed_out_year": 0,
  "language_choice": "string",
  "status": "string",
  "created_at": "datetime",
  "tenant_id": "uuid",
  "cycle_id": "uuid"
}
```

#### Bulk Upload Candidates
**POST** `/api/candidates/bulk-upload`

Upload a CSV/Excel file and get a preview of records to be created.

**Response:**
```json
{
  "batch_id": "string",
  "total_records": 0,
  "valid_records": 0,
  "invalid_records": 0,
  "preview": [],
  "errors": []
}
```

## Authentication

All API requests require authentication using Bearer tokens.

**Authorization Header:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Error Handling

All error responses follow this structure:
```json
{
  "detail": "string"
}
```

## Status Codes

| Code | Description |
|------|-------------|
| 200  | Successful GET, PUT, PATCH, DELETE requests |
| 201  | Successful POST request |
| 400  | Bad Request - invalid parameters or request |  
| 401  | Unauthorized - invalid or missing authentication |
| 403  | Forbidden - insufficient permissions |
| 404  | Not Found - resource not found |
| 500  | Internal Server Error |

## Rate Limiting

API requests are limited to 1000 requests per hour per user.

## Code Examples

### cURL Examples

#### Login
```bash
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "secure_password"
  }'
```

#### Get Candidates
```bash
curl -X GET https://your-domain.com/api/candidates/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Update Candidate Status
```bash
curl -X PATCH https://your-domain.com/api/candidates/candidate_id/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "shortlisted"
  }'
```

### Python (Requests)

#### Login
```python
import requests

response = requests.post(
    'https://your-domain.com/api/auth/login',
    json={
        'email': 'candidate@example.com',
        'password': 'secure_password'
    }
)

token = response.json()['access_token']
```

#### Get Candidates
```python
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://your-domain.com/api/candidates/',
    headers=headers
)

candidates = response.json()
```

### JavaScript (Fetch)

#### Login
```javascript
const response = await fetch('https://your-domain.com/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'candidate@example.com',
    password: 'secure_password'
  })
});

const data = await response.json();
const token = data.access_token;
```

#### Get Candidates
```javascript
const response = await fetch('https://your-domain.com/api/candidates/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const candidates = await response.json();
```

## API Versions

Currently running version: v1.0

## Support

For support, contact: api-support@knowledgefactory.com