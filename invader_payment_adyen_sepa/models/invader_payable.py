# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class InvaderPayable(models.AbstractModel):
    _inherit = "invader.payable"
