import unittest

from shop.cart import Cart
from shop.checkout import PaymentTimeout, RetryableCheckoutError, checkout


class TimeoutGateway:
    def charge(self, total):
        raise PaymentTimeout("gateway timed out")


class CheckoutTests(unittest.TestCase):
    def test_timeout_leaves_cart_unpaid(self):
        cart = Cart(total=42)

        with self.assertRaises(RetryableCheckoutError):
            checkout(cart, TimeoutGateway())

        self.assertFalse(cart.paid)
        self.assertEqual(cart.failure_reason, "payment timeout")


if __name__ == "__main__":
    unittest.main()
