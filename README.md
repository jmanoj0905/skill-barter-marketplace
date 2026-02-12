# skill-barter-marketplace
Phase 4 – Matching & Partner Discovery (Minimal Implementation)
📌 Project Overview

The Skill Barter Marketplace is a platform where users exchange skills instead of money.
The system is designed as a multi-phase, AI-assisted architecture, gradually evolving from basic skill matching to real-time monitored learning sessions with trust and escrow mechanisms.

This repository currently implements Phase 4 of the minimal implementation, focusing on:

Finding compatible skill-exchange partners and initiating a barter interaction.

🎯 Phase 4 – Scope (What is Implemented)

Phase 4 enables two users to discover each other and start a barter based on skill compatibility and trust.

✅ Implemented Capabilities
1. Skill-Based Matching

Users search for partners using a desired skill

Semantic similarity is computed using vector embeddings

Matching considers:

Skill similarity

Mutual interest (both users offer what the other wants)

Trust score

2. Match Ranking

Each candidate is assigned a composite match score

Matches are ranked and the top results are returned

3. Match Decision Flow

Users can:

Accept a match → creates a barter

Reject a match → no persistence (ephemeral decision)

4. Barter Creation

Accepting a match:

Creates a barter record

Sets status to proposed

Establishes a logical communication boundary

5. Chat Enablement (Minimal)

Each barter implicitly acts as a chat room

Users can exchange messages using the barter ID

REST-based chat (WebSockets deferred to later phases)

🔍 Semantic Skill Embeddings & Matching Logic
Skill Embedding Generation

To support flexible and meaningful skill matching (e.g., “Python programming” vs “Python development”), the system uses semantic vector embeddings.

Process:

Each skill name is passed through a pre-trained sentence embedding model
(e.g., Sentence-Transformers).

The model converts the skill text into a fixed-length numerical vector.

These vectors are stored in PostgreSQL using the pgvector extension.

An index (ivfflat) is used for efficient similarity search.

Why embeddings?

Avoids strict keyword matching

Supports synonyms and variations

Improves recall for real-world skill inputs

Match Computation Logic

When a user searches for a desired skill, the system performs the following steps:

Step 1: Candidate Discovery

Fetch users who offer a skill semantically similar to the desired skill.

Exclude the requesting user.

Apply a minimum trust threshold.

Step 2: Mutual Interest Check

A candidate is considered valid only if:

Candidate offers a skill the requester wants

Candidate wants a skill the requester offers

This ensures true barter compatibility.

Match Scoring Formula (Phase-4)

Each valid candidate is assigned a composite match score:

Match Score = 0.5 × Skill Similarity + 0.3 × Candidate Trust Score + 0.2 ×Requester Trust Score
Match Score=0.5 × Skill Similarity + 0.3 × Candidate Trust Score + 0.2 × Requester Trust Score

Where:

Skill Similarity ∈ [0,1]
(cosine similarity between embedding vectors)

Trust Scores ∈ [0,1]

The weights are chosen to:

Prioritize skill relevance

Still account for platform trust and reliability

Candidates are ranked by this score, and the top results are returned.

Design Rationale

Simple weighted scoring keeps Phase-4 explainable

Trust is included but not yet adaptive

More advanced factors (availability, skill-specific trust) are deferred