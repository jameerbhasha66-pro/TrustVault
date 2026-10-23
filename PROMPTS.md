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
- **Commit reference:** To be added after committing this milestone.