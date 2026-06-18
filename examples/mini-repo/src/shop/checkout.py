class PaymentTimeout(Exception):
    pass


class RetryableCheckoutError(Exception):
    pass


def checkout(cart, gateway):
    try:
        gateway.charge(cart.total)
    except PaymentTimeout as exc:
        cart.mark_failed("payment timeout")
        raise RetryableCheckoutError("payment timeout, retry checkout") from exc
    cart.mark_paid()
    return {"status": "paid"}
