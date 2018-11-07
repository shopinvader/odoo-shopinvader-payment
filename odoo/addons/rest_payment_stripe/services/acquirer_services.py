# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class AcquirerService(AbstractComponent):
    _inherit = "acquirer.service"

    # add the stripe_publishable_key to the acquirer.service
    def _json_acquirer(self, acquirer):
        res = super()._json_acquirer(acquirer)
        res.update({"stripe_key": acquirer.stripe_publishable_key})
        return res

    def _validator_return_search(self):
        res = super()._validator_return_search()
        res.update({"stripe_key": {"type": "string"}})
        return res
