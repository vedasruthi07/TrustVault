# TrustVault — Secure Document Sharing with Audit Trails

TrustVault is a secure document-sharing web application built with Python Flask. It allows users to upload, share, view, download and manage PDF documents through controlled permissions, while maintaining a tamper-evident audit trail of important activities.

## Key Features

- **User Authentication:** Secure registration, login and logout with password hashing.
- **Role-Based Access:** Different roles control access to application functions.
- **Secure PDF Upload:** Validates uploaded PDF files and stores them in private storage.
- **Document Sharing:** Owners can grant READ or EDIT permissions to other users.
- **Access Revocation:** Owners can revoke previously granted permissions.
- **Server-Side Authorization:** Checks permissions on every protected document request.
- **Document Management:** Search, view, download, edit and delete documents according to permissions.
- **Audit Logging:** Records successful and denied security-related actions.
- **Tamper-Evident Audit Trail:** Uses an HMAC-based hash chain to help detect audit-record modification.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Werkzeug password hashing |
| Security | Flask-WTF CSRF, Flask-Limiter |
| PDF Processing | PyMuPDF |
| Testing | Pytest |
| Version Control | Git and GitHub |

## Permission Model

| Role / Permission | Access |
|---|---|
| OWNER | Manages their own documents and sharing permissions |
| READ | Views and downloads shared documents |
| EDIT | Views, downloads and edits shared documents |
| ADMIN | Manages administrative audit-log access without automatic access to document contents |

Document permissions are enforced by the backend. Hiding a frontend button is not treated as an authorization control.

## Project Structure

```text
TrustVault/
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── permissions.py
│   │   ├── admin.py
│   │   └── pages.py
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── security.py
│   ├── audit.py
│   └── permission_management.py
├── migrations/
├── tests/
├── config.py
├── run.py
├── requirements.txt
└── .gitignore
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vedasruthi07/TrustVault.git
cd TrustVault
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Set a new secret key for your local environment. Never commit secret keys to GitHub.

PowerShell example:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:APP_ENV = "development"
```

### 5. Initialize the Database

```powershell
python -m flask --app run db upgrade
```

### 6. Start the Application

```powershell
python run.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## Running Tests

Run the test suite from the project root:

```powershell
python -m pytest -v
```

The current development test suite has passed **90 tests**.

## Security Design

- Passwords are stored as hashes rather than plaintext.
- CSRF protection is enabled for protected requests.
- Login attempts and application requests are rate-limited.
- Uploaded documents are stored outside the public static directory.
- Document access is checked on the server for each request.
- Unauthorized requests are denied and relevant security events are audited.
- Audit entries are linked using an HMAC-based hash chain.

**Important:** Revoking access prevents future authorized requests. It cannot delete copies that a recipient has already downloaded.

## Current Project Status

The authentication, document management, permission handling, audit logging and current automated test suite have been implemented.

Deployment, final documentation and the project demonstration are pending completion.

## Repository

GitHub: https://github.com/vedasruthi07/TrustVault