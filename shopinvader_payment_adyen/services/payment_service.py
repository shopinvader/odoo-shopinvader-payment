# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServiceAdyen(Component):
    _inherit = "payment.service.adyen"

    def _validator_add_payment(self):
        return {
            "token": {"type": "string"},
            "redirect_success_url": {"type": "string"},
            "redirect_cancel_url": {"type": "string"},
            "accept_header": {"type": "string"},
            "user_agent": {"type": "string"},
            "shopper_ip": {"type": "string"},
        }

    def _validator_check_payment(self):
        return {
            "md": {"type": "string"},
            "pares": {"type": "string"},
            "accept_header": {"type": "string"},
            "user_agent": {"type": "string"},
            "shopper_ip": {"type": "string"},
        }

    def _execute_payment_action(
        self, provider_name, transaction, target, params
    ):
        """

        :param provider_name: str
        :param transaction: transaction recordset
        :param target: recordset
        :param params: dict
        :return: dict
        """
        if provider_name == "adyen" and transaction.url:
            res = {
                "data": {
                    "payment": {
                        "adyen_params": {
                            "MD": transaction.meta["MD"],
                            "PaReq": transaction.meta["paRequest"],
                            "TermUrl": params["return_url"],
                            "IssuerUrl": transaction.url,
                        }
                    }
                }
            }
            return res
        return super(PaymentServiceAdyen, self)._execute_payment_action(
            provider_name, transaction, target, params
        )

    def _add_params_from_header(self, params):
        """

        :param params: dict
        :return:
        """
        params.update(
            {
                "accept_header": self.client_header["ACCEPT"],
                "user_agent": self.client_header["USER_AGENT"],
                "shopper_ip": self.client_header["IP"],
            }
        )

    def _process_payment_provider(self, provider_name, target, params):
        """

        :param provider_name: str
        :param target: recordset
        :param params: dict
        :return:
        """
        if provider_name == "adyen":
            self._add_params_from_header(params)
        return super(PaymentServiceAdyen, self)._process_payment_provider(
            provider_name, target, params
        )

    def check_payment(self, provider_name=None, **params):
        """

        :param provider_name: str
        :param params: dict
        :return:
        """
        if provider_name == "adyen":
            self._add_params_from_header(params)
            params.update(
                {
                    "md": params.pop("MD", None),
                    "pares": params.pop("PaRes", None),
                }
            )
        return super(PaymentServiceAdyen, self).check_payment(
            provider_name=provider_name, **params
        )
