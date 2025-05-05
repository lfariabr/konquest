# apiCrm

The `apiCrm` component is a deep connection with Pró-Corpo's custom ERP system, integrating with various endpoints available in the GraphQL API.

---

## 📌 Overview

The `apiCrm` module is responsible for managing contact records from Pró-Corpo's ERP system through automated syncing and campaign logic.

---

### 1. 🧲 Lead

Fetches leads via GraphQL with fields such as:

- `created date`, `source`, `store`, `status`, `customer`, `name`, `telephone`, `email`, `message`, `utmMedium`, `utmContent`, `utmCampaign`, `utmSearch`, `utmTerm`

**Usage:**

- Compare leads with local `Contacts` to identify who became a lead  
- Trigger follow-ups and targeted CRM campaigns (e.g., leads with status **NCC** receive specific campaigns via `core` and `messageShooter`)

---

### 2. 📅 Appointment

Fetches appointments via GraphQL with fields like:

- `created date`, `store`, `status`, `customer`, `name`, `telephone`, `email`, `message`, `procedure`

**Usage:**

- Compare appointments with `Contacts` to determine follow-up needs  
- Campaign targeting for statuses like **Served**, using `core` and `messageShooter`

---

### 3. 💳 Bill Charges

Fetches bill charges via GraphQL including:

- `created date`, `store`, `status`, `value purchased`, `procedure purchased`, etc.

**Usage:**

- Match with `Contacts` for purchase behavior tracking  
- Initiate specific campaigns for contacts with status **Bought**

---

## ⚙️ Key Features

- ✅ **Celery Task Integration**  
  Periodically fetches, syncs, and cleans contact data via Celery tasks

- 🔗 **GraphQL Integration**  
  Full support for custom queries, schemas, and resolvers

---

## 📦 Dependencies

- **@core** module:  
  Handles creation and updates to the `Contact` model based on fetched data

---