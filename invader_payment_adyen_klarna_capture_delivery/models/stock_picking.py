# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        """
        Inherit to automatically execute the klarna capture when the picking is validated
        """
        result = super().button_validate()
        for picking in self:
            if picking.picking_type_id.code == "outgoing" and picking.sale_id:
                picking.sale_id._trigger_klarna_capture()
        return result
