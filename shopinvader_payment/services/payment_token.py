# Copyright 2020 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class PaymentTokenService(Component):
    _inherit = "base.shopinvader.service"
    # This heritage is the reason this class is here and not in invader_payment
    _name = "shopinvader.payment.token.service"
    _usage = "payment_token"
    _expose_model = "payment.token"

    def get(self, _id):
        return self._to_json(self._get(_id))

    def search(self, **params):
        if not self.partner:
            return {"data": []}
        else:
            return self._paginate_search(**params)

    # pylint: disable=W8106
    def create(self, **params):
        token = self.env[self._expose_model].create(
            self._prepare_params(params, mode="create")
        )
        return self._to_json(token)

    def update(self, _id, **params):
        token = self._get(_id)
        token.write(self._prepare_params(params, mode="update"))
        return self._to_json(token)

    def delete(self, _id):
        token = self._get(_id)
        token.active = False
        return {}

    # The following method are 'private' and should be never never NEVER call
    # from the controller.
    # All params are trusted as they have been checked before

    # Validator
    def _validator_search(self):
        return {"scope": {"type": "dict", "nullable": True}}

    def _validator_create(self):
        res = {
            "name": {"type": "string", "required": True},
            "acquirer_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "acquirer_ref": {"type": "string", "required": True},
        }
        return res

    def _validator_update(self):
        res = self._validator_create()
        for key in res:
            if "required" in res[key]:
                del res[key]["required"]
        return res

    def _validator_delete(self):
        return {}

    def _get_base_search_domain(self):
        return [("partner_id", "=", self.partner.id)]

    def _json_parser(self):
        res = [
            "id",
            "name",
            "acquirer_ref",
            ("acquirer_id:acquirer", ["id", "name"]),
            ("partner_id:partner", ["id", "name"]),
        ]
        return res

    def _to_json(self, token):
        return token.jsonify(self._json_parser())

    def _prepare_params(self, params, mode="create"):
        if mode == "create":
            params["partner_id"] = self.partner.id
        return params
