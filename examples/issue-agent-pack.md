# Issue Agent Pack

**Issue:** Checkout retry fails after payment timeout

## Ready-To-Paste Agent Prompt

```text
Work as a pragmatic senior engineer in this repo.

Issue: Checkout retry fails after payment timeout

Likely relevant files:
- tests/test_checkout.py (score 39): path matches: checkout, test; content mentions: cart, checkout, gateway, paid, payment, test, timeout, unpaid; test file may need a regression case
- src/shop/checkout.py (score 29): path matches: checkout; content mentions: cart, checkout, gateway, paid, payment, retry, timeout
- src/shop/cart.py (score 19): path matches: cart; content mentions: cart, paid
- AGENTS.md (score 3): content mentions: behavior, checkout, payment
- .github/workflows/ci.yml (score 2): content mentions: checkout, test

Suggested commands:
- `python -m pip install .`
- `python -m unittest discover -s tests`

Acceptance criteria:
- A timeout should leave the cart unpaid.
- The checkout endpoint should return a retryable error.
- Add a regression test for the timeout path.

Risks:
- Sensitive area mentioned: payment. Avoid broad auth, billing, migration, or secret-handling changes.

Repo instructions to honor:
- AGENTS.md: # Agent Instructions

- Keep checkout changes small.
- Add tests before changing payment behavior.
- Do not touch billing migrations in the first pass.

Keep the change minimal. Do not rewrite unrelated code. Verify before final response.
```

## Relevant Files

### `tests/test_checkout.py`
- Score: 39
- path matches: checkout, test
- content mentions: cart, checkout, gateway, paid, payment, test, timeout, unpaid
- test file may need a regression case

```text
L3: from shop.cart import Cart
L4: from shop.checkout import PaymentTimeout, RetryableCheckoutError, checkout
L9: raise PaymentTimeout("gateway timed out")
```

### `src/shop/checkout.py`
- Score: 29
- path matches: checkout
- content mentions: cart, checkout, gateway, paid, payment, retry, timeout

```text
L9: def checkout(cart, gateway):
L11: gateway.charge(cart.total)
L13: cart.mark_failed("payment timeout")
```

### `src/shop/cart.py`
- Score: 19
- path matches: cart
- content mentions: cart, paid

```text
L1: class Cart:
L4: self.paid = False
L7: def mark_paid(self):
```

### `AGENTS.md`
- Score: 3
- content mentions: behavior, checkout, payment

```text
L3: - Keep checkout changes small.
L4: - Add tests before changing payment behavior.
```

### `.github/workflows/ci.yml`
- Score: 2
- content mentions: checkout, test

```text
L8: test:
L11: - uses: actions/checkout@v5
```

## Suggested Commands

- `python -m pip install .`
- `python -m unittest discover -s tests`

## Acceptance Criteria

- A timeout should leave the cart unpaid.
- The checkout endpoint should return a retryable error.
- Add a regression test for the timeout path.

## Risks

- Sensitive area mentioned: payment. Avoid broad auth, billing, migration, or secret-handling changes.

## Repo Instructions

### `AGENTS.md`

```text
# Agent Instructions

- Keep checkout changes small.
- Add tests before changing payment behavior.
- Do not touch billing migrations in the first pass.
```
