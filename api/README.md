# api

The `api` component is a feature from Konquista that provides endpoints where customers can access data via restful api requests.

---

## 📌 Overview

The `api` module is responsible for providing endpoints where customers can access data such as Contacts and Sent Messages via restful api requests.

---

### 1. 🧲 Contacts

Endpoints for Contacts with fields such as:

- `created date`, `source`, `store`, `name`, `priority`, `telephone`, `email`, `message`, `relationship_tag`

**Usage:**

- Fetch data from `Contacts`

---

### 2. 📅 Sent Messages

Endpoints for Sent Messages with fields like:

- `sent at`, `relationship_tag`, `contact phone`, `message`, `sender_phone_name` 

**Usage:**

- Fetch data from `Sent Messages`

## ⚙️ Key Features

- ✅ **Django Rest Framework**  
  Provides endpoints for Contacts and Sent Messages

- 🔗 **... ?**  
  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam nec metus vel ante feugiat placerat. Nullam nec metus vel ante feugiat placerat.

---

## 📦 Dependencies

- **@core** module:  
  Exposes models and serializers for Contacts and Sent Messages

---

# Progress

basic DRF (Django REST Framework) API with:

1. Models:
- Using direct imports from core models (Contact and MessageLogs)
- No proxy models or model extensions
2. Serializers:
- Basic ModelSerializer using fields = '__all__'
- No custom validation or field-level customization
3. Views:
- Basic ModelViewSet for both models
- No custom actions or filtering
4. URLs:
- Properly configured with DRF's DefaultRouter
- Endpoints at /api/contacts/ and /api/messagelogs/

# Recommendations for Improvement
1. Model Layer
- Proxy Models: Create proxy models in api/models/ to keep API-specific logic separate from core models
- Custom Managers: Add custom managers for API-specific queries
2. Serializers
- Field Selection: Explicitly define fields instead of using __all__
- Validation: Add field-level and object-level validation
- Nested Serializers: For related fields
- Read-Only Fields: Mark appropriate fields as read-only
3. Views
- Permissions: Add proper permission classes
- Filtering: Add filtering and search capabilities
- Pagination: Configure pagination
- Custom Actions: Add custom endpoints for common operations
4. Security
- Authentication: Set up token authentication
- Throttling: Implement rate limiting
- CORS: Configure CORS headers

# Next Steps
1. Basic Enhancements:
- Add proper field definitions to serializers
- Add basic filtering and search
- Set up pagination
2. Advanced Features:
- Add custom actions to viewsets
- Implement token authentication
- Add comprehensive documentation
3. Testing:
- Set up API tests
- Add test coverage
