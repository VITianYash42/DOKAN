"""
Example: Using the Validation Framework

This file demonstrates how to use the validation framework
in different scenarios.
"""

from validators import (
    ValidationError,
    require_fields,
    parse_int,
    parse_float,
    validate_string,
    validate_inventory_item,
    validate_user_credentials,
    sanitize_for_csv
)


def example_1_basic_validation():
    """Example 1: Basic field validation"""
    print("=" * 60)
    print("Example 1: Basic Field Validation")
    print("=" * 60)

    # Simulating form data
    form_data = {
        'product_name': '  Milk  ',
        'quantity': '100',
        'price': '45.50'
    }

    try:
        # Validate required fields
        require_fields(form_data, ['product_name', 'quantity', 'price'])

        # Parse and validate each field
        name = validate_string('Product Name', form_data['product_name'])
        quantity = parse_int('Quantity', form_data['quantity'], min_val=0)
        price = parse_float('Price', form_data['price'], min_val=0.0, decimals=2)

        print(f"✅ Valid input:")
        print(f"   Name: '{name}'")
        print(f"   Quantity: {quantity}")
        print(f"   Price: ₹{price}")

    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")


def example_2_invalid_input():
    """Example 2: Handling invalid input"""
    print("\n" + "=" * 60)
    print("Example 2: Invalid Input Handling")
    print("=" * 60)

    test_cases = [
        ('Negative quantity', {'quantity': '-10'}),
        ('Invalid price format', {'price': 'abc'}),
        ('Empty name', {'name': '   '}),
        ('Too short username', {'username': 'ab', 'password': 'password123'}),
    ]

    for description, data in test_cases:
        try:
            if 'quantity' in data:
                parse_int('Quantity', data['quantity'], min_val=0)
            elif 'price' in data:
                parse_float('Price', data['price'], min_val=0.0)
            elif 'name' in data:
                validate_string('Name', data['name'], min_length=1)
            elif 'username' in data:
                validate_user_credentials(data)

        except ValidationError as e:
            print(f"❌ {description}: {e.message}")


def example_3_inventory_validation():
    """Example 3: Complete inventory item validation"""
    print("\n" + "=" * 60)
    print("Example 3: Inventory Item Validation")
    print("=" * 60)

    # Valid inventory item
    valid_item = {
        'id': 'PROD001',
        'name': 'Tata Tea Gold',
        'category': 'Beverages',
        'stock': '250',
        'price': '245.00',
        'supplier': 'Tata Consumer Products',
        'expiry_date': '2026-12-31'
    }

    try:
        validated = validate_inventory_item(valid_item)
        print("✅ Valid inventory item:")
        for key, value in validated.items():
            print(f"   {key}: {value}")
    except ValidationError as e:
        print(f"❌ Error: {e.message}")

    # Invalid inventory item (negative stock)
    print("\n" + "Trying invalid item (negative stock)...")
    invalid_item = valid_item.copy()
    invalid_item['stock'] = '-50'

    try:
        validate_inventory_item(invalid_item)
    except ValidationError as e:
        print(f"❌ Caught error: {e.message}")


def example_4_csv_sanitization():
    """Example 4: CSV injection prevention"""
    print("\n" + "=" * 60)
    print("Example 4: CSV Injection Prevention")
    print("=" * 60)

    dangerous_inputs = [
        '=SUM(A1:A10)',
        '+1234567890',
        '-5000',
        '@USERNAME',
        'Normal text'
    ]

    print("Input → Sanitized Output:")
    for input_val in dangerous_inputs:
        output = sanitize_for_csv(input_val)
        indicator = "🛡️" if input_val != output else "✅"
        print(f"   {indicator} '{input_val}' → '{output}'")


def example_5_user_registration():
    """Example 5: User registration validation"""
    print("\n" + "=" * 60)
    print("Example 5: User Registration Validation")
    print("=" * 60)

    test_users = [
        ('Valid user', {'username': 'shopkeeper01', 'password': 'secure123'}),
        ('Short username', {'username': 'ab', 'password': 'password123'}),
        ('Short password', {'username': 'shopkeeper01', 'password': '12345'}),
        ('Missing field', {'username': 'shopkeeper01'}),
    ]

    for description, user_data in test_users:
        try:
            username, password = validate_user_credentials(user_data)
            print(f"✅ {description}: username='{username}', password length={len(password)}")
        except ValidationError as e:
            print(f"❌ {description}: {e.message}")


def example_6_range_validation():
    """Example 6: Numeric range validation"""
    print("\n" + "=" * 60)
    print("Example 6: Numeric Range Validation")
    print("=" * 60)

    test_values = [
        ('Stock (0-1000)', 'stock', 500, 0, 1000),
        ('Stock too high', 'stock', 1500, 0, 1000),
        ('Stock negative', 'stock', -10, 0, 1000),
        ('Discount (0-100%)', 'discount', 15.5, 0, 100),
        ('Discount too high', 'discount', 150, 0, 100),
    ]

    for description, field_name, value, min_val, max_val in test_values:
        try:
            if isinstance(value, float):
                result = parse_float(field_name, value, min_val=min_val, max_val=max_val)
            else:
                result = parse_int(field_name, value, min_val=min_val, max_val=max_val)
            print(f"✅ {description}: {result}")
        except ValidationError as e:
            print(f"❌ {description}: {e.message}")


def example_7_flask_route_pattern():
    """Example 7: Flask route integration pattern"""
    print("\n" + "=" * 60)
    print("Example 7: Flask Route Pattern")
    print("=" * 60)

    # Simulated Flask route logic
    simulated_form = {
        'id': 'PROD002',
        'name': 'Fortune Rice',
        'category': 'Grains',
        'stock': '500',
        'price': '450.00',
        'supplier': 'Adani Wilmar',
        'expiry_date': '2027-06-30'
    }

    print("Simulating Flask route with validation:")
    print(f"Form data: {simulated_form}")

    try:
        # Validate (like in app.py)
        validated_item = validate_inventory_item(simulated_form)

        # Sanitize for CSV
        safe_item = {
            key: sanitize_for_csv(value)
            for key, value in validated_item.items()
        }

        print("\n✅ Validation passed!")
        print("   Ready to save to CSV:")
        for key, value in safe_item.items():
            print(f"   {key}: {value}")

        # In real Flask: flash("Product added successfully!", "success")
        print("\n📢 Flash message: 'Product added successfully!' (success)")

    except ValidationError as e:
        print(f"\n❌ Validation failed!")
        print(f"   Error: {e.message}")
        print(f"   Field: {e.field}")
        # In real Flask: flash(e.message, "error")
        print(f"\n📢 Flash message: '{e.message}' (error)")


def main():
    """Run all examples"""
    print("\n")
    print("🛍️" * 30)
    print("   DOKAN VALIDATION FRAMEWORK - EXAMPLES")
    print("🛍️" * 30)
    print("\n")

    example_1_basic_validation()
    example_2_invalid_input()
    example_3_inventory_validation()
    example_4_csv_sanitization()
    example_5_user_registration()
    example_6_range_validation()
    example_7_flask_route_pattern()

    print("\n" + "=" * 60)
    print("Examples completed! See VALIDATION_FRAMEWORK.md for more info.")
    print("=" * 60)
    print("\n")


if __name__ == '__main__':
    main()

