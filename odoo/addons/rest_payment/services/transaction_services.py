# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent


# pylint want to merge this component with "acquirer.service", and when
# the pylint error is disabled, a useless-suppression of the error is raised.
# pylint: disable=consider-merging-classes-inherited,useless-suppression
class TransactionService(AbstractComponent):
    _inherit = 'base.rest.service'
    _name = 'transaction.service'
    _description = """
            transaction Services
        """

    def _get_default_acquirer(self):
        return self.env["payment.acquirer"]._get_default_acquirer()

    def _get_transaction_values(self, acquirer, **post):
        # minimum overload: 'amount', 'currency_id', 'partner_id', 'reference'
        return {
            'acquirer_id': acquirer.id,
            'type': 'form',
        }

    def _json_transaction(self, transaction):
        return {
            "id": transaction.id,
            "state": transaction.state,
        }

    # In a component, not a model (super().create not existent)
    # pylint: disable=method-required-super
    def create(self, acquirer_id=False, **post):
        """
        create a transaction based on the parameters.
        :param acquirer_id: acquirer to used to create the transaction
        :param post: value to create the transaction
        :return: a payment.transaction jsonify
        """
        if acquirer_id:
            acquirer = self.env["payment.acquirer"].browse(acquirer_id)
        else:
            acquirer = self._get_default_acquirer()

        tx_values = self._get_transaction_values(acquirer, **post)

        tx = self.env["payment.transaction"].create(tx_values)
        return self._json_transaction(tx)

    def _validator_create(self):
        return {
            "acquirer_id": {
                "type": "integer",
            }
        }

    def _validator_return_create(self):
        return {
            "id": {
                'type': 'integer',
            },
            "state": {
                'type': 'string',
            },
        }

    def get(self, _id):
        """
        Get a payment.transaction by id
        :param _id: id of the payment.transaction
        :return:
        """
        pt = self.env["payment.transaction"]
        return self._json_transaction(pt.browse(int(_id)))

    def _validator_get(self):
        return {
            "_id": {
                "coerce": int,
                "type": "integer",
            },
        }

    def _validator_return_get(self):
        return {
            "id": {
                'type': 'integer',
            },
            "state": {
                'type': 'string',
            },
        }
