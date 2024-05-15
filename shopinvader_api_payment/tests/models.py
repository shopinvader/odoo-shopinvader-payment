# Copyright 2024 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class PayableTestModel(models.Model):
    _name = "payable.test.model"
    _description = "Fake model defining a payable"

    name = fields.Char()
    amount = fields.Float()
    partner_id = fields.Many2one("res.partner")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.user.company_id.currency_id
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
