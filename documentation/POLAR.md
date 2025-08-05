# Polar API Documentation for SOLEil

## Overview
This is a placeholder document for Polar integration. Polar is a creator monetization platform that could be integrated into SOLEil for handling payments, subscriptions, and creator support features.

## Status
**Not Currently Implemented** - This documentation serves as a reference for future integration.

## Potential Use Cases for SOLEil

### 1. Band Monetization
- **Tip Jar**: Allow fans to support bands directly
- **Exclusive Content**: Gate premium charts or recordings
- **Subscription Tiers**: Different access levels for band content

### 2. Session Musician Payments
- **Gig Payments**: Handle payments for session work
- **Revenue Sharing**: Automatic splits between band members
- **Invoice Generation**: Professional invoicing for corporate gigs

### 3. Music Lessons
- **Lesson Bookings**: Schedule and pay for music lessons
- **Course Sales**: Sell instructional content
- **Workshop Registration**: Handle event ticketing

## Basic Integration Steps

### 1. Authentication
```python
# Example Polar client setup
from polar import Polar

polar_client = Polar(
    access_token=os.getenv("POLAR_ACCESS_TOKEN"),
    server_url="https://api.polar.sh"
)
```

### 2. Create Products
```python
# Create a product for band subscriptions
product = await polar_client.products.create(
    name="Band Premium Access",
    description="Get exclusive access to all band content",
    price_amount=999,  # $9.99
    price_currency="USD",
    type="subscription",
    interval="month"
)
```

### 3. Handle Webhooks
```python
@router.post("/webhooks/polar")
async def handle_polar_webhook(
    request: Request,
    signature: str = Header(alias="Polar-Signature")
):
    # Verify webhook signature
    body = await request.body()
    if not verify_webhook_signature(body, signature):
        raise HTTPException(400, "Invalid signature")
    
    # Process webhook event
    event = json.loads(body)
    
    match event["type"]:
        case "subscription.created":
            await handle_new_subscription(event["data"])
        case "subscription.canceled":
            await handle_canceled_subscription(event["data"])
        case "payment.succeeded":
            await handle_successful_payment(event["data"])
```

## Integration Architecture

### Database Models
```python
class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    
    user_id = Column(String, ForeignKey("users.id"))
    polar_subscription_id = Column(String, unique=True)
    product_id = Column(String)
    status = Column(String)  # active, canceled, past_due
    current_period_end = Column(DateTime)
    
class Payment(BaseModel):
    __tablename__ = "payments"
    
    user_id = Column(String, ForeignKey("users.id"))
    polar_payment_id = Column(String, unique=True)
    amount = Column(Integer)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
```

### API Endpoints
```python
# Subscription management
POST   /api/subscriptions/create
GET    /api/subscriptions/status
DELETE /api/subscriptions/cancel

# Payment handling
POST   /api/payments/create-checkout
GET    /api/payments/history
POST   /api/payments/refund

# Creator dashboard
GET    /api/creator/earnings
GET    /api/creator/supporters
POST   /api/creator/withdraw
```

## Security Considerations

1. **Webhook Verification**: Always verify webhook signatures
2. **PCI Compliance**: Never store card details directly
3. **Access Control**: Verify user permissions for paid content
4. **Audit Trail**: Log all payment-related activities

## Testing Integration

### Test Mode
```python
# Use test API keys for development
POLAR_TEST_ACCESS_TOKEN = "test_token_xxx"

# Test webhook events
async def trigger_test_webhook():
    test_event = {
        "type": "subscription.created",
        "data": {
            "id": "sub_test_123",
            "customer_id": "cus_test_456",
            "product_id": "prod_test_789"
        }
    }
    await handle_polar_webhook(test_event)
```

## Future Considerations

### 1. Multi-Currency Support
- Handle different currencies for international bands
- Currency conversion for reporting

### 2. Tax Handling
- VAT/GST calculation
- Tax reporting for creators

### 3. Payout Management
- Automated payouts to band members
- Split payment handling

### 4. Analytics
- Revenue tracking
- Subscriber analytics
- Conversion metrics

## Resources

- [Polar Documentation](https://docs.polar.sh)
- [Polar API Reference](https://api.polar.sh/docs)
- [Polar Python SDK](https://github.com/polarsource/polar-python)
- [Webhook Events](https://docs.polar.sh/webhooks)

## Implementation Checklist

When ready to implement:

- [ ] Create Polar account and get API credentials
- [ ] Set up webhook endpoints
- [ ] Design subscription tiers and products
- [ ] Implement payment flow UI
- [ ] Add subscription status checks to protected routes
- [ ] Create creator dashboard
- [ ] Implement webhook handlers
- [ ] Add payment history tracking
- [ ] Set up automated testing
- [ ] Configure production environment

## Notes

This integration would significantly enhance SOLEil's capability to support professional musicians and bands in monetizing their work. The platform's focus on band collaboration makes it ideal for implementing revenue sharing and band financial management features.