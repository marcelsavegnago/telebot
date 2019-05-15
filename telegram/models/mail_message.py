import base64
import logging
import re
from io import BytesIO
from html import unescape

from odoo import models, fields, api
from telegram.error import BadRequest
from transliterate import translit

from .models import BOT

_logger = logging.getLogger(__name__)


class MessageTelegram(models.Model):
    _inherit = 'mail.message'

    telegram_id = fields.Integer('Telegram id', default=0)

    # ToDo: learn how to send document file with send_document
    @api.multi
    def create(self, vals):
        _logger.critical("Creating new message with vals: %s" % vals)
        message = super(MessageTelegram, self).create(vals)
        _logger.critical("MessageL %s" % message.channel_ids)
        # telegram_chat = self.env['mail.channel'].sudo().search([('id', '=', message.channel_ids.id)], limit=1) # for odoo 11
        telegram_chat = self.env['mail.channel'].sudo().search([('id', '=', message.res_id)], limit=1) # for odoo 12
        if telegram_chat.telegram_chat_id and message.telegram_id == 0:  # new message in telegram chat and created in odoo
            _logger.critical("New Message %s" % message)
            if message.body:
                BOT.send_message(chat_id=telegram_chat.telegram_chat_id,
                                 text=unescape(re.sub('<.*?>', '', message.body)))
            if message.attachment_ids:
                _logger.critical("Document send to telegram %s" % message.attachment_ids)

                for attachment in message.attachment_ids:
                    b = BytesIO()
                    b.write(base64.b64decode(attachment.datas))
                    b.seek(0)
                    # fixme: cyrillic filename sends incorrect, refactored
                    try:
                        BOT.send_document(chat_id=telegram_chat.telegram_chat_id,
                                          document=b,
                                          filename=attachment.datas_fname)
                    except BadRequest as error:
                        _logger.error(error)
                        b = BytesIO()
                        b.write(base64.b64decode(attachment.datas))
                        b.seek(0)
                        BOT.send_document(chat_id=telegram_chat.telegram_chat_id,
                                          document=b,
                                          filename=translit(attachment.datas_fname, reversed=True))
        return message
