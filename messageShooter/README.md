# messageShooter

The `messageShooter` component is the core engine responsible for managing message campaigns, organizing target recipients, and dispatching messages through asynchronous queues.

## Overview

This system handles three primary responsibilities:

1. **Campaigns**  
   Define scheduling rules for dispatching messages, such as:
   - Days of the week
   - Time ranges
   - Frequency of execution  
   Campaigns pull **Contacts**, **Messages**, and **Phone Tokens** from the `@core` module.

2. **Target Lists**  
   Each campaign generates a list of recipients based on:
   - Message `counter` logic
   - Contact relationship tags (e.g., lead, appointment)  
   These lists determine who will receive the next message in sequence.

3. **Queues**  
   Campaign target lists are placed into queues for processing.  
   The `@queue_processor` uses the `@apiSocialHub` integration to send messages and logs each interaction to `@core/message_logs`.

## Key Features

- ✅ **1 Queue = 1 Token**  
  Each message queue is tied to a single WhatsApp phone token for sending.

- 🚀 **Async Multi-Queue Processing**  
  Multiple queues can run in parallel using asynchronous execution.

- ⏱ **Rate Limiting**  
  Enforces an 16-second interval between recipients in a queue.

- 🔁 **Sequential Message Delivery**  
  Messages are sent in order, based on the recipient's position in the `counter` history from logs.

- ⚙️ **Scheduler Integration**  
  The `run_scheduler` task acts as the main worker, triggering campaign rules and initializing target list generation.

## Dependencies

- `@core`: Provides contact data, tokens, and message content
- `@apiSocialHub`: Sends messages through the external platform
- `@queue_processor`: Handles message dispatch and error handling
- `@core/message_logs`: Stores message history and counters

---