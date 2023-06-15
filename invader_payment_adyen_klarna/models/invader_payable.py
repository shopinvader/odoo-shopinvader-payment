# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class InvaderPayable(models.AbstractModel):

    _inherit = "invader.payable"

    def _klarna_shopper_info(self, shopper):
        lang = shopper.lang or self.env.lang or "en_US"
        values = {
            "shopperLocale": lang,
            "shopperName": {
                "firstName": shopper.display_name or "",
            },
        }
        if shopper.phone:
            values.update({"telephoneNumber": shopper.phone})
        if shopper.email:
            values.update({"shopperEmail": shopper.email})
        return values

    def _klarna_partner_info(self, partner):
        """
        All of these keys are required for Adyen Klarna.
        It's not the goal of Odoo to do the check.
        And if Adyen change some requirements, we don't have
        to do an update of this module.
        """
        values = {
            "city": partner.city or "",
            "country": partner.country_id.code or "",
            "houseNumberOrName": "",
            "postalCode": partner.zip or "",
            "street": partner.street or "",
        }
        return values

    def _get_klarna_shopper(self):
        """
        Get the shopper of the payable (res.partner) for Klarna
        """
        raise NotImplementedError()

    def _get_klarna_billing(self):
        """
        Get the billing address of the payable (res.partner) for Klarna
        """
        raise NotImplementedError()

    def _get_klarna_delivery(self):
        """
        Get the delivery address of the payable (res.partner) for Klarna
        """
        raise NotImplementedError()

    def _get_klarna_internal_ref(self):
        """
        Get the delivery address of the payable (res.partner) for Klarna
        """
        raise NotImplementedError()

    def _prepare_adyen_payment_klarna(self, transaction, payment_method):
        values = self._klarna_shopper_info(self._get_klarna_shopper())
        values.update(
            {
                "shopperReference": self._get_klarna_internal_ref(),
                "billingAddress": self._klarna_partner_info(
                    self._get_klarna_billing()
                ),
                "deliveryAddress": self._klarna_partner_info(
                    self._get_klarna_delivery()
                ),
                "lineItems": [
                    self._prepare_adyen_payment_klarna_line(
                        transaction, payment_method, line
                    )
                    for line in self._get_payable_lines()
                ],
            }
        )
        return values

    def _prepare_adyen_payment_klarna_line(
        self, transaction, payment_method, line
    ):
        values = {
            "id": line.id,
            "description": line.display_name,
        }
        return values
