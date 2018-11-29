# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import _
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import MissingError
from odoo.addons.base_rest.components.service import skip_secure_params, \
    skip_secure_response

_logger = logging.getLogger(__name__)


# pylint want to merge this component with "acquirer.service", and when
# the pylint error is disabled, a useless-suppression of the error is raised.
# pylint: disable=consider-merging-classes-inherited,useless-suppression
class WebhookService(AbstractComponent):
    _inherit = 'base.rest.service'
    _name = 'webhook.service'
    _description = """
            Webhook for stripe
        """

    # In a component, not a model (super().create not existent)
    # pylint: disable=method-required-super
    # the params is a huge json
    @skip_secure_params
    # stripe wait only the HTTP 200 code status (no json response)
    @skip_secure_response
    def create(self, **payload):
        """
        Handle stripe webhook
        :param payload: stripe event value
        :return: nothing (stripe wait for HTTP 200)
        """
        source = payload['data']['object']['metadata'].get('reference')
        if not source:
            _logger.info(
                'Webhook of type %s without reference: ignored',
                payload['type'])
            return
        transaction = self.env['payment.transaction'].search([
            ('reference', '=', source),
        ])

        if transaction:
            transaction._stripe_process_webhook(payload)
        if not transaction:
            raise MissingError(_("Unknown transaction"))

    def _validator_create(self):
        # needed for swagger
        return {
        }

    def _validator_return_create(self):
        # needed for swagger
        return {
        }
