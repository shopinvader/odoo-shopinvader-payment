# Copyright 2019 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.http import route

from odoo.addons.shopinvader.controllers import main

_logger = logging.getLogger(__name__)


class InvaderController(main.InvaderController):
    @route(["/shopinvader/payment_paypal/normal_return"], methods=["GET"])
    def normal_return(self, **params):
        return self._process_method(
            "payment_paypal", "normal_return", params=params
        )
