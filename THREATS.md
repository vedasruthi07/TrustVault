# Threat Model & Security Architecture - TrustVault

## 1. Broken Access Control & IDOR Protection
* **Threat:** Malicious users changing document IDs in URLs (e.g., /api/documents/2/view) to access unauthorized files.
* **Mitigation:** Server-side authorization checks verify document ownership (owner_id) or explicit DocumentPermission records on every single request. Unauthorized access returns an immediate 403 Forbidden.

## 2. Stale Permission Vulnerability (Instant Revocation)
* **Threat:** A user retaining access to previously bookmarked or cached document links after their permission has been revoked by the owner.
* **Mitigation:** The /api/documents/<id>/view endpoint queries the live database on every request. When permission is deleted, access is blocked instantly without relying on stale sessions or token caches.

## 3. Audit Log Tampering
* **Threat:** An attacker or compromised admin modifying database rows to conceal unauthorized access attempts.
* **Mitigation:** Audit records utilize SHA-256 HMAC hash chaining (previous_hash + entry_hash). Modifying any row breaks the cryptographic chain, causing verify_audit_chain() to return False.

## 4. Direct Static Path Traversal
* **Threat:** Accessing uploaded PDF files directly via static Web server paths (e.g., /static/uploads/file.pdf).
* **Mitigation:** File uploads are stored outside the public static directory. Files are served exclusively through authenticated Flask streaming endpoints after permission validation.
