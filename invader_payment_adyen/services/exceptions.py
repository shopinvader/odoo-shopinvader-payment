# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError


class AdyenInvalidData(UserError):
    def __init__(self, msg):
        msg = " - ".join(["ADYEN Invalid Data", msg])
        super(AdyenInvalidData, self).__init__(msg)
