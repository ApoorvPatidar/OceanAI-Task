# E-Commerce Product Specifications

## Product Overview
This document outlines the specifications for our e-commerce checkout system.

## Discount Code Feature

### Valid Discount Codes

1. **SAVE10**
   - Type: Percentage Discount
   - Value: 10% off subtotal
   - Applicable to: All products
   - Restrictions: Cannot be combined with other offers
   - Expiration: None

2. **SAVE20**
   - Type: Percentage Discount
   - Value: 20% off subtotal
   - Applicable to: All products
   - Restrictions: Cannot be combined with other offers
   - Expiration: None

3. **FREESHIP**
   - Type: Free Shipping
   - Value: Waives shipping fee ($9.99)
   - Applicable to: All orders
   - Restrictions: Cannot be combined with other offers
   - Expiration: None

### Discount Code Validation Rules

- Discount codes are case-insensitive
- Only one discount code can be applied per order
- Invalid codes display error message: "Invalid discount code"
- Valid codes display success message: "Discount applied successfully!"
- Discount is applied to subtotal before shipping

## Checkout Form Fields

### Required Fields
- Email address (must be valid email format)
- First Name
- Last Name
- Street Address
- City
- State
- ZIP Code

### Optional Fields
- Phone Number
- Apartment/Suite number (address line 2)
- Discount Code

## Payment Methods

Supported payment methods:
1. Credit Card (default)
2. PayPal
3. Bank Transfer

## Order Pricing

### Default Pricing
- Subtotal: $99.99
- Shipping: $9.99
- Total (before discount): $109.98

### Discount Calculation
- Percentage discounts apply to subtotal only
- Free shipping removes shipping fee
- Final total = Subtotal - Discount + Shipping

## Form Validation

### Email Validation
- Must contain @ symbol
- Must have domain extension
- Error message: "Please enter a valid email"

### Required Field Validation
- All required fields must be filled
- Empty required fields prevent form submission
- Required fields marked with red asterisk (*)

## State Selection

Available states:
- California (CA)
- New York (NY)
- Texas (TX)
- Florida (FL)

## Order Completion

### Success Behavior
- Order ID generated in format: ORD-XXXXXXXXX
- Success message displays with order ID
- "Place Order" button changes to "Order Placed"
- Form becomes disabled after successful submission

## UI/UX Features

- Real-time discount code validation
- Dynamic total calculation
- Visual feedback for payment method selection
- Responsive form layout
- Error/success message display
