This addon is the core of the new Shopinvader API Payment addons suite.
It defines basic services, which will be extended in two axes.

* The first axe concerns the payable object. Here the methods should work with any abstract payable object (sale order, account invoice, ...) but specific logic must be implemented in related addons (see `shopinvader_api_payment_cart` to pay sale orders for eg.)
* The second axe concerns the payment provider. The idea is to develop one addon for each payment provider. Some of them are already available, see `shopinvader_api_payment_sips`, `shopinvader_api_payment_stripe`, `shopinvader_api_payment_custom`. In these addons we add the necessary logic to redirect to the payment provider payment website, the return url ...

All payment routes are public. We must thus encode all sensitive info.
The `Payable` object achieves this. In each service we ensure that the payable
wasn't tampered.

**Concrete Usage**

The idea to use this suite of addons is the following. Assume you have a valid
payable (see addons of the first axe on how to get them, for eg. `shopinvader_api_payment_cart`
on how to get the payable of the current cart).

1. Get all providers that are allowed to pay your payable object.
You just need to call the GET route `/payment/methods` with your payable for this.

2. Once you chose the payment method you want to use, create the payment transaction
calling the POST route `/payment/transactions` with your payable + some
additional input info (the chosen provider, the frontend redirect url...).
See the associated `TransactionCreate` Pydantic schema.

3. The following (and last) step depends on the chosen provider. See more info
into the dedicated Shopinvader API payment addon.
However, the idea is often the same: a `redirect_form_html` is returned and
you should submit this HTML form to call the provider services.
