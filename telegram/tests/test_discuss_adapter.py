from odoo.tests.common import TransactionCase

class TestTelegram(TransactionCase):

    def test_succes(self):
        self.assertEqual(1, 1)

    def test_failed(self):
        self.assertEqual(1, 2)