# AI Usage & Prompt Log - TrustVault

## Overview
This document records how Artificial Intelligence (AI) was utilized as an architectural mentor and technical partner during the development of TrustVault for the Snovasys Fresher Hiring Challenge 2026.

## Key Areas of AI Engagement

### 1. Windows SQLite Path Standardization
* **Problem:** sqlite3.OperationalError occurred consistently on Windows operating systems due to backslash path escaping in SQLite connection strings.
* **AI Solution:** Diagnosed URI string formatting issues and recommended standardizing database file paths to .as_posix() inside config.py.
* **Outcome:** Stabilized database initialization and table creation across all environment executions.

### 2. Cryptographic Audit Chain Architecture
* **Problem:** Implementing tamper-evident logging to ensure audit logs cannot be altered unnoticed.
* **AI Solution:** Designed an HMAC SHA-256 hash chaining mechanism where each log entry hashes its payload alongside the previous_hash of the preceding record.
* **Outcome:** Successfully implemented verify_audit_chain(), returning True during automated integrity checks.

### 3. Comprehensive Automated Testing
* **Problem:** Fulfilling the threat modeling and testing requirements.
* **AI Solution:** Structured a 90-case pytest suite covering RBAC, path traversal, IDOR prevention, and immediate access revocation.

## Verification & Integrity
All AI-suggested code, security models, and path fixes were independently reviewed, executed, and verified via PowerShell terminal commands and live browser testing.
