# -*- coding: utf-8 -*-

# BACKPORT FROM 12.0 TO BE REMOVED!!!!!!!

from openerp import fields, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    sips_version = fields.Char(
        "Interface Version",
        required_if_provider="sips",
        groups="base.group_no_one",
        default="HP_2.3",
    )
