# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class ShopinvaderPayable(models.AbstractModel):

    _name = "shopinvader.payable"
    _description = "Interface for payable objects (SO, inv, ...)"

    def _get_transaction_to_capture_amount(self):
        """

        :return:
        """
        raise NotImplementedError

    def _get_target_provider(self, target):
        """

        :param target: payment recordset
        :return: str
        """
        raise NotImplementedError

    def _prepare_payment_transaction_data(self, payment_mode):
        """
        Implement this to fill in payment.transaction object data
        :return: dict
        """
        raise NotImplementedError

    def _attach_transaction(self, payment_mode, payment_transaction):
        """
        Implement this method to attach transaction to payable object
        :param payment_mode:
        :param payment_transaction:
        :return: bool
        """
        raise NotImplementedError

    def _get_shopinvader_payment_info(self):
        """

        :param target: target recordset
        :return: dict
        """
        self.ensure_one()
        methods = self._get_shopinvader_available_payment_mode()
        selected_method = self._get_shopinvader_selected_method(methods)
        values = {
            "available_methods": {"count": len(methods), "items": methods},
            "selected_method": selected_method,
            "amount": self._get_transaction_to_capture_amount(),
        }
        return values

    def _get_shopinvader_available_payment_mode(self):
        """

        :param target:
        :return:
        """
        self.ensure_one()
        methods = []
        for method in self.shopinvader_backend_id.payment_method_ids:
            methods.append(self._prepare_shopinvader_payment(method))
        return methods

    def _prepare_shopinvader_payment(self, method):
        """

        :param method:
        :return: dict
        """
        return {
            "id": method.payment_mode_id.id,
            "name": method.payment_mode_id.name,
            "provider": method.payment_mode_id.provider,
            "code": method.code,
            "description": method.description,
        }

    def _get_shopinvader_selected_method(self, methods):
        """

        :param methods: list of dict
        :param target:
        :return: dict
        """
        self.ensure_one()
        selected_method = {}
        if self.payment_mode_id:
            for method in methods:
                if method.get("id") == self.payment_mode_id.id:
                    selected_method = method
        return selected_method

    def _get_shopinvader_payment_mode(self, payment_mode):
        """

        :param target: payment recordset
        :param params: dict
        :return: str
        """
        payment_mode_obj = self.env["account.payment.mode"]
        payment_mode_id = payment_mode_obj.browse(int(payment_mode))
        available_payment_mode_ids = [
            p.get("id") for p in self._get_shopinvader_available_payment_mode()
        ]
        if payment_mode_id.id not in available_payment_mode_ids:
            raise UserError(_("Unsupported payment mode"))

        return {
            "payment_mode_id": payment_mode_id.id,
            "acquirer_id": payment_mode_id.payment_acquirer_id.id,
        }
