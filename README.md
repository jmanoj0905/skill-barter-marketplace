# skill-barter-marketplace

## Backend environment setup

The backend reads configuration from `backend/.env`. This file is intentionally
ignored by Git because it contains credentials.

To configure a local backend:

1. Copy `backend/.env.example` to `backend/.env`.
2. Replace the placeholder values with the database, Supabase, email, and
   Twilio credentials for your environment.
3. Start the backend from the repository root using the project's normal
   startup command.
