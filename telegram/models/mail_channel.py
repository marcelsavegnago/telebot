from odoo import models, fields

class ChannelPartnerTelegram(models.Model):
    _inherit = 'mail.channel'

    telegram_chat_id = fields.Integer('Telegram id')