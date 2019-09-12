# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase
from odoo.addons.shopinvader import shopinvader_response


class TestCommonPayment(TransactionComponentCase):
    def setUp(self):
        super(TestCommonPayment, self).setUp()
        shopinvader_response.set_testmode(True)

        @self.addCleanup
        def cleanupShopinvaderResponseTestMode():
            shopinvader_response.set_testmode(False)

        self.shopinvader_response = shopinvader_response.get()

    def _get_service(self, usage):
        collection = _PseudoCollection("res.partner", self.env)
        work = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        return work.component(usage=usage)
