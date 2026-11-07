# API Specification - TrustVault

## Authentication & Session
* POST /login - Authenticate user session.
* GET /logout - Terminate active session.

## Document Management
* POST /api/documents/upload
  * **Role Required:** OWNER
  * **Payload:** Multipart form data (file)
  * **Success:** 201 Created
  * **Error:** 400 Bad Request

* GET /api/documents/<id>/view
  * **Role Required:** OWNER (Document Owner) or Permitted User (READ/EDIT)
  * **Success:** 200 OK (Streams PDF binary payload)
  * **Error:** 403 Forbidden / 404 Not Found

## Permission Management
* POST /api/documents/<id>/permissions
  * **Role Required:** Document Owner
  * **Payload:** {"user_id": 3, "permission_type": "READ"}
  * **Success:** 200 OK
  * **Error:** 403 Forbidden

* DELETE /api/documents/<id>/permissions/<user_id>
  * **Role Required:** Document Owner
  * **Success:** 200 OK
  * **Error:** 403 Forbidden

## Admin & Audit
* GET /api/admin/audit-logs
  * **Role Required:** ADMIN
  * **Success:** 200 OK (Returns JSON audit trail with HMAC verification state)
  * **Error:** 403 Forbidden
