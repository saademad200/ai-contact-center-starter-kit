# Decouple Admin Dashboard to Frontend SPA

This plan addresses your request to loosely couple the frontend and backend by moving the Admin Dashboard out of the Python codebase and into the `frontend/` Nginx container as a static Single Page Application (SPA).

## Proposed Architecture

Currently, the Admin Dashboard is **Server-Side Rendered (SSR)** using FastAPI and Jinja2 templates (`backend/app/admin/views.py`). This tightly couples the UI to the backend code.

We will transition to a **Client-Side Rendered (SPA)** approach:
1. Nginx (in the Frontend container) will serve all HTML/CSS/JS for the landing page, the chat widget, *and* the Admin Dashboard.
2. The Admin Dashboard UI will use vanilla Javascript `fetch()` calls to interact with the backend purely via JSON REST APIs (`/api/v1/...`).
3. Authentication will switch from server-side session cookies to JWT tokens stored in `localStorage`.

## Proposed Changes

### 1. Infrastructure (Terraform)
We need to update the ALB routing rules so that traffic to `/admin/*` goes to the Frontend container (Nginx) instead of the Backend container (FastAPI).

#### [MODIFY] [load_balancer/main.tf](file:///home/saad/Documents/Code/Devops/Project/infrastructure/terraform/modules/load_balancer/main.tf)
- Update `aws_lb_listener_rule.api_routing` to only forward `/api/*` and `/ws/*` to the backend. Traffic for `/admin/*` will fall back to the default rule (Frontend).

### 2. Backend Codebase (FastAPI)
Remove all server-side HTML rendering capabilities. The backend will become a pure JSON API.

#### [MODIFY] [main.py](file:///home/saad/Documents/Code/Devops/Project/backend/app/main.py)
- Remove `admin_views.router` and static file mounts.
- Remove `SessionMiddleware`.

#### [DELETE] [backend/app/admin/views.py](file:///home/saad/Documents/Code/Devops/Project/backend/app/admin/views.py)
- This file is no longer needed. The existing routers in `app/routers/` (e.g. `llmops.py`, `documents.py`) already provide the necessary JSON endpoints.

### 3. Frontend Codebase (Nginx SPA)
Move the Jinja2 templates into the `frontend/` folder and rewrite them into standard HTML + JS.

#### [NEW] [frontend/admin/login.html](file:///home/saad/Documents/Code/Devops/Project/frontend/admin/login.html)
- Standard HTML login form.
- Vanilla JS to `POST /api/v1/auth/token` and save the resulting JWT to `localStorage`.

#### [NEW] [frontend/admin/dashboard.html](file:///home/saad/Documents/Code/Devops/Project/frontend/admin/dashboard.html) (and other pages)
- Standard HTML templates without `{% ... %}` Jinja2 syntax.
- Vanilla JS that runs on page load, fetches data from `/api/v1/...` using the JWT token, and populates the DOM tables dynamically.

#### [NEW] [frontend/admin/admin.css](file:///home/saad/Documents/Code/Devops/Project/frontend/admin/admin.css) and `admin.js`
- Relocated from the backend. `admin.js` will be heavily expanded to handle API fetching, JWT authentication checks, and DOM manipulation.

#### [MODIFY] [frontend/nginx.conf](file:///home/saad/Documents/Code/Devops/Project/frontend/nginx.conf)
- Ensure Nginx properly serves requests to `/admin/` by routing them to `/admin/dashboard.html` or `/admin/login.html`.

## Verification Plan

1. Verify Terraform applies successfully to update ALB routing.
2. Verify visiting `http://localhost/admin/login` loads the static SPA login page served by Nginx.
3. Verify logging in successfully calls the FastAPI JSON endpoint, receives a JWT, and redirects to the dashboard.
4. Verify the dashboard successfully fetches stats from the backend and renders them via Javascript.
5. Verify no backend API endpoints return HTML.
