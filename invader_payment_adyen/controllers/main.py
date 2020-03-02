# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.shopinvader.controllers.main import InvaderController
from odoo.http import route

_logger = logging.getLogger(__name__)


class InvaderAdyenController(InvaderController):
    @route(["/shopinvader/payment_adyen/paymentResult"], methods=["GET"])
    def adyen_payment_result(self, **params):
        return self._process_method(
            "payment_adyen", "paymentResult", params=params
        )
