# Validation Framework - Architecture Diagram

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Form Submission / API Request
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FLASK ROUTE                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  @app.route('/endpoint', methods=['POST'])                   │  │
│  │  def endpoint():                                             │  │
│  │      try:                                                    │  │
│  │          # Step 1: Validate input                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     VALIDATORS MODULE                                │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │ require_fields │  │   parse_int    │  │  parse_float   │       │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘       │
│           │                   │                   │                 │
│           └───────────────────┴───────────────────┘                 │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────┐                            │
│                    │  Validation OK?  │                            │
│                    └────────┬─────────┘                            │
│                             │                                      │
│          ┌──────────────────┴──────────────────┐                  │
│          │ YES                                  │ NO               │
│          ▼                                      ▼                  │
│  ┌───────────────┐                   ┌──────────────────┐         │
│  │ Return Valid  │                   │ Raise            │         │
│  │ Data          │                   │ ValidationError  │         │
│  └───────┬───────┘                   └──────────┬───────┘         │
└──────────┼──────────────────────────────────────┼──────────────────┘
           │                                      │
           │                                      │
┌──────────┴──────────────────┐    ┌─────────────┴─────────────────┐
│   SUCCESS PATH              │    │    ERROR PATH                  │
│                             │    │                                │
│  ┌──────────────────────┐   │    │  ┌──────────────────────────┐ │
│  │ Process validated    │   │    │  │ Catch ValidationError    │ │
│  │ data                 │   │    │  │                          │ │
│  └──────────┬───────────┘   │    │  └──────────┬───────────────┘ │
│             │                │    │             │                 │
│             ▼                │    │             ▼                 │
│  ┌──────────────────────┐   │    │  ┌──────────────────────────┐ │
│  │ Sanitize for storage │   │    │  │ flash(e.message,         │ │
│  │ (CSV injection prev.)│   │    │  │       "error")           │ │
│  └──────────┬───────────┘   │    │  └──────────┬───────────────┘ │
│             │                │    │             │                 │
│             ▼                │    │             ▼                 │
│  ┌──────────────────────┐   │    │  ┌──────────────────────────┐ │
│  │ Save to database/CSV │   │    │  │ Return to form with      │ │
│  │                      │   │    │  │ error message            │ │
│  └──────────┬───────────┘   │    │  └──────────┬───────────────┘ │
│             │                │    │             │                 │
│             ▼                │    │             │                 │
│  ┌──────────────────────┐   │    │             │                 │
│  │ flash("Success!",    │   │    │             │                 │
│  │       "success")     │   │    │             │                 │
│  └──────────┬───────────┘   │    │             │                 │
│             │                │    │             │                 │
│             ▼                │    │             ▼                 │
│  ┌──────────────────────┐   │    │  ┌──────────────────────────┐ │
│  │ redirect(success)    │   │    │  │ render_template(form)    │ │
│  └──────────────────────┘   │    │  └──────────────────────────┘ │
└─────────────┬────────────────┘    └─────────────┬─────────────────┘
              │                                    │
              └────────────────┬───────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TEMPLATE RENDERING                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  {% with messages = get_flashed_messages() %}              │    │
│  │    {% if messages %}                                       │    │
│  │      <div class="flash-message flash-{{ category }}">      │    │
│  │        {{ message }}                                       │    │
│  │      </div>                                                │    │
│  │    {% endif %}                                             │    │
│  │  {% endwith %}                                             │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         USER FEEDBACK                                │
│                                                                      │
│  SUCCESS:  ┌──────────────────────────────────────────────────┐   │
│            │ ✅ Product 'Milk' added successfully!        [×] │   │
│            └──────────────────────────────────────────────────┘   │
│                                                                      │
│  ERROR:    ┌──────────────────────────────────────────────────┐   │
│            │ ❌ Field 'Stock' must be at least 0         [×] │   │
│            └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Validation Function Hierarchy

```
validators.py
│
├─── ValidationError (Exception)
│    ├─── message: str
│    ├─── field: str
│    └─── to_dict() -> dict
│
├─── Core Validators
│    │
│    ├─── require_fields(data, fields)
│    │    └─── Checks: None, empty, whitespace
│    │
│    ├─── parse_int(name, value, min, max)
│    │    └─── Checks: type, range
│    │
│    ├─── parse_float(name, value, min, max, decimals)
│    │    └─── Checks: type, range, precision
│    │
│    ├─── validate_string(name, value, min_len, max_len, pattern, trim)
│    │    └─── Checks: type, length, format
│    │
│    └─── validate_date(name, value, format, future/past)
│         └─── Checks: format, range
│
├─── Domain Validators
│    │
│    ├─── validate_gst(value)
│    │    └─── Uses: parse_float(0-50%, 2 decimals)
│    │
│    ├─── validate_product_id(value)
│    │    └─── Uses: validate_string(1-50 chars)
│    │
│    ├─── validate_inventory_item(data)
│    │    ├─── Uses: require_fields()
│    │    ├─── Uses: validate_product_id()
│    │    ├─── Uses: validate_string() × 3
│    │    ├─── Uses: parse_int()
│    │    ├─── Uses: parse_float()
│    │    └─── Uses: validate_date()
│    │
│    └─── validate_user_credentials(data)
│         ├─── Uses: require_fields()
│         └─── Uses: validate_string() × 2
│
└─── Security Utilities
     │
     └─── sanitize_for_csv(value)
          └─── Escapes: =, +, -, @
```

---

## Data Flow Example: Adding Inventory Item

```
1. USER INPUT
   ┌─────────────────────────────────┐
   │ Form Submission                 │
   │ ─────────────                   │
   │ id: "PROD001"                   │
   │ name: "  Milk  "                │
   │ category: "Dairy"               │
   │ stock: "100"                    │
   │ price: "45.50"                  │
   │ supplier: "DairyFarm"           │
   │ expiry_date: "2025-12-31"       │
   └─────────────────────────────────┘
                 │
                 ▼
2. VALIDATION
   ┌─────────────────────────────────┐
   │ validate_inventory_item()       │
   │ ─────────────────────────────   │
   │ ✓ All required fields present   │
   │ ✓ id: "PROD001" (valid)         │
   │ ✓ name: "Milk" (trimmed)        │
   │ ✓ category: "Dairy" (valid)     │
   │ ✓ stock: 100 (int ≥ 0)          │
   │ ✓ price: 45.5 (float ≥ 0)       │
   │ ✓ supplier: "DairyFarm" (valid) │
   │ ✓ expiry: "2025-12-31" (valid)  │
   └─────────────────────────────────┘
                 │
                 ▼
3. SANITIZATION
   ┌─────────────────────────────────┐
   │ sanitize_for_csv()              │
   │ ─────────────────────────────   │
   │ ✓ Escape formula characters     │
   │ ✓ No injection risk detected    │
   └─────────────────────────────────┘
                 │
                 ▼
4. STORAGE
   ┌─────────────────────────────────┐
   │ Save to inventory.csv           │
   │ ─────────────────────────────   │
   │ PROD001,Milk,Dairy,100,45.5,... │
   └─────────────────────────────────┘
                 │
                 ▼
5. FEEDBACK
   ┌─────────────────────────────────┐
   │ ✅ Success Flash Message        │
   │ "Product 'Milk' added!"         │
   └─────────────────────────────────┘
```

---

## Error Handling Flow

```
INPUT: stock = "-10"
│
├─ ROUTE: /inventory (POST)
│  └─ validate_inventory_item(request.form)
│     │
│     └─ parse_int('Stock', '-10', min_val=0)
│        │
│        ├─ Convert to int: -10 ✓
│        │
│        ├─ Check min_val: -10 < 0 ✗
│        │
│        └─ RAISE ValidationError(
│             message="Field 'Stock' must be at least 0",
│             field="Stock"
│          )
│
├─ CATCH ValidationError in route
│  └─ flash(e.message, "error")
│
├─ RENDER template with error
│  └─ Display flash message:
│      ┌────────────────────────────────────┐
│      │ ❌ Field 'Stock' must be at least 0│
│      └────────────────────────────────────┘
│
└─ USER sees clear, actionable error
   (NOT: "500 Internal Server Error")
```

---

## Security Flow: CSV Injection Prevention

```
INPUT: name = "=SUM(A1:A10)"
│
├─ VALIDATION: validate_string() → PASS
│  (String is valid format)
│
├─ SANITIZATION: sanitize_for_csv()
│  │
│  ├─ Detect dangerous prefix: '='
│  │
│  ├─ Add safety quote: "'=SUM(A1:A10)"
│  │
│  └─ RETURN: "'=SUM(A1:A10)"
│
├─ STORAGE: Save to CSV
│  └─ File content: ...,'''=SUM(A1:A10)',...
│
└─ RESULT: Formula treated as text, not executed
   ✅ Security threat neutralized
```

---

## Test Coverage Map

```
validators.py (100% coverage)
│
├─── ValidationError
│    └─── test_validators.py
│         ├─── test_error_message()
│         ├─── test_to_dict()
│         └─── test_error_without_field()
│
├─── require_fields()
│    └─── test_validators.py
│         ├─── test_all_fields_present()
│         ├─── test_missing_field_raises_error()
│         ├─── test_empty_string_raises_error()
│         ├─── test_whitespace_only_raises_error()
│         └─── test_none_value_raises_error()
│
├─── parse_int()
│    └─── test_validators.py
│         ├─── test_valid_integer()
│         ├─── test_string_integer()
│         ├─── test_negative_integer()
│         ├─── test_invalid_format_raises_error()
│         ├─── test_float_string_raises_error()
│         ├─── test_min_constraint()
│         ├─── test_max_constraint()
│         ├─── test_value_at_min_boundary()
│         └─── test_value_at_max_boundary()
│
└─── ... (all functions tested)

Integration tests (test_app_validation.py)
│
├─── Registration Flow
│    ├─── test_register_valid_user()
│    ├─── test_register_short_username()
│    ├─── test_register_short_password()
│    ├─── test_register_missing_username()
│    └─── test_register_duplicate_username()
│
├─── Login Flow
│    ├─── test_login_valid_credentials()
│    ├─── test_login_invalid_credentials()
│    └─── test_login_missing_fields()
│
└─── Inventory Flow
     ├─── test_inventory_negative_stock()
     ├─── test_inventory_negative_price()
     ├─── test_inventory_invalid_stock_format()
     └─── test_inventory_missing_required_fields()
```

---

**Architecture designed for:**
- ✅ Security (CSV injection prevention)
- ✅ Reliability (comprehensive validation)
- ✅ User Experience (clear error messages)
- ✅ Maintainability (modular design)
- ✅ Testability (100% test coverage)

