# TrustVault - Secure Document Sharing & Audit System

TrustVault is a secure Python/Flask web application designed for role-based document storage, granular permission delegation, real-time access revocation, and tamper-evident audit logging.

## Tech Stack
* **Backend:** Python 3.14.10, Flask
* **Database & ORM:** SQLite, Flask-SQLAlchemy
* **Security & Crypto:** hashlib (HMAC SHA-256)
* **Frontend:** Jinja2, Bootstrap 5.3.2

## Installation & Setup

1. **Clone Repository:**
   git clone https://github.com/vedasruthi07/TrustVault.git
   cd TrustVault

2. **Set Up Virtual Environment:**
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt

3. **Environment Configuration (.env):**
   SECRET_KEY=tv_sec_2026_94f8a3b2c1e7d065a4891e3f
   APP_ENV=development

4. **Run Server:**
   python run.py

5. **Run Automated Test Suite:**
   pytest
