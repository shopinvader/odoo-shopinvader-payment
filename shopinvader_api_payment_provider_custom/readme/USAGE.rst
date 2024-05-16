**Specific procedure for Custom payments**

This addon manages custom payments (such as wire transfers).

First call the POST `/payment/transactions` as described in the core addon `shopinvader_api_payment`.
This method will return a `TransactionProcessingValues` schema in which you will find a `redirect_form_html` HTML form.
This HTML form must just be submitted by the front. It will call the POST route `payment/providers/custom/pending` that will send the transaction into pending (compared to other providers, a transaction paid with a custom payment mode is not automatically validated).
This route will then redirect to the `frontend_redirect_url` giving the pending message defined on the provider.
