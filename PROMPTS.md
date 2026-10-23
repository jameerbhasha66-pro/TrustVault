# TrustVault — AI Usage and Development Log

This document records AI assistance used during the development of TrustVault. Entries reflect actual work completed and will be updated as development progresses.

## Entry 1 — 2026-10-23: Initial project setup

- **Goal:** Set up a minimal FastAPI application and prepare the project for version control.
- **AI assistance requested:** Guidance on creating a beginner-friendly FastAPI starter application and configuring the initial project files.
- **Output used:** A minimal FastAPI application with a home endpoint and a health-check endpoint, plus `requirements.txt` and `.gitignore`.
- **Verification:** Started the application locally and checked that the API was running.
- **Issues and corrections:** No specific AI-generated error was identified during this step.
- **My decision:** Keep the starter application minimal before adding authentication, document storage, authorization, and audit logging.
- **Commit reference:** `b2ff99c` — Set up initial TrustVault application.

## Entry 2 — 2026-10-23: Authentication foundation

- **Goal:** Implement basic user registration, password verification, and session-based login.
- **AI assistance requested:** Help design and implement authentication using FastAPI, SQLAlchemy, Argon2 password hashing, and signed session cookies.
- **Output used:** Registration, login, logout, and current-user endpoints in `main.py`, plus password helpers in `security.py`.
- **Verification:** Registration returned HTTP 201; login and the current-user endpoint returned HTTP 200.
- **Issues and corrections:** No authentication failure was observed in these initial tests. Further security testing is still required.
- **My decision:** Public registration assigns the viewer role. Document-level authorization, CSRF protection, and additional security tests remain future tasks.
- **Commit reference:** `fff2f63` — Add authentication foundation.

## Entry 3 — 2026-10-23 — Authorization rules and tests

- **What I asked AI:** Help implement document authorization rules and unit tests for ownership, read/edit permissions, inactive users, and administrator access.
- **AI output:** Created `authorization.py` and `tests/test_authorization.py`.
- **What went wrong:** The initial test run could not import `authorization` because the module had not yet been created in the project root.
- **What I did instead:** Created the module in the project root and ran the tests again. All six authorization unit tests passed.
- **Commit:** `0fcada5` — Add document authorization rules and tests.

## Entry 4 — 2026-10-23 — Document endpoints and upload audit

- **What I asked AI:** Help add authenticated document listing, file uploads, and audit logging for successful uploads.
- **AI output:** Added `documents.py` with document listing and upload routes, and connected the router to `main.py`.
- **What went wrong:** The application initially failed to start because the router was defined after the upload route decorator.
- **What I did instead:** Moved the router definition above the route decorators, restarted the application, uploaded a test document, and checked the audit database using `check_audit.py`.
- **Verification:** Unauthenticated upload returned 401; an authenticated upload returned 201; document listing returned 200; the audit query showed an upload event for document ID 2; all six existing unit tests passed.
- **Commit:** Pending.

