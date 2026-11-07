\# TrustVault — AI Prompt and Development Log



\## Introduction



This document records the use of AI assistance during the development of TrustVault from November 3 to November 7, 2026.



AI was used to understand technical concepts, plan implementation, debug errors, improve security and review test scenarios. The developer reviewed the suggestions, implemented changes, tested functionality and made the final decisions.



The prompts below are summaries of the actual development discussions, not verbatim transcripts.



\---



\## Entry 1 — Project Setup and Application Structure



\*\*Date:\*\* November 3, 2026



\*\*Prompt Summary:\*\*



How should I set up a Flask-based secure document-sharing application with a proper project structure and required dependencies?



\*\*AI Assistance:\*\*

\- Suggested a modular Flask application structure.

\- Explained the purpose of routes, templates, static files and configuration.

\- Guided the creation of a Python virtual environment.

\- Helped install and manage project dependencies.



\*\*Issues and Corrections:\*\*

\- The project needed a clear separation between application routes, templates, static files and tests.

\- Environment configuration needed to be handled separately from application code.



\*\*Developer Action:\*\*

\- Created the TrustVault project structure.

\- Created application folders and Python package files.

\- Configured the virtual environment.

\- Installed dependencies and generated the requirements file.



\*\*Outcome:\*\* Initial application structure and development environment established.



\---



\## Entry 2 — Database, Migrations and Security Foundation



\*\*Date:\*\* November 4, 2026



\*\*Prompt Summary:\*\*



How can I design the database models, migrations, permissions and audit logging for TrustVault?



\*\*AI Assistance:\*\*

\- Explained Flask-SQLAlchemy models and database relationships.

\- Suggested database structures for users, documents, document permissions and audit logs.

\- Explained database migrations.

\- Suggested separating permission management and audit functionality into modules.

\- Recommended security-focused automated tests.



\*\*Issues and Corrections:\*\*

\- Database migration initialization did not initially detect schema changes.

\- The database structure and migration state needed further verification.

\- Security checks needed to be enforced in backend routes rather than relying only on the frontend.



\*\*Developer Action:\*\*

\- Worked on database models and migration setup.

\- Implemented audit, access-control and permission-management modules.

\- Added document, permission and administrative routes.

\- Added soft-delete support and security-related tests.



\*\*Outcome:\*\* Core database and security foundation implemented.



\---



\## Entry 3 — Document Management and Search



\*\*Date:\*\* November 5, 2026



\*\*Prompt Summary:\*\*



How can I implement secure PDF upload, document management and search functionality in TrustVault?



\*\*AI Assistance:\*\*

\- Explained PDF upload validation and private file storage.

\- Suggested document listing and management operations.

\- Helped with search functionality for document titles and categories.

\- Explained how protected document operations should be handled.



\*\*Issues and Corrections:\*\*

\- Uploaded documents should not be exposed through the public static directory.

\- Document operations must respect ownership and permissions.

\- Search functionality needed to work with the available document information.



\*\*Developer Action:\*\*

\- Implemented and tested PDF upload.

\- Verified document listing.

\- Tested document viewing, downloading, editing and deletion.

\- Verified title search and category search.



\*\*Outcome:\*\* Core document-management and search functionality working in local testing.



\---



\## Entry 4 — Authentication, Dashboard and Access Control



\*\*Date:\*\* November 6, 2026



\*\*Prompt Summary:\*\*



How can I implement user authentication, role-based access and a dashboard that supports secure document sharing?



\*\*AI Assistance:\*\*

\- Suggested authentication using password hashing.

\- Explained role-based access control.

\- Recommended backend authorization checks for protected routes.

\- Suggested a dashboard for document management and sharing.

\- Explained READ and EDIT permission handling.



\*\*Issues and Corrections:\*\*

\- Frontend button visibility alone cannot enforce authorization.

\- Direct API requests must also be checked by the backend.

\- Different user roles must not automatically receive access to confidential documents.



\*\*Developer Action:\*\*

\- Implemented registration, login and logout functionality.

\- Worked on the dashboard interface.

\- Implemented document-sharing functionality.

\- Tested document access according to permission levels.



\*\*Outcome:\*\* Authentication, dashboard and permission-based access functionality implemented and tested.



\---



\## Entry 5 — Permission Revocation and Unauthorized Access Testing



\*\*Date:\*\* November 7, 2026



\*\*Prompt Summary:\*\*



How can TrustVault prevent users from accessing documents after their permissions are revoked, including through previously known document URLs?



\*\*AI Assistance:\*\*

\- Explained why authorization must be checked on every protected request.

\- Recommended testing direct view and download endpoints.

\- Suggested testing READ-only and EDIT permissions separately.

\- Explained how to record denied access attempts.



\*\*Issues and Corrections:\*\*

\- Removing a shared document from the frontend does not prevent direct URL access.

\- Revoked users must not retain access through previously issued URLs.

\- Unauthorized permission-management requests must be rejected by the backend.



\*\*Developer Action:\*\*

\- Tested READ and EDIT permissions.

\- Tested permission revocation.

\- Verified that revoked users could no longer view or download the shared document.

\- Tested unauthorized permission-grant attempts.

\- Verified that denied attempts were recorded in the audit log.



\*\*Outcome:\*\* Permission enforcement and revocation behaviour verified through application testing.



\---



\## Entry 6 — Audit Logging and Tamper Detection



\*\*Date:\*\* November 7, 2026



\*\*Prompt Summary:\*\*



How can I maintain a tamper-evident audit trail that records successful and denied security-related actions?



\*\*AI Assistance:\*\*

\- Explained audit logging and hash chaining.

\- Suggested an HMAC-based hash chain for linking audit records.

\- Explained audit-chain verification.

\- Highlighted the importance of protecting the secret key.



\*\*Issues and Corrections:\*\*

\- Both successful and denied security operations need to be recorded.

\- A hash chain cannot guarantee integrity if an attacker compromises both the database and the secret key.

\- Audit metadata should not expose confidential document contents.



\*\*Developer Action:\*\*

\- Implemented audit logging.

\- Tested successful and denied permission operations.

\- Verified administrative access to audit metadata.

\- Tested direct document access using the admin account.

\- Ran audit-chain verification and confirmed it returned True.



\*\*Outcome:\*\* Audit logging and hash-chain verification tested.



\---



\## Entry 7 — Automated Testing and Final Verification



\*\*Date:\*\* November 7, 2026



\*\*Prompt Summary:\*\*



How can I verify the completed TrustVault functionality and identify issues before documentation and deployment?



\*\*AI Assistance:\*\*

\- Suggested running the automated test suite.

\- Helped investigate a document date-search test failure.

\- Explained how to inspect database timestamps and date filtering.

\- Recommended verifying the final Git changes before pushing.



\*\*Issues and Corrections:\*\*

\- A date-search test initially failed and required further investigation.

\- The individual date-search test subsequently passed.

\- The complete test suite was rerun to verify the current implementation.



\*\*Developer Action:\*\*

\- Investigated the date-search behaviour.

\- Reran the individual test successfully.

\- Ran the complete test suite.

\- Verified that all 90 tests passed.

\- Reviewed and pushed the completed source changes to GitHub.



\*\*Outcome:\*\* Current automated test suite passed 90 tests, and the latest code changes were pushed to GitHub.



\---



\## Developer Responsibility and AI Usage



AI assistance was used for:



\- Understanding Flask application architecture.

\- Learning database design and migrations.

\- Implementing authentication and authorization.

\- Developing document-management functionality.

\- Understanding security risks and mitigations.

\- Debugging errors and improving code.

\- Preparing automated tests and technical documentation.



The developer was responsible for:



\- Reviewing AI-generated suggestions.

\- Implementing and modifying the application.

\- Understanding the security logic.

\- Testing application functionality.

\- Correcting issues and verifying behaviour.

\- Making final implementation decisions.



AI-generated suggestions were not treated as automatically correct. They were reviewed, modified and tested before being accepted.



\## Repository



GitHub: https://github.com/vedasruthi07/TrustVault



Latest development commit: `481885a`

