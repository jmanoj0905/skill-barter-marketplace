# PART 1: DATA SCHEMAS

These are the exact shapes of all data objects. Every endpoint returns these. No variations.

## Schema: User

```json
{
  "user_id": "integer",
  "email": "string (unique, lowercase, max 255 chars)",
  "name": "string (1-100 chars)",
  "trust_score": "float (0.0 - 1.0, default 0.30)",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "user_id": 1,
  "email": "alice@example.com",
  "name": "Alice Chen",
  "trust_score": 0.62,
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-20T14:30:00Z"
}
```

**Used in**: Every endpoint that returns user info

---

## Schema: Skill

```json
{
  "skill_id": "integer",
  "user_id": "integer (foreign key to User)",
  "skill_name": "string (lowercase, trimmed, 3-50 chars)",
  "skill_type": "enum: 'offer' | 'want'",
  "proficiency_level": "enum: 'beginner' | 'intermediate' | 'advanced' | 'expert' (optional)",
  "created_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "skill_id": 42,
  "user_id": 1,
  "skill_name": "python programming",
  "skill_type": "offer",
  "proficiency_level": "advanced",
  "created_at": "2026-01-20T10:15:00Z"
}
```

**Used in**: Skills endpoints, matching, QA

---

## Schema: Wallet

```json
{
  "wallet_id": "integer",
  "user_id": "integer (unique, foreign key)",
  "available_balance": "integer (credits)",
  "locked_balance": "integer (credits)",
  "total_earned": "integer (credits, cumulative)",
  "total_spent": "integer (credits, cumulative)",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "wallet_id": 1,
  "user_id": 1,
  "available_balance": 42,
  "locked_balance": 28,
  "total_earned": 100,
  "total_spent": 30,
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-20T14:30:00Z"
}
```

**Used in**: Wallet endpoints, escrow, settlement

---

## Schema: Barter

```json
{
  "barter_id": "integer",
  "user_a_id": "integer (foreign key to User)",
  "user_b_id": "integer (foreign key to User)",
  "skill_a": "string (what user_a teaches)",
  "skill_b": "string (what user_b teaches)",
  "status": "enum: 'proposed' | 'confirmed' | 'escrow_locked' | 'active' | 'completed' | 'settled' | 'disputed'",
  "proposed_at": "ISO8601 timestamp",
  "scheduled_time": "ISO8601 timestamp (nullable)",
  "agreed_duration_minutes": "integer (nullable)",
  "actual_start_time": "ISO8601 timestamp (nullable)",
  "actual_end_time": "ISO8601 timestamp (nullable)",
  "actual_duration_minutes": "integer (nullable)"
}
```

**Example**:
```json
{
  "barter_id": 1,
  "user_a_id": 1,
  "user_b_id": 2,
  "skill_a": "graphic design",
  "skill_b": "python programming",
  "status": "settled",
  "proposed_at": "2026-01-20T10:30:00Z",
  "scheduled_time": "2026-01-21T14:00:00Z",
  "agreed_duration_minutes": 90,
  "actual_start_time": "2026-01-21T14:05:00Z",
  "actual_end_time": "2026-01-21T15:35:00Z",
  "actual_duration_minutes": 90
}
```

**Status progression** (MUST follow this order):
- `proposed` → `confirmed` → `escrow_locked` → `active` → `completed` → `settled`
- OR `disputed` (from any state, manual intervention)

**Used in**: All barter endpoints

---

## Schema: Escrow

```json
{
  "escrow_id": "integer",
  "barter_id": "integer (foreign key)",
  "user_id": "integer (foreign key)",
  "amount": "integer (credits, immutable once locked)",
  "status": "enum: 'locked' | 'released' | 'penalized' | 'disputed'",
  "created_at": "ISO8601 timestamp",
  "released_at": "ISO8601 timestamp (nullable)"
}
```

**Example**:
```json
{
  "escrow_id": 1,
  "barter_id": 1,
  "user_id": 1,
  "amount": 28,
  "status": "released",
  "created_at": "2026-01-21T14:00:00Z",
  "released_at": "2026-01-21T15:40:00Z"
}
```

**Rule**: One escrow per user per barter (two escrows total per barter)

**Used in**: Escrow endpoints, settlement

---

## Schema: Feedback

```json
{
  "feedback_id": "integer",
  "barter_id": "integer (foreign key)",
  "respondent_id": "integer (who gave feedback)",
  "satisfaction_rating": "integer (1-5, required)",
  "teaching_quality_rating": "integer (1-5, required)",
  "did_complete_scope": "enum: 'yes' | 'no' | 'partial'",
  "comment": "string (optional, max 1000 chars)",
  "submitted_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "feedback_id": 1,
  "barter_id": 1,
  "respondent_id": 1,
  "satisfaction_rating": 5,
  "teaching_quality_rating": 4,
  "did_complete_scope": "yes",
  "comment": "Great session, learned a lot!",
  "submitted_at": "2026-01-21T15:45:00Z"
}
```

**Rules**:
- Both ratings required (1-5 each)
- One feedback per user per barter (two feedbacks total)
- Ratings must be integers, not floats

**Used in**: Feedback endpoints, QA verification

---

## Schema: QA Verdict

```json
{
  "verdict_id": "integer",
  "barter_id": "integer (foreign key)",
  "verdict_type": "enum: 'SUCCESSFUL' | 'PARTIAL' | 'DISPUTE'",
  "confidence_score": "float (0.0 - 1.0)",
  "checks": {
    "duration_check": "boolean (actual >= 80% of agreed?)",
    "feedback_check": "boolean (both ratings >= 3?)",
    "presence_check": "boolean (both users confirmed present?)"
  },
  "explanation": "string (human-readable reason for verdict)",
  "created_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "verdict_id": 1,
  "barter_id": 1,
  "verdict_type": "SUCCESSFUL",
  "confidence_score": 0.98,
  "checks": {
    "duration_check": true,
    "feedback_check": true,
    "presence_check": true
  },
  "explanation": "All checks passed. Both users gave positive feedback. Session duration 90 minutes (100% of agreed 90 minutes).",
  "created_at": "2026-01-21T15:50:00Z"
}
```

**Verdict logic**:
- SUCCESSFUL: All 3 checks = true
- PARTIAL: 1-2 checks = true
- DISPUTE: 0 checks = true OR conflict between feedback ratings

**Used in**: QA endpoint, settlement

---

## Schema: Settlement

```json
{
  "settlement_id": "integer",
  "barter_id": "integer (foreign key)",
  "user_id": "integer (foreign key)",
  "verdict_type": "string (from QA verdict)",
  "escrow_amount_returned": "integer (credits)",
  "bonus_awarded": "integer (credits)",
  "engagement_reward": "integer (flat 10 for all verdicts)",
  "total_released": "integer (sum of above three)",
  "transaction_id": "integer (links to Transaction table)",
  "created_at": "ISO8601 timestamp"
}
```

**Example**:
```json
{
  "settlement_id": 1,
  "barter_id": 1,
  "user_id": 1,
  "verdict_type": "SUCCESSFUL",
  "escrow_amount_returned": 28,
  "bonus_awarded": 14,
  "engagement_reward": 10,
  "total_released": 52,
  "transaction_id": 100,
  "created_at": "2026-01-21T15:52:00Z"
}
```

**Calculation rules**:
- SUCCESSFUL: escrow + (50% × escrow) + 10 = total
- PARTIAL: (50% × escrow) + (25% × escrow) + 10 = total
- DISPUTE: 0 (hold in escrow for manual review)

**Rule**: One settlement per user per barter (two settlements total)

**Used in**: Settlement endpoint

---

## Schema: Trust Score

```json
{
  "trust_id": "integer",
  "user_id": "integer (unique, foreign key)",
  "score": "float (0.0 - 1.0)",
  "successful_barters": "integer (count of SUCCESSFUL verdicts)",
  "disputed_barters": "integer (count of DISPUTE verdicts)",
  "average_rating": "float (0.0 - 5.0, average of all feedback ratings)",
  "updated_at": "ISO8601 timestamp",
  "update_reason": "string (why was this updated?)"
}
```

**Example**:
```json
{
  "trust_id": 1,
  "user_id": 1,
  "score": 0.62,
  "successful_barters": 3,
  "disputed_barters": 0,
  "average_rating": 4.7,
  "updated_at": "2026-01-21T15:53:00Z",
  "update_reason": "Barter 1 completed successfully. Rating improved from feedback scores."
}
```

**Rule**: One record per user (updated, not created new)

**Used in**: Trust endpoints, matching

---

# PART 2: API ENDPOINTS

These are all the endpoints your system exposes. Each has exact request/response format.

## Authentication Endpoints

### POST /auth/register

**Purpose**: Create new user account

**Who can call**: Anyone (no authentication required)

**Request**:
```json
{
  "email": "string (required, valid email format, lowercase)",
  "password": "string (required, min 8 chars, must have uppercase + number)",
  "name": "string (required, 1-100 chars)"
}
```

**Success Response (201 Created)**:
```json
{
  "user_id": 1,
  "email": "alice@example.com",
  "name": "Alice Chen",
  "trust_score": 0.30,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "wallet": {
    "available_balance": 50,
    "locked_balance": 0
  }
}
```

**Error Responses**:
- 400 Email already exists
  ```json
  {
    "error": "email_exists",
    "message": "An account with this email already exists"
  }
  ```
- 400 Password too weak
  ```json
  {
    "error": "password_weak",
    "message": "Password must be at least 8 characters with 1 uppercase and 1 number"
  }
  ```
- 400 Invalid email
  ```json
  {
    "error": "invalid_email",
    "message": "Email format is invalid"
  }
  ```
- 400 Invalid name
  ```json
  {
    "error": "invalid_name",
    "message": "Name must be 1-100 characters"
  }
  ```

**Assigned to**: Person 1

---

### POST /auth/login

**Purpose**: Authenticate user and get access token

**Who can call**: Anyone (no authentication required)

**Request**:
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Success Response (200 OK)**:
```json
{
  "user_id": 1,
  "email": "alice@example.com",
  "name": "Alice Chen",
  "trust_score": 0.62,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

**Error Responses**:
- 401 Invalid credentials
  ```json
  {
    "error": "invalid_credentials",
    "message": "Email or password is incorrect"
  }
  ```
- 404 Email not registered
  ```json
  {
    "error": "user_not_found",
    "message": "No account found with this email"
  }
  ```

**Assigned to**: Person 1

---

### GET /auth/me

**Purpose**: Get current authenticated user profile

**Who can call**: Authenticated users (requires JWT)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "user_id": 1,
  "email": "alice@example.com",
  "name": "Alice Chen",
  "trust_score": 0.62,
  "created_at": "2026-01-20T10:00:00Z"
}
```

**Error Responses**:
- 401 Unauthorized (missing or invalid token)
  ```json
  {
    "error": "unauthorized",
    "message": "No valid authentication token provided"
  }
  ```

**Assigned to**: Person 1

---

## Skills Endpoints

### POST /users/skills

**Purpose**: Add a new skill for current user

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "skill_name": "string (required, 3-50 chars, will be lowercased)",
  "skill_type": "enum: 'offer' | 'want' (required)",
  "proficiency_level": "enum: 'beginner' | 'intermediate' | 'advanced' | 'expert' (optional)"
}
```

**Success Response (201 Created)**:
```json
{
  "skill_id": 42,
  "user_id": 1,
  "skill_name": "python programming",
  "skill_type": "offer",
  "proficiency_level": "advanced",
  "created_at": "2026-01-20T10:15:00Z"
}
```

**Error Responses**:
- 400 Skill name too short/long
  ```json
  {
    "error": "invalid_skill_name",
    "message": "Skill name must be 3-50 characters"
  }
  ```
- 400 Invalid skill type
  ```json
  {
    "error": "invalid_skill_type",
    "message": "Skill type must be 'offer' or 'want'"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 2 (frontend integration, backend logic shared)

---

### GET /users/skills

**Purpose**: Get all skills for current user

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "user_id": 1,
  "skills_offered": [
    {
      "skill_id": 42,
      "skill_name": "python programming",
      "proficiency_level": "advanced",
      "created_at": "2026-01-20T10:15:00Z"
    }
  ],
  "skills_wanted": [
    {
      "skill_id": 43,
      "skill_name": "graphic design",
      "proficiency_level": null,
      "created_at": "2026-01-20T10:20:00Z"
    }
  ]
}
```

**Error Responses**:
- 401 Unauthorized

**Assigned to**: Person 2

---

### DELETE /users/skills/{skill_id}

**Purpose**: Remove a skill

**Who can call**: Authenticated users (must own the skill)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (204 No Content)**:
(empty body, just status code)

**Error Responses**:
- 404 Skill not found
  ```json
  {
    "error": "skill_not_found",
    "message": "Skill does not exist"
  }
  ```
- 403 Forbidden (user doesn't own this skill)
  ```json
  {
    "error": "forbidden",
    "message": "You do not own this skill"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 2

---

### GET /skills/suggestions

**Purpose**: Autocomplete skill names

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Query Parameters**:
- `q` (required): search string
- `limit` (optional, default 5): max suggestions to return

**Example Request**: `GET /skills/suggestions?q=python&limit=5`

**Response (200 OK)**:
```json
{
  "suggestions": [
    "python programming",
    "python for data science",
    "python web development",
    "python machine learning"
  ]
}
```

**Assigned to**: Person 2

---

## User Profile Endpoints

### GET /users/{user_id}

**Purpose**: Get public profile of any user

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "user_id": 2,
  "name": "Bob Singh",
  "trust_score": 0.78,
  "successful_barters": 5,
  "disputed_barters": 0,
  "average_rating": 4.8,
  "skills_offered": [
    {
      "skill_name": "python programming",
      "proficiency_level": "expert"
    }
  ],
  "skills_wanted": [
    {
      "skill_name": "graphic design"
    }
  ]
}
```

**Error Responses**:
- 404 User not found
  ```json
  {
    "error": "user_not_found",
    "message": "User does not exist"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 2

---

## Matching Endpoints

### POST /matching/request

**Purpose**: Find compatible partners for a skill

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "desired_skill": "string (required, skill to learn)"
}
```

**Success Response (200 OK)**:
```json
{
  "matches": [
    {
      "user_id": 2,
      "name": "Bob Singh",
      "trust_score": 0.78,
      "skills_offered": ["python programming"],
      "skills_wanted": ["graphic design"],
      "match_score": 0.95,
      "compatibility_reason": "Bob teaches python (your want). You teach graphic design (his want). Trust 0.78."
    },
    {
      "user_id": 3,
      "name": "Charlie Lee",
      "trust_score": 0.45,
      "skills_offered": ["python programming"],
      "skills_wanted": ["machine learning"],
      "match_score": 0.72,
      "compatibility_reason": "Charlie teaches python. You teach graphic design (not his want). Partial match."
    }
  ],
  "total_matches": 2
}
```

**Error Responses**:
- 400 Skill not found in system
  ```json
  {
    "error": "skill_not_found",
    "message": "No users offer 'weird_skill'. Try searching for a common skill."
  }
  ```
- 401 Unauthorized

**Match Score Calculation**:
- Perfect match (you teach what they want, they teach what you want): 0.95-1.0
- One-sided match (they teach what you want, you don't teach what they want): 0.70-0.85
- Skill match only (both offer/want similar skills): 0.50-0.70

**Assigned to**: Person 2

---

### POST /matching/accept

**Purpose**: Accept a match and create a barter

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "match_user_id": "integer (required)",
  "your_skill": "string (required, what you will teach)",
  "their_skill": "string (required, what they will teach)"
}
```

**Success Response (201 Created)**:
```json
{
  "barter_id": 1,
  "status": "proposed",
  "user_a_id": 1,
  "user_b_id": 2,
  "skill_a": "graphic design",
  "skill_b": "python programming",
  "proposed_at": "2026-01-20T10:30:00Z",
  "message": "Match created! You can now chat with Bob to negotiate session details."
}
```

**Error Responses**:
- 400 User already in active barter
  ```json
  {
    "error": "already_in_barter",
    "message": "You already have an active barter with another user"
  }
  ```
- 404 Match user not found
  ```json
  {
    "error": "user_not_found",
    "message": "The user you're trying to match with doesn't exist"
  }
  ```
- 400 User cannot barter with themselves
  ```json
  {
    "error": "invalid_match",
    "message": "You cannot create a barter with yourself"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 2

---

## Chat Endpoints

### POST /barters/{barter_id}/chat/message

**Purpose**: Send a message in a barter chat

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "content": "string (required, 1-5000 chars)"
}
```

**Success Response (201 Created)**:
```json
{
  "message_id": 100,
  "barter_id": 1,
  "sender_id": 1,
  "sender_name": "Alice Chen",
  "content": "Can we do next Saturday at 2pm?",
  "sent_at": "2026-01-20T10:45:00Z"
}
```

**Error Responses**:
- 400 Message empty or too long
  ```json
  {
    "error": "invalid_message",
    "message": "Message must be 1-5000 characters"
  }
  ```
- 403 User not in this barter
  ```json
  {
    "error": "forbidden",
    "message": "You are not part of this barter"
  }
  ```
- 404 Barter not found
  ```json
  {
    "error": "barter_not_found",
    "message": "Barter does not exist"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 3

---

### GET /barters/{barter_id}/chat

**Purpose**: Get chat history for a barter

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Query Parameters**:
- `page` (optional, default 1): page number
- `limit` (optional, default 50): messages per page

**Example Request**: `GET /barters/1/chat?page=1&limit=50`

**Response (200 OK)**:
```json
{
  "barter_id": 1,
  "messages": [
    {
      "message_id": 100,
      "sender_id": 1,
      "sender_name": "Alice Chen",
      "content": "Can we do next Saturday at 2pm?",
      "sent_at": "2026-01-20T10:45:00Z"
    },
    {
      "message_id": 101,
      "sender_id": 2,
      "sender_name": "Bob Singh",
      "content": "Perfect! I'm free then.",
      "sent_at": "2026-01-20T10:46:00Z"
    }
  ],
  "page": 1,
  "total_messages": 2
}
```

**Error Responses**:
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

## Session Proposal Endpoints

### POST /barters/{barter_id}/session/propose

**Purpose**: Propose a session (time, duration, details)

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "scheduled_time": "ISO8601 timestamp (required, future time only)",
  "agreed_duration_minutes": "integer (required, 30-180 minutes)",
  "notes": "string (optional, up to 500 chars)"
}
```

**Success Response (201 Created)**:
```json
{
  "barter_id": 1,
  "status": "confirmed",
  "scheduled_time": "2026-01-21T14:00:00Z",
  "agreed_duration_minutes": 90,
  "notes": "Let's do 90 minutes each way",
  "proposed_by": 1,
  "created_at": "2026-01-20T10:50:00Z",
  "message": "Session proposed! The other user must accept to lock escrow."
}
```

**Error Responses**:
- 400 Time is in the past
  ```json
  {
    "error": "invalid_time",
    "message": "Session time must be in the future"
  }
  ```
- 400 Duration out of range
  ```json
  {
    "error": "invalid_duration",
    "message": "Duration must be 30-180 minutes"
  }
  ```
- 400 Session already proposed
  ```json
  {
    "error": "session_exists",
    "message": "A session has already been proposed. Cancel it first if you want to propose a different time."
  }
  ```
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

### POST /barters/{barter_id}/session/accept

**Purpose**: Accept the proposed session and lock escrow

**Who can call**: Authenticated users (must be the other user in barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "accept": "boolean (required, true to accept)"
}
```

**Success Response (200 OK)**:
```json
{
  "barter_id": 1,
  "status": "escrow_locked",
  "scheduled_time": "2026-01-21T14:00:00Z",
  "agreed_duration_minutes": 90,
  "user_a_id": 1,
  "user_b_id": 2,
  "escrow": {
    "user_a_locked": 28,
    "user_a_balance_after": 22,
    "user_b_locked": 12,
    "user_b_balance_after": 38
  },
  "message": "Session confirmed and escrow locked! You're ready to teach."
}
```

**Error Responses**:
- 400 Not enough balance
  ```json
  {
    "error": "insufficient_balance",
    "message": "You need 28 credits but only have 15 available"
  }
  ```
- 403 Forbidden (wrong user, or already accepted)
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

## Session Execution Endpoints

### POST /barters/{barter_id}/session/start

**Purpose**: Start the teaching session

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "barter_id": 1,
  "status": "active",
  "session_id": "sess_1234567890abcdef",
  "agreed_duration_minutes": 90,
  "start_time": "2026-01-21T14:05:00Z",
  "target_end_time": "2026-01-21T15:35:00Z"
}
```

**Error Responses**:
- 400 Session not in escrow_locked state
  ```json
  {
    "error": "invalid_state",
    "message": "Session must be in 'escrow_locked' status to start"
  }
  ```
- 400 Session already started
  ```json
  {
    "error": "already_started",
    "message": "Session is already active"
  }
  ```
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

### GET /barters/{barter_id}/session/status

**Purpose**: Check current session progress

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "barter_id": 1,
  "status": "active",
  "session_id": "sess_1234567890abcdef",
  "agreed_duration_minutes": 90,
  "start_time": "2026-01-21T14:05:00Z",
  "elapsed_seconds": 1234,
  "elapsed_minutes": 20.5,
  "percent_complete": 22.8,
  "minimum_required_seconds": 4320,
  "can_complete": false,
  "message": "20.5 / 90 minutes elapsed. You need 72 minutes minimum. Can complete after 11:18pm."
}
```

**Error Responses**:
- 400 Session not active
  ```json
  {
    "error": "not_active",
    "message": "Session is not currently active"
  }
  ```
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

### POST /barters/{barter_id}/session/complete

**Purpose**: End the session (mark as completed)

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "barter_id": 1,
  "status": "completed",
  "actual_duration_minutes": 90,
  "actual_start_time": "2026-01-21T14:05:00Z",
  "actual_end_time": "2026-01-21T15:35:00Z",
  "validity": "PASS",
  "message": "Session completed! 90 minutes (100% of agreed 90). Next: both give feedback."
}
```

**Error Responses**:
- 400 Session too short
  ```json
  {
    "error": "too_short",
    "message": "Session was only 45 minutes. Minimum is 72 minutes (80% of 90). Come back when you've met the minimum."
  }
  ```
- 400 Session not active
  ```json
  {
    "error": "not_active",
    "message": "Session is not currently active"
  }
  ```
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 3

---

## Feedback Endpoints

### POST /barters/{barter_id}/feedback

**Purpose**: Submit feedback after session

**Who can call**: Authenticated users (must be in the barter, session must be completed)

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "satisfaction_rating": "integer 1-5 (required)",
  "teaching_quality_rating": "integer 1-5 (required)",
  "did_complete_scope": "enum: 'yes' | 'no' | 'partial' (required)",
  "comment": "string (optional, max 1000 chars)"
}
```

**Success Response (201 Created)**:
```json
{
  "feedback_id": 42,
  "barter_id": 1,
  "respondent_id": 1,
  "respondent_name": "Alice Chen",
  "satisfaction_rating": 5,
  "teaching_quality_rating": 4,
  "did_complete_scope": "yes",
  "comment": "Great session, learned a lot!",
  "submitted_at": "2026-01-21T15:45:00Z",
  "message": "Feedback submitted! Waiting for the other user's feedback before QA analysis."
}
```

**Error Responses**:
- 400 Invalid rating
  ```json
  {
    "error": "invalid_rating",
    "message": "Ratings must be integers between 1 and 5"
  }
  ```
- 400 Feedback already submitted
  ```json
  {
    "error": "already_submitted",
    "message": "You have already submitted feedback for this session"
  }
  ```
- 400 Session not completed
  ```json
  {
    "error": "session_not_completed",
    "message": "Session must be completed before submitting feedback"
  }
  ```
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 4

---

### GET /barters/{barter_id}/feedback

**Purpose**: Get feedback from both users

**Who can call**: Authenticated users (must be in the barter)

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "barter_id": 1,
  "feedback": [
    {
      "feedback_id": 42,
      "respondent_id": 1,
      "respondent_name": "Alice Chen",
      "satisfaction_rating": 5,
      "teaching_quality_rating": 4,
      "did_complete_scope": "yes",
      "comment": "Great session, learned a lot!",
      "submitted_at": "2026-01-21T15:45:00Z"
    },
    {
      "feedback_id": 43,
      "respondent_id": 2,
      "respondent_name": "Bob Singh",
      "satisfaction_rating": 5,
      "teaching_quality_rating": 5,
      "did_complete_scope": "yes",
      "comment": "Excellent learner!",
      "submitted_at": "2026-01-21T15:50:00Z"
    }
  ],
  "all_feedback_submitted": true
}
```

**Note**: Can be called even if feedback is incomplete (returns what's available)

**Error Responses**:
- 403 Forbidden
- 404 Barter not found
- 401 Unauthorized

**Assigned to**: Person 4

---

## QA & Settlement Endpoints

### POST /qa/{barter_id}/analyze

**Purpose**: Run automated QA verification (INTERNAL ONLY)

**Who can call**: Backend system only (not exposed to frontend)

**Note**: This is called automatically by backend, not by users

**Response (200 OK)**:
```json
{
  "verdict_id": 1,
  "barter_id": 1,
  "verdict_type": "SUCCESSFUL",
  "confidence_score": 0.98,
  "checks": {
    "duration_check": true,
    "feedback_check": true,
    "presence_check": true
  },
  "explanation": "All checks passed. Both users gave positive feedback (5/5 and 5/5). Session duration 90 minutes (100% of agreed 90 minutes).",
  "created_at": "2026-01-21T15:52:00Z"
}
```

**Assigned to**: Person 4

---

### POST /settlement/{barter_id}/execute

**Purpose**: Execute settlement and release credits (INTERNAL ONLY)

**Who can call**: Backend system only (not exposed to frontend)

**Note**: This is called automatically after QA verdict

**Response (200 OK)**:
```json
{
  "settlement_id": 1,
  "barter_id": 1,
  "status": "settled",
  "user_a_settlement": {
    "user_id": 1,
    "user_name": "Alice Chen",
    "escrow_returned": 28,
    "bonus_awarded": 14,
    "engagement_reward": 10,
    "total_released": 52,
    "balance_after": 74
  },
  "user_b_settlement": {
    "user_id": 2,
    "user_name": "Bob Singh",
    "escrow_returned": 12,
    "bonus_awarded": 9,
    "engagement_reward": 10,
    "total_released": 31,
    "balance_after": 69
  },
  "created_at": "2026-01-21T15:53:00Z"
}
```

**Assigned to**: Person 4

---

## Wallet Endpoints

### GET /wallet

**Purpose**: Get current user's wallet info

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "wallet_id": 1,
  "user_id": 1,
  "available_balance": 74,
  "locked_balance": 0,
  "total_earned": 100,
  "total_spent": 26,
  "transactions_count": 5,
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-21T15:53:00Z"
}
```

**Error Responses**:
- 401 Unauthorized

**Assigned to**: Person 2 (integration with escrow)

---

## Escrow Lock Endpoint

### POST /escrow/lock

**Purpose**: Lock escrow credits when session confirmed

**Who can call**: Authenticated users (session proposer accepts)

**Auth Header**: `Authorization: Bearer <access_token>`

**Request**:
```json
{
  "barter_id": "integer (required)"
}
```

**Success Response (200 OK)**:
```json
{
  "barter_id": 1,
  "user_a_id": 1,
  "user_b_id": 2,
  "user_a_trust_score": 0.30,
  "user_b_trust_score": 0.70,
  "user_a_escrow_amount": 28,
  "user_b_escrow_amount": 12,
  "user_a_balance_before": 50,
  "user_a_balance_after": 22,
  "user_b_balance_before": 50,
  "user_b_balance_after": 38,
  "status": "escrow_locked",
  "locked_at": "2026-01-21T14:00:00Z"
}
```

**Error Responses**:
- 400 Insufficient balance
  ```json
  {
    "error": "insufficient_balance",
    "message": "User A needs 28 credits but has 15 available. User B is OK."
  }
  ```
- 400 Barter not in confirmed state
  ```json
  {
    "error": "invalid_state",
    "message": "Barter must be in 'confirmed' status to lock escrow"
  }
  ```
- 400 Escrow already locked
  ```json
  {
    "error": "already_locked",
    "message": "Escrow is already locked for this barter"
  }
  ```
- 401 Unauthorized

**Assigned to**: Person 2

---

## Trust Endpoints

### GET /users/{user_id}/trust

**Purpose**: Get trust information for a user

**Who can call**: Authenticated users

**Auth Header**: `Authorization: Bearer <access_token>`

**Response (200 OK)**:
```json
{
  "user_id": 1,
  "user_name": "Alice Chen",
  "trust_score": 0.62,
  "trust_level": "good",
  "successful_barters": 3,
  "disputed_barters": 0,
  "average_rating": 4.7,
  "total_barters": 3,
  "success_rate": 100.0,
  "history": [
    {
      "update_id": 1,
      "old_score": 0.30,
      "new_score": 0.45,
      "change_reason": "Barter 1 completed successfully",
      "updated_at": "2026-01-21T15:53:00Z"
    }
  ]
}
```

**Error Responses**:
- 404 User not found
- 401 Unauthorized

**Assigned to**: Person 4

---

# PART 3: ERROR HANDLING STANDARDS

All error responses follow this format:

```json
{
  "error": "error_code (snake_case, machine-readable)",
  "message": "Human-readable explanation",
  "details": "Optional: extra context or suggestions"
}
```

**HTTP Status Codes**:
- 200 OK: Success
- 201 Created: Resource created successfully
- 204 No Content: Success with no response body
- 400 Bad Request: Client error (invalid input, validation failed)
- 401 Unauthorized: Authentication required or failed
- 403 Forbidden: Authenticated but not allowed
- 404 Not Found: Resource doesn't exist
- 500 Internal Server Error: Server-side problem
- 503 Service Unavailable: Temporary server issue

---

# PART 4: AUTHENTICATION

All endpoints except `/auth/register` and `/auth/login` require:

**Header**: `Authorization: Bearer <access_token>`

**Token Format**: JWT (JSON Web Token)

**Token Expiration**: 24 hours (86400 seconds)

**Example Header**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFsaWNlQGV4YW1wbGUuY29tIiwiaWF0IjoxNjc0Njc2MDAwLCJleHAiOjE2NzQ3NjI0MDB9.signature
```