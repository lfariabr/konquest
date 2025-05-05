# dataWrestler

The `dataWrestler` component transforms raw data into actionable insights for admins and operators. It delivers daily operational visibility across contacts, messaging, and campaign performance—serving as the analytics backbone of the system.

## Overview

This system is responsible for generating analytics across three major areas:

### 1. Contact Analytics  
Tracks and aggregates contact behavior over time:
- 📅 Contacts grouped by **month**
- 🏷️ Contacts by **relationship tag** and **source**
- 🔁 Contacts converted into **Leads**, **Appointments**, and **Revenue**

> Data source: `@core` (contact records, lead status, financial data)

---

### 2. Message Analytics  
Monitors the system's messaging activity:
- 📅 Messages grouped by **month**
- 📱 Messages per **userphone/token**
- 🧩 Messages segmented by **relationship tag**

> Data source: `@core` (message logs, contact-token mappings)

---

### 3. Media Campaign Analytics  
Focused analysis of contacts originating from paid media:
- 📅 Metrics grouped by **month** and **day**
- 📊 Breakdowns by media tags (e.g., *Instagram*, *Botox*, *Preenchimento*)
- 💰 Revenue and ROI from Leads/Appointments derived from campaigns

> Data source: `@core` (contact tags, attribution, financials)

---

## Key Features

- ✅ **Custom Analytics Dashboards**  
  Fully tailored HTML views rendered via Django with a modern UI for business users.

- ⚙️ **Advanced Django ORM Usage**  
  Uses `Q`, `TruncMonth`, `Sum`, `Count`, and other ORM expressions for efficient data aggregation and filtering.

---

## Dependencies

- `@core`: Primary source of truth for contact data, tags, lead status, and revenue.
- `@media`: (optional) If media campaign tagging is integrated externally.

---