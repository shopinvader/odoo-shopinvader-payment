# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent


class AcquirerService(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "acquirer.service"
    _description = """
            acquirer Services
        """

    def search(self, acquirer_id=False):
        """
        Search after a acquirer by id or return a default one
        :param acquirer_id: the id of the acquirer (non mandatory)
        :return: a jsonify acquirer
        """
        if acquirer_id:
            acquirer = self.env["payment.acquirer"].browse(acquirer_id)
        else:
            acquirer = self._get_default_acquirer()
        return self._json_acquirer(acquirer)

    def _json_acquirer(self, acquirer):
        return {"name": acquirer.name}

    def _validator_search(self):
        return {"acquirer_id": {"type": "integer", "coerce": int}}

    def _validator_return_search(self):
        return {"name": {"type": "string"}}

    def _get_default_acquirer(self):
        return self.env["payment.acquirer"]._get_default_acquirer()
