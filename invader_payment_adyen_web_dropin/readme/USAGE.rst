This has been developed following `Adyen Web Drop-in documentation <https://docs.adyen.com/online-payments/build-your-integration/?platform=Web&integration=Drop-in&tab=python_6>`_.


Two services are exposed to manage payments with Adyen.

Here are the services (that can be explored and tested with Swagger):

* payments

    * This will initiate the payment session itself.

    * This takes as parameters:

        * target: (eg.: "current_cart")
        * The payable ID (invoice, SO,...)

    * Then a json is built internally to create a transaction (Odoo record) and send information to Adyen.

        .. code:: python

            def test_sessions_success(self):
                ady = Adyen.Adyen()
                client = ady.client
                client.xapikey = config.xapikey
                client.platform = "test"
                # Data build by the transaction
                request = {...}
                result = ady.checkout.sessions(request)
        ..

* webhook (also used as returnUrl after the payment)

    * This is used to update a transaction (Odoo record)

    * This takes as parameters:

        * transaction_id
        * data

    * Example of webhook json :

      .. code:: python

          {
            "live": "false",
            "notificationItems":[
              {
                "NotificationRequestItem":{
                  "eventCode":"AUTHORISATION",
                  "merchantAccountCode":"YOUR_MERCHANT_ACCOUNT",
                  "reason":"033899:1111:03/2030",
                  "amount":{
                    "currency":"EUR",
                    "value":2500
                  },
                  "operations":["CANCEL","CAPTURE","REFUND"],
                  "success":"true",
                  "paymentMethod":"mc",
                  "additionalData":{
                    "expiryDate":"03/2030",
                    "authCode":"033899",
                    "cardBin":"411111",
                    "cardSummary":"1111",
                    "checkoutSessionId":"xxx"
                  },
                  "merchantReference":"YOUR_REFERENCE",
                  "pspReference":"xxx",
                  "eventDate":"2021-09-13T14:10:22+02:00"
                }
              }
            ]
          }
      ..
