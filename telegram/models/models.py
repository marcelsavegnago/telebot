# -*- coding: utf-8 -*-
import logging
import base64
from html import escape

from telegram import Bot
from telegram.error import NetworkError, Unauthorized

from odoo import models

TOKEN = "794841002:AAEBqYS5DuUnoGtkTqBp-EJ90jXANGWM7mI"  # todo: set parameter in System Parameters
_logger = logging.getLogger(__name__)

BOT = Bot(token=TOKEN)

try:
    UPDATE_ID = BOT.get_updates()[0].update_id
except IndexError:
    UPDATE_ID = None


class Telegram(models.Model):
    _name = 'telegram.bot'

    # todo: rename function
    def cron_update_data(self):
        global UPDATE_ID
        _logger.critical('Cron Working...')
        try:
            self.discuss_adapter(BOT)
        except NetworkError:
            # todo: add logger message
            pass
        except Unauthorized:
            # The user has removed or blocked the bot.
            UPDATE_ID += 1
        return True

    def _get_or_create_partner(self, telegram_partner):
        partner = self.env['res.partner'].sudo().search([('telegram_id', '=', telegram_partner.id)],
                                                        limit=1)
        if not partner:
            partner = self.env['res.partner'].sudo().create({
                'name': telegram_partner.full_name,
                'telegram_fullname': telegram_partner.full_name,
                'telegram_id': telegram_partner.id,
            })
        _logger.critical('partner is got, %s' % partner)
        return partner

    def _get_or_create_channel(self, telegram_chat_id, partner):
        _logger.critical('Getting or create channel...')
        channel = self.env['mail.channel'].sudo().search([('telegram_chat_id', '=', telegram_chat_id)],
                                                         limit=1)
        if not channel:
            _logger.critical("creating new channel")
            channel = self.env['mail.channel'].sudo().create({
                'name': 'Telegram with %s' % partner.telegram_fullname,
                'channel_partner_ids': [(4, partner.id, None)],
                'telegram_chat_id': telegram_chat_id,
                'public': 'public',
            })
        _logger.critical('channel is got, %s' % channel)
        return channel

    def discuss_adapter(self, bot):
        global UPDATE_ID
        for update in bot.get_updates(offset=UPDATE_ID, timeout=10):
            UPDATE_ID = update.update_id + 1

            telegram_message = update.message
            partner = self._get_or_create_partner(telegram_message.from_user)
            channel = self._get_or_create_channel(telegram_message.chat_id, partner)
            # create new odoo_message, link to partner (many2one author_id) and channel(many2many channel_ids)
            if telegram_message:  # your bot can receive updates without messages
                _logger.critical("odoo_message document %s" % telegram_message.document)
                odoo_message = {
                    'telegram_id': telegram_message.message_id,
                    'author_id': partner.id,
                    'channel_ids': [(4, channel.id, None)],
                }
                for strategy in (self.message_strategy, self.document_strategy,
                                 self.photo_strategy, self.video_strategy,
                                 self.audio_strategy, self.voice_strategy,):
                    odoo_message = strategy(odoo_message=odoo_message, telegram_message=telegram_message)

                self.create_or_update_contact(telegram_message=telegram_message)

                _logger.critical("Creating new odoo_message %s" % odoo_message)
                self.env['mail.message'].sudo().create(odoo_message)

    def message_strategy(self, odoo_message, telegram_message):
        if telegram_message.text:
            odoo_message['body'] = escape(telegram_message.text)
        return odoo_message

    def document_strategy(self, odoo_message, telegram_message):
        document = telegram_message.document
        if document is not None:
            _logger.critical('Creating attachment')
            attachment = self.env['ir.attachment'].sudo().create({
                'name': document.file_name,
                'datas_fname': document.file_name,
                'datas': base64.b64encode(document.get_file().download_as_bytearray()),
                'mimetype': document.mime_type,
                'file_size': document.file_size,
            })
            odoo_message['attachment_ids'] = [(4, attachment.id, None), ]
        return odoo_message

    def photo_strategy(self, odoo_message, telegram_message):
        if telegram_message.photo:
            photo = telegram_message.photo[-1]  # get the highest resolution
            attachment = self.env['ir.attachment'].sudo().create({
                'name': photo.file_id,
                'datas_fname': photo.get_file()['file_path'].split('/')[-1],
                'datas': base64.b64encode(photo.get_file().download_as_bytearray()),
                'file_size': photo.file_size,
            })
            odoo_message['attachment_ids'] = [(4, attachment.id, None), ]
        return odoo_message

    def video_strategy(self, odoo_message, telegram_message):
        if telegram_message.video:
            video = telegram_message.video
            attachment = self.env['ir.attachment'].sudo().create({
                'name': video.file_id,
                'datas_fname': video.get_file()['file_path'].split('/')[-1],
                'datas': base64.b64encode(video.get_file().download_as_bytearray()),
                'mimetype': video.mime_type,
                'file_size': video.file_size,
            })
            odoo_message['attachment_ids'] = [(4, attachment.id, None),]
        return odoo_message

    def audio_strategy(self, odoo_message, telegram_message):
        if telegram_message.audio:
            audio = telegram_message.audio
            attachment = self.env['ir.attachment'].sudo().create({
                'name': audio.file_id,
                'datas_fname': audio.get_file()['file_path'].split('/')[-1],
                'datas': base64.b64encode(audio.get_file().download_as_bytearray()),
                'mimetype': audio.mime_type,
                'file_size': audio.file_size,
            })
            odoo_message['attachment_ids'] = [(4, attachment.id, None), ]
        return odoo_message

    def voice_strategy(self, odoo_message, telegram_message):
        if telegram_message.voice:
            voice = telegram_message.voice
            attachment = self.env['ir.attachment'].sudo().create({
                'name': voice.file_id,
                'datas_fname': voice.get_file()['file_path'].split('/')[-1],
                'datas': base64.b64encode(voice.get_file().download_as_bytearray()),
                'mimetype': voice.mime_type,
                'file_size': voice.file_size,
            })
            odoo_message['attachment_ids'] = [(4, attachment.id, None), ]
        return odoo_message

    def create_or_update_contact(self, telegram_message):
        contact = telegram_message.contact
        if contact:
            contact.full_name = "%s %s" % (contact.first_name, contact.last_name)
            contact.id = contact.user_id
            partner = self._get_or_create_partner(telegram_partner=contact)
            partner.write({'telegram_phone': contact.phone_number})
            return partner
