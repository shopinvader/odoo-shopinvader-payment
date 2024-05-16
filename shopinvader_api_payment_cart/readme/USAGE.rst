**Get the encoded payable info for a cart**

As the routes on the cart router are private, the user needs to be authenticated to retrieve the cart payable info.
Call one of the routes `/current/payable/` or `/{uuid}/payable` to retrieve the payable token that will be needed in all public payment routes of the `shopinvader_api_payment` core addon.


