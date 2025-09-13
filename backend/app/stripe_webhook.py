# backend/app/stripe_webhook.py
import os
from fastapi import APIRouter, Request, HTTPException
import stripe

stripe_api_key = os.environ.get("STRIPE_SECRET_KEY", "")
stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = stripe_api_key

stripe_webhook_router = APIRouter()

@stripe_webhook_router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    """
    Create a Stripe Checkout session for subscription.
    Expects JSON body: { "priceId": "<stripe_price_id>", "customer_email": "<email>" }
    """
    payload = await request.json()
    price_id = payload.get("priceId")
    customer_email = payload.get("customer_email")
    if not price_id or not customer_email:
        raise HTTPException(status_code=400, detail="Missing priceId or customer_email")

    try:
        session = stripe.checkout.Session.create(
            success_url=os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000") + "/?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000") + "/pricing",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=customer_email,
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_webhook_router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_secret)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")
    else:
        # If webhook secret not set, try to parse body
        event = None
        try:
            event = await request.json()
        except:
            raise HTTPException(status_code=400, detail="Invalid payload")

    # Process events: invoice.paid, customer.subscription.created, etc.
    # TODO: store subscription data to your DB
    # Example:
    # if event["type"] == "checkout.session.completed": ...
    return {"status": "success"}
