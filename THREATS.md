\# TrustVault — Threat Model and Security Analysis



\## 1. Introduction



TrustVault is a secure document-sharing application designed to protect confidential PDF documents through user authentication, permission-based access control and tamper-evident audit logging.



This threat model identifies potential security risks, their impact and the measures implemented to reduce them.



\## 2. Assets to Protect



The main assets that require protection are:



\- User accounts and password credentials.

\- Uploaded PDF documents.

\- Document ownership and sharing permissions.

\- Authentication sessions.

\- Audit logs and security activity records.

\- Application configuration and secret keys.



\## 3. Threat Identification and Mitigation



\### 3.1 Unauthorized Document Access



\*\*Threat:\*\* An unauthorized user may attempt to access confidential documents using a direct URL or API request.



\*\*Impact:\*\* Confidential information may be exposed.



\*\*Mitigation:\*\*

\- Authentication is required for protected document operations.

\- Server-side authorization checks verify document permissions.

\- Uploaded files are stored outside the public static directory.

\- Unauthorized requests are rejected.



\*\*Implementation Status:\*\* Implemented and tested.



\### 3.2 Privilege Escalation



\*\*Threat:\*\* A normal user may attempt to gain additional privileges or access another user's documents.



\*\*Impact:\*\* Users may obtain permissions they were not granted.



\*\*Mitigation:\*\*

\- Public registration assigns the OWNER role.

\- Administrative routes require the ADMIN role.

\- Only document owners can grant or revoke document permissions.

\- Permission levels are validated by the backend.



\*\*Implementation Status:\*\* Implemented and tested for the tested authorization scenarios.



\### 3.3 Unauthorized Document Modification



\*\*Threat:\*\* A READ-only user may attempt to edit or delete a document through direct API requests.



\*\*Impact:\*\* Document integrity may be compromised.



\*\*Mitigation:\*\*

\- Document modification endpoints enforce server-side permission checks.

\- READ permission does not allow editing or deletion.

\- EDIT permission is required for permitted modifications.



\*\*Implementation Status:\*\* Implemented and tested.



\### 3.4 Access After Permission Revocation



\*\*Threat:\*\* A user may attempt to access a shared document after the owner revokes their permission.



\*\*Impact:\*\* Confidential documents may remain accessible to former recipients.



\*\*Mitigation:\*\*

\- Permissions are checked on every protected document request.

\- Revoked permissions are removed from the database.

\- Previously issued document URLs do not bypass authorization checks.



\*\*Implementation Status:\*\* Implemented and tested.



\*\*Limitation:\*\* Revocation cannot remove copies that a recipient downloaded before access was revoked.



\### 3.5 Malicious File Upload



\*\*Threat:\*\* An attacker may upload invalid or unexpected files disguised as PDF documents.



\*\*Impact:\*\* Malicious or malformed files may create application or processing risks.



\*\*Mitigation:\*\*

\- Upload size is limited.

\- PDF extension and document structure are validated.

\- Stored filenames use generated identifiers.

\- Uploaded files are stored in private storage.



\*\*Implementation Status:\*\* Implemented.



\*\*Remaining Risk:\*\* Dedicated malware scanning is not currently implemented. PDF validation alone cannot guarantee that every uploaded file is harmless.



\### 3.6 Cross-Site Request Forgery (CSRF)



\*\*Threat:\*\* An attacker may attempt to make an authenticated user perform an unwanted action.



\*\*Impact:\*\* Unauthorized actions may be performed using the victim's authenticated session.



\*\*Mitigation:\*\*

\- Flask-WTF CSRF protection is enabled.

\- Protected frontend requests include CSRF tokens.

\- Session cookies use HTTP-only and SameSite settings.



\*\*Implementation Status:\*\* Implemented.



\### 3.7 Brute-Force Login Attempts



\*\*Threat:\*\* An attacker may repeatedly attempt to guess account passwords.



\*\*Impact:\*\* An attacker may gain unauthorized account access.



\*\*Mitigation:\*\*

\- Passwords are stored using password hashing.

\- Login attempts are rate-limited.

\- Passwords must meet the application's minimum length requirement.



\*\*Implementation Status:\*\* Implemented.



\### 3.8 Audit Log Tampering



\*\*Threat:\*\* An attacker may attempt to modify or delete audit records to hide unauthorized activities.



\*\*Impact:\*\* Security investigations and accountability may be compromised.



\*\*Mitigation:\*\*

\- Audit records are linked using an HMAC-based hash chain.

\- Each record contains hash information connected to the previous record.

\- Audit-chain verification can identify inconsistencies in the chain.



\*\*Implementation Status:\*\* Implemented and hash-chain verification tested.



\*\*Remaining Risk:\*\* The hash chain depends on the security of the secret key and database. An attacker who compromises both may undermine its integrity. Independent audit backups and external checkpoints are recommended.



\### 3.9 Administrative Misuse



\*\*Threat:\*\* An administrator may attempt to access confidential document contents without explicit document permission.



\*\*Impact:\*\* Confidential user documents may be exposed.



\*\*Mitigation:\*\*

\- Administrative audit-log access is restricted to ADMIN users.

\- The audit-log endpoint exposes audit metadata rather than document contents.

\- Administrative privileges do not automatically grant document ownership or sharing permissions.



\*\*Implementation Status:\*\* Implemented and tested for the tested access scenarios.



\### 3.10 Application Secret Exposure



\*\*Threat:\*\* Application secret keys may be exposed through source code, configuration files or accidental repository commits.



\*\*Impact:\*\* Session security and other protections relying on the secret key may be compromised.



\*\*Mitigation:\*\*

\- Secret keys are loaded through environment variables.

\- The application refuses to start when the secret key is missing.

\- `.env` is excluded from version control.

\- A newly generated secret key is required for production deployment.



\*\*Implementation Status:\*\* Configuration implemented; production secret rotation remains required.



\## 4. Security Testing



The following security scenarios have been tested:



\- Unauthorized attempts to access protected documents.

\- READ-only users attempting to edit or delete documents.

\- Non-owners attempting to grant document permissions.

\- Revoked users attempting to access previously shared documents.

\- Unauthorized users attempting to view permission lists.

\- Administrative access to audit records without automatic document-content access.

\- Audit hash-chain verification.



The current automated test suite has passed \*\*90 tests\*\*.



\## 5. Known Limitations and Future Improvements



The following are planned improvements and are not claimed as completed features:



\- Implement dedicated malware scanning for uploaded documents.

\- Introduce multi-factor authentication.

\- Store audit backups or signed checkpoints independently.

\- Add stronger monitoring and alerting for suspicious activities.

\- Consider a more scalable database and file-storage solution for production.

\- Perform an independent security assessment before handling real confidential documents.



\## 6. Conclusion



TrustVault uses authentication, server-side authorization, permission-based document sharing and tamper-evident audit logging to reduce the risks of unauthorized document access and modification.



The security design aims to ensure that document access is controlled and important security activities remain traceable and verifiable.

