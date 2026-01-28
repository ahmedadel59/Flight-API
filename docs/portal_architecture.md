# Flight Portal Architecture Documentation

This document explains the frontend JavaScript widget and backend Python controller for the Flight Portal module.

---

## Table of Contents

1. [portal_flights.js - Frontend Widget](#portal_flightsjs---frontend-widget)
2. [portal.py - Backend Controller](#portalpy---backend-controller)
3. [Visual Architecture](#visual-architecture)
4. [Request Flow Examples](#request-flow-examples)

---

## portal_flights.js - Frontend Widget

**Location:** `static/src/js/portal_flights.js`

This is an Odoo frontend widget that handles user interactions on the flight portal page.

### 1. Module Declaration & Import (Lines 1-3)

```javascript
/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
```

- Declares this as an Odoo module
- Imports Odoo's public widget framework for frontend interactivity

### 2. Widget Registration (Lines 5-10)

```javascript
selector: '.o_flight_portal',
events: {
    'click #syncBtn': '_onSyncFlights',
    'click #saveKey': '_onSaveApiKey',
},
```

| Part | Purpose | Links To |
|------|---------|----------|
| `selector: '.o_flight_portal'` | Attaches widget to elements with this class | `portal_templates.xml:21` - `<div class="o_flight_portal">` |
| `'click #syncBtn'` | Listens for clicks on sync button | `portal_templates.xml:28` - `<button id="syncBtn">` |
| `'click #saveKey'` | Listens for clicks on save API key button | `portal_templates.xml:113` - `<button id="saveKey">` |

### 3. `_onSyncFlights` Method (Lines 16-55)

**Purpose:** Syncs flight data from the AviationStack API

**Flow:**
1. Disables button, shows spinner
2. Sends POST request to `/my/flights/sync`
3. Shows success/error notification
4. Reloads page on success

**Links to:** `portal.py:180-185`
```python
@http.route('/my/flights/sync', type='json', auth='user', methods=['POST'])
def sync_flights(self, flight_type='realtime', **kwargs):
    api_service = request.env['aviationstack.api'].sudo()
    result = api_service.with_context(...).sync_flights_from_api(...)
```

### 4. `_onSaveApiKey` Method (Lines 61-100)

**Purpose:** Saves the AviationStack API key to Odoo system parameters

**Flow:**
1. Gets value from `#apiKey` input
2. Validates it's not empty
3. Sends POST to `/my/flights/set-api-key`
4. Closes modal on success

**Links to:**
- `portal_templates.xml:110` - `<input id="apiKey">`
- `portal.py:187-193`

```python
@http.route('/my/flights/set-api-key', type='json', auth='user', methods=['POST'])
def set_api_key(self, api_key='', **kwargs):
    request.env['ir.config_parameter'].sudo().set_param('aviationstack.api_key', api_key)
```

### 5. Helper Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `_closeModal(modalId)` | 107-115 | Closes Bootstrap modal by clicking its dismiss button |
| `_showNotification(message, type)` | 122-151 | Displays Bootstrap alert notifications at top of container |

---

## portal.py - Backend Controller

**Location:** `controllers/portal.py`

This is the Odoo controller that handles all HTTP routes for the flight portal.

### 1. Imports & Class Declaration (Lines 1-8)

```python
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
```

| Import | Purpose |
|--------|---------|
| `CustomerPortal` | Base class that provides portal framework (breadcrumbs, layout, authentication) |
| `portal_pager` | Helper for creating paginated lists |
| `AND` | Combines Odoo search domains |

### 2. Helper Methods (Lines 10-31)

| Method | Purpose | Used By |
|--------|---------|---------|
| `_is_admin_user()` | Checks if user has admin/manager rights | All access control |
| `_get_flight_domain()` | Returns search filter - admins see all flights, users see only their own | List & count methods |
| `_check_flight_access(flight)` | Validates user can access a specific flight record | Detail, edit, delete routes |

### 3. Portal Home Counter (Lines 13-19)

```python
def _prepare_home_portal_values(self, counters):
```

**Purpose:** Adds flight count to the portal home page (`/my`)

**Links to:** `portal_templates.xml:4-14`
```xml
<t t-set="placeholder_count" t-value="'flight_count'"/>
```

### 4. Routes Overview

| Route | Type | Method | Purpose |
|-------|------|--------|---------|
| `/my/flights` | HTTP | `portal_my_flights` | List all flights with pagination |
| `/my/flights/<id>` | HTTP | `portal_flight_detail` | View single flight details |
| `/my/flights/create` | HTTP | `portal_flight_create` | Create new flight form |
| `/my/flights/<id>/edit` | HTTP | `portal_flight_edit` | Edit flight form |
| `/my/flights/<id>/delete` | HTTP | `portal_flight_delete` | Delete a flight |
| `/my/flights/sync` | JSON | `sync_flights` | Sync from AviationStack API |
| `/my/flights/set-api-key` | JSON | `set_api_key` | Save API key |

### 5. Flight List Route (Lines 33-80)

```python
@http.route(['/my/flights', '/my/flights/page/<int:page>'], type='http', auth='user', website=True)
def portal_my_flights(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
```

**Flow:**
1. Gets user-specific domain (admin sees all, user sees own)
2. Applies search filters (flight number, origin, destination)
3. Creates pagination
4. Checks if API key is configured
5. Renders template with flight data

**Links to:**
- `portal_templates.xml:17-120` - `portal_my_flights` template
- Model: `flight.schedule`
- Config param: `aviationstack.api_key`

### 6. Flight Detail Route (Lines 82-94)

```python
@http.route(['/my/flights/<int:flight_id>'], type='http', auth='user', website=True)
def portal_flight_detail(self, flight_id, **kw):
```

**Flow:**
1. Fetches flight by ID
2. Checks access permission
3. Redirects to list if unauthorized
4. Renders detail template

**Links to:** `portal_templates.xml:123-185` - `portal_flight_detail` template

### 7. Create Flight Route (Lines 96-127)

```python
@http.route('/my/flights/create', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
def portal_flight_create(self, **post):
```

**Flow:**
- **GET:** Renders empty form
- **POST:** Creates `flight.schedule` record with:
  - Parsed datetime fields
  - `is_from_api: False` (manual entry)
  - `user_id`: current user

**Links to:** `portal_templates.xml:188-243` - `portal_flight_create` template

### 8. Edit Flight Route (Lines 129-168)

```python
@http.route('/my/flights/<int:flight_id>/edit', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
def portal_flight_edit(self, flight_id, **post):
```

**Flow:**
- **GET:** Renders form pre-filled with flight data
- **POST:** Updates only provided fields (partial update pattern)

**Links to:** `portal_templates.xml:246-308` - `portal_flight_edit` template

### 9. Delete Flight Route (Lines 170-178)

```python
@http.route('/my/flights/<int:flight_id>/delete', type='http', auth='user', website=True, methods=['POST'], csrf=True)
def portal_flight_delete(self, flight_id, **post):
```

**Flow:**
1. Checks access
2. Deletes record if authorized
3. Redirects to list

**Links to:** `portal_templates.xml:81-86` - Delete form button

### 10. API Sync Route (Lines 180-185)

```python
@http.route('/my/flights/sync', type='json', auth='user', methods=['POST'])
def sync_flights(self, flight_type='realtime', **kwargs):
```

**Purpose:** Triggers flight sync from AviationStack API

**Links to:**
- `portal_flights.js:25-36` - JS `fetch('/my/flights/sync')`
- Model: `aviationstack.api` service

### 11. Set API Key Route (Lines 187-193)

```python
@http.route('/my/flights/set-api-key', type='json', auth='user', methods=['POST'])
def set_api_key(self, api_key='', **kwargs):
```

**Purpose:** Saves API key to Odoo system parameters

**Links to:**
- `portal_flights.js:72-83` - JS `fetch('/my/flights/set-api-key')`
- Stores in: `ir.config_parameter` with key `aviationstack.api_key`

---

## Visual Architecture

### JavaScript Widget Connection

```
┌─────────────────────────────────────────────────────────────┐
│  portal_templates.xml                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ <div class="o_flight_portal">  ← Widget attaches here │  │
│  │   ┌─────────────┐  ┌─────────────┐                    │  │
│  │   │ #syncBtn    │  │ #saveKey    │                    │  │
│  │   └──────┬──────┘  └──────┬──────┘                    │  │
│  └──────────┼────────────────┼───────────────────────────┘  │
└─────────────┼────────────────┼──────────────────────────────┘
              │                │
              ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│  portal_flights.js                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ _onSyncFlights()    │  │ _onSaveApiKey()     │           │
│  │ POST /my/flights/   │  │ POST /my/flights/   │           │
│  │      sync           │  │      set-api-key    │           │
│  └──────────┬──────────┘  └──────────┬──────────┘           │
└─────────────┼────────────────────────┼──────────────────────┘
              │                        │
              ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│  portal.py (Controller)                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ sync_flights()      │  │ set_api_key()       │           │
│  │ → aviationstack.api │  │ → ir.config_param   │           │
│  └─────────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              BROWSER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  portal_flights.js          │  HTML Forms (templates)                    │
│  ├─ fetch('/my/flights/     │  ├─ POST /my/flights/create               │
│  │        sync')            │  ├─ POST /my/flights/<id>/edit            │
│  └─ fetch('/my/flights/     │  └─ POST /my/flights/<id>/delete          │
│           set-api-key')     │                                            │
└──────────────┬──────────────┴────────────────┬──────────────────────────┘
               │ JSON                          │ HTTP
               ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         portal.py (Controller)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  HTTP Routes (type='http')           │  JSON Routes (type='json')        │
│  ┌─────────────────────────────────┐ │ ┌─────────────────────────────┐   │
│  │ /my/flights      → list view    │ │ │ /my/flights/sync            │   │
│  │ /my/flights/<id> → detail view  │ │ │ /my/flights/set-api-key     │   │
│  │ /my/flights/create              │ │ └──────────────┬──────────────┘   │
│  │ /my/flights/<id>/edit           │ │                │                  │
│  │ /my/flights/<id>/delete         │ │                │                  │
│  └────────────────┬────────────────┘ │                │                  │
└───────────────────┼──────────────────┴────────────────┼──────────────────┘
                    │                                   │
                    ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           ODOO MODELS                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  flight.schedule          │  aviationstack.api    │  ir.config_parameter │
│  ├─ flight_number         │  └─ sync_flights_     │  └─ aviationstack.   │
│  ├─ origin/destination    │       from_api()      │       api_key        │
│  ├─ departure/arrival     │                       │                      │
│  ├─ price, status         │                       │                      │
│  ├─ is_from_api           │                       │                      │
│  └─ user_id               │                       │                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Examples

### 1. User views flight list

```
Browser → GET /my/flights → portal_my_flights() → flight.schedule.search()
       → render portal_my_flights template → HTML response
```

### 2. User clicks "Sync from API"

```
Browser → portal_flights.js._onSyncFlights() → POST /my/flights/sync
       → sync_flights() → aviationstack.api.sync_flights_from_api()
       → JSON response → JS reloads page
```

### 3. User creates a flight

```
Browser → POST /my/flights/create (form data) → portal_flight_create()
       → flight.schedule.create() → redirect /my/flights
```

### 4. User saves API key

```
Browser → portal_flights.js._onSaveApiKey() → POST /my/flights/set-api-key
       → set_api_key() → ir.config_parameter.set_param()
       → JSON response → JS closes modal
```

### 5. User edits a flight

```
Browser → GET /my/flights/<id>/edit → portal_flight_edit()
       → render portal_flight_edit template (pre-filled form)
       → User submits → POST /my/flights/<id>/edit
       → flight.write() → redirect to detail page
```

### 6. User deletes a flight

```
Browser → POST /my/flights/<id>/delete (form submit)
       → portal_flight_delete() → _check_flight_access()
       → flight.unlink() → redirect /my/flights
```

---

## File Cross-Reference

| File | Type | Purpose |
|------|------|---------|
| `controllers/portal.py` | Python | HTTP/JSON route handlers |
| `static/src/js/portal_flights.js` | JavaScript | Frontend widget for AJAX operations |
| `views/portal_templates.xml` | XML | QWeb templates for HTML rendering |
| `models/flight_schedule.py` | Python | Flight data model |
| `models/aviationstack_api.py` | Python | External API integration service |
