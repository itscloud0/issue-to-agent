class Cart:
    def __init__(self, total):
        self.total = total
        self.paid = False
        self.failure_reason = None

    def mark_paid(self):
        self.paid = True
        self.failure_reason = None

    def mark_failed(self, reason):
        self.paid = False
        self.failure_reason = reason
