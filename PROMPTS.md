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
- **Commit:** `56754b6` — Add document upload and audit logging.
## Entry 5 — 2026-10-23 — Secure document downloads

- **Goal:** Add a download endpoint that enforces document-level access control and records successful download attempts.
- **AI assistance requested:** Help implement a FastAPI download route that checks document ownership or read permission, returns appropriate HTTP errors, and records an audit event.
- **Output used:** Added `GET /documents/{document_id}/download` in `documents.py`, using `can_read_document`, querying document permissions, validating the stored file path, recording a download audit event, and returning the file with `FileResponse`.
- **Verification:** Unauthenticated download returned HTTP 401; the document owner downloaded document 2 successfully with HTTP 200; the ungranted user `viewer_test3` received HTTP 403. Python compilation succeeded, and all six existing authorization tests passed.
- **Issues and corrections:** A temporary typo in the `pathlib` import prevented application startup and was corrected. The download route was then tested successfully.
- **My decision:** Deny downloads unless the user is the document owner or has read permission. Keep the download audit event in the database before returning the file.
- **Commit reference:** Pending.

