\# TrustVault — API Documentation



\## 1. Introduction



TrustVault provides backend endpoints for user authentication, document management, permission control and administrative audit-log access.



The application uses Python Flask and JSON-based API responses for document and permission operations.



\## 2. Authentication and Authorization



Protected API endpoints require an authenticated user session.



The application uses the following roles and permission levels:



| Role / Permission | Description |

|---|---|

| OWNER | Manages documents owned by the user and sharing permissions |

| READ | Can view and download shared documents |

| EDIT | Can view, download and edit shared documents |

| ADMIN | Can access administrative audit logs |



All document permissions are checked on the server.



\## 3. API Endpoints



\### 3.1 CSRF Token



\*\*Endpoint:\*\* `/api/csrf-token`



\*\*Method:\*\* GET



\*\*Access:\*\* Public



\*\*Purpose:\*\* Provides a CSRF token for protected requests.



\*\*Response:\*\* Returns a JSON object containing the CSRF token.



\### 3.2 Document Upload



\*\*Endpoint:\*\* `/api/documents/upload`



\*\*Method:\*\* POST



\*\*Access:\*\* Authenticated users



\*\*Purpose:\*\* Uploads a PDF document to private storage.



\*\*Validation:\*\*

\- PDF file validation.

\- Maximum upload size of 10 MB.

\- Document metadata is stored in the database.



\*\*Security:\*\* Uploaded files are not stored in the public static directory.



\### 3.3 Document Search



\*\*Endpoint:\*\* `/api/documents/search`



\*\*Method:\*\* GET



\*\*Access:\*\* Authenticated users



\*\*Purpose:\*\* Searches documents owned by the current user and documents shared with them.



\*\*Supported filters:\*\*

\- Document title.

\- Owner.

\- Category.

\- Start date.

\- End date.



\*\*Response:\*\* Returns matching document information, including document ID, title, filename, category, owner, creation date and permission level.



\### 3.4 View Document



\*\*Endpoint:\*\* `/api

