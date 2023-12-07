# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class GiftCard(models.Model):
    _inherit = "gift.card"

    @api.depends("start_date", "end_date", "available_amount", "duration")
    def _compute_state(self):
        for card in self:
            if card.state == "soldout" and card.available_amount > 0:
                card.state = "active"
        return super()._compute_state()
