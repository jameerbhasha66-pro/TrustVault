# TrustVault 🔐

**Secure Document Sharing with Access Control and Audit Logging**

TrustVault is a web application built with FastAPI that allows registered users to upload documents, manage document access, and share files securely with other registered users. It uses server-side authorization checks and records important document activities in an audit log.

## Live Demo

- **Live Application:** https://trustvault-demo-rabs.onrender.com
- **GitHub Repository:** https://github.com/jameerbhasha66-pro/TrustVault
- **API Documentation:** https://trustvault-demo-rabs.onrender.com/docs

## Features

### Authentication
- User registration and login.
- Password hashing using `pwdlib` with its recommended password-hashing configuration.
- Session-based authentication.

### Document Management
- Upload and list documents.
- Download documents when authorized.
- Organize documents by category.
- Maximum upload size: 5 MB.
- Supported file types: PDF, TXT, PNG, JPG, and JPEG.

### Access Control
- Document owners can share documents with other registered users.
- Sharing permissions support read and edit flags.
- Only document owners can manage sharing permissions.
- Owners can revoke previously granted access.
- Authorization is enforced by the backend, not just the frontend.

### Audit Logging
The application records important actions, including document uploads, downloads, sharing, and access revocation, in its audit-log database table.

### Web Interface
A browser-based interface provides registration, login, a document wallet, uploading, downloading, sharing, and access revocation.

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI
- **Database and ORM:** SQLite, SQLAlchemy
- **Authentication:** SessionMiddleware
- **Password Security:** `pwdlib`
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** pytest, HTTPX
- **Deployment:** Render

## Project Structure

```text
TrustVault/
├── static/
│   └── index.html
├── tests/
├── main.py
├── documents.py
├── authorization.py
├── security.py
├── models.py
├── database.py
├── check_audit.py
├── check_db.py
├── requirements.txt
├── PROMPTS.md
└── README.md
```

## Run Locally

### Prerequisites

- Python 3.11 or a compatible Python version.
- Git.

### 1. Clone the repository

```bash
git clone https://github.com/jameerbhasha66-pro/TrustVault.git
cd TrustVault
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the session secret

**Windows PowerShell:**

```powershell
$env:TRUSTVAULT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**macOS/Linux:**

```bash
export TRUSTVAULT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Generate a fresh secret for your own environment. Never commit secret keys or passwords to GitHub.

### 5. Start the application

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

Interactive API documentation is available at http://127.0.0.1:8000/docs.

##  Run Tests

Run the test suite from the project root:

```bash
pytest
```

##  Security and Limitations

- Protected document operations use server-side authentication and authorization.
- Passwords are stored as hashes rather than plaintext.
- File uploads are restricted by extension, content type, and size.
- Access permissions are stored in the database and can be revoked by the owner.
- Audit events are stored in the database for accountability.

**Deployment note:** The current configuration uses a local SQLite database and local file storage. On hosting platforms with ephemeral filesystems, stored data may not survive restarts or redeployments. Persistent storage should be configured before using the application for important documents.

TrustVault is a project demonstration and should not be considered production-ready for confidential documents without further security review and persistent storage configuration.

##  Project Goal

TrustVault demonstrates document sharing with authentication, server-side access control, permission management, and audit logging in a deployable web application.
