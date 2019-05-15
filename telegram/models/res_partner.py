from odoo import models, fields


class PartnerTelegram(models.Model):
    _inherit = 'res.partner'

    telegram_id = fields.Integer('Telegram id')
    telegram_fullname = fields.Char('Telegram fullname', help="User's fullname in telegram")
    telegram_phone = fields.Char('Telegram phone')
