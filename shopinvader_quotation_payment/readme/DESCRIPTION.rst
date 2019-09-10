This module add the support of payment for quotation for shopinvader.

Estimated quotation can be paid with all payment mode configured on shopinvader backend.

Cart that contains a product that requires a quotation can not be paid anymore (no payment mode available). The method `request_quotation` must be called on the cart service to convert the cart into a quotation.
