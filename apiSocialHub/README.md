# apiSocialHub

The `apiSocialHub` component integrates directly with the [SocialHub](https://socialhub.pro/) platform — a WhatsApp-based CRM and marketing tool — to send both text and file-based messages using their REST API.

---

## 📌 Overview

This module is responsible for two core functionalities:

---

### 1. 📁 Send File Message

Handles media-based communication using:

```python
send_file_message(phone, message, token_socialhub, file_path)
```

- Sends files such as images, videos, and audio clips  
- Utilizes SocialHub’s REST API with a valid token tied to a specific `UserPhone`

---

### 2. 💬 Send Text Message

Handles plain text message dispatch:

- Sends text-only messages  
- Optionally includes a file if `file_path` is provided

---

## ⚙️ Key Features

- ✅ **Monitoring & Alerts**  
  Includes daily monitoring of message dispatch queues:
  - Success and failure reports  
  - Email and Discord notifications for real-time visibility

- 🔐 **Token-Based Authentication**  
  All requests are authorized using WhatsApp tokens tied to `UserPhone` records in the system

---

## 📦 Dependencies

- `@core` module provides:
  - Contact information (e.g., phone, tags)  
  - Message content (text, files)  
  - User and token associations  
  - Message logging and dispatch tracking

---

## 📝 Notes

- Ensure all `UserPhone` tokens are synchronized and valid before dispatch  
- File paths must point to accessible media files on the backend
