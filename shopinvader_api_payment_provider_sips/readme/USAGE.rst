**Specific procedure for Sips**

First call the POST `/payment/transactions` as described in the core addon `shopinvader_api_payment`.
This method will return a `TransactionProcessingValues` schema in which you will find a `redirect_form_html` HTML form.
This HTML form must just be submitted by the front to call the Sips services.
After Sips has finished, the frontend redirect url will be called back.
