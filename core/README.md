# core

The `core` component is the heart of the Konquista system. It contains the essential data models and logic required to operate the SaaS application, providing a centralized source of truth for contacts, users, messages, tokens, and system logs.

---

## Overview

The `core` module is responsible for managing five critical domains:

---

### 1. **Contact**

Manages all contact records entering the system, whether via:
- `@apiSocialHub` (via REST API or .csv upload)
- `@apiCrm` (via GraphQL fetch from Pró-Corpo’s ERP)

The contact model is fully compatible with `.csv` exports from **[SocialHub](https://socialhub.pro/)** — a marketing platform for WhatsApp that supports:
> Multi-agent routing, WhatsApp bots, integrated CRM, marketing campaigns, contact management, reporting, and more.

**Contact Fields Include:**
- Name, phone number, created date
- Relationship tag (e.g., *lead*, *appointment*)
- Source-specific details (for WhatsApp, appointments, chatbot interactions)
- ERP integration fields from `@apiCrm` (e.g., is_lead, is_appointment, revenue info)

---

### 2. **Message**

Defines all message templates used across campaigns.

**Message Fields:**
- Title, text content, file (optional), file_type (e.g., mp3, mp4, jpeg)
- Counter (defines message sequence: 0 = first, 1 = second, etc.)
- Relationship tag (target group)
- Contact type (e.g., *Botox*, *NPS*, *Appointment*)
- Created timestamp

---

### 3. **User**

Handles platform users (admins, operators, etc.).

**User Fields:**
- Name, email, password, company, created_at

---

### 4. **UserPhone**

Represents phone numbers (tokens) connected to the system, typically via SocialHub.

**UserPhone Fields:**
- User, phone number, token (for WhatsApp integration)
- Relationship tag, phone description

---

### 5. **MessageLogs**

Tracks all messages sent to contacts for traceability and analytics.

**MessageLog Fields:**
- Message, contact, user, user_phone, status, sent_at, relationship tag

---

## Key Features

- ✅ **Celery Task Integration**  
  Periodically fetches and syncs contacts from `@apiCrm` (GraphQL).

- 📥 **Manual Upload Support**  
  Allows batch import of SocialHub contacts via `.csv`.

- 📊 **DataWrestler Compatibility**  
  Acts as the primary data source for analytics and reporting.

---

## Dependencies

- `@apiCrm`: Pulls lead and appointment status
- `@apiSocialHub`: Integrates WhatsApp tokens and contact uploads
- `@dataWrestler`: Consumes contact and message data for reporting

---