# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    @api.model
    def _get_default_acquirer(self):
        raise NotImplementedError()
