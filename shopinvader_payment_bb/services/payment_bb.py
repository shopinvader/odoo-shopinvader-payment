#  Copyright 2023 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServiceBbShopinvader(Component):
    """Expose Bacnk of Brazil payment service under /shopinvader endpoint"""

    _name = "payment.service.bb.shopinvader"
    _inherit = ["payment.service.bb", "base.shopinvader.service"]
    _usage = "payment_bacen_pix"
    _collection = "shopinvader.backend"
