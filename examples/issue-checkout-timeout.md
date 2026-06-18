# Checkout retry fails after payment timeout

When the payment gateway returns a timeout during checkout, the API returns a 500 and the cart is marked as paid.

Expected behavior:

- [ ] A timeout should leave the cart unpaid.
- [ ] The checkout endpoint should return a retryable error.
- [ ] Add a regression test for the timeout path.

Notes:

- This started after the payment retry code was added.
- It may be in the checkout service rather than the HTTP route.
