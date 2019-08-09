# -*- coding: utf-8 -*-

# BACKPORT FROM 12.0 TO BE REMOVED!!!!!!!

import re
import time

from openerp import api, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _compute_reference(self, values=None, prefix=None):
        res = super(PaymentTransaction, self)._compute_reference(
            values=values, prefix=prefix
        )
        acquirer = self.env["payment.acquirer"].browse(
            values.get("acquirer_id")
        )
        if acquirer and acquirer.provider == "sips":
            return (
                re.sub(r"[^0-9a-zA-Z]+", "x", res)
                + "x"
                + str(int(time.time()))
            )
        return res
