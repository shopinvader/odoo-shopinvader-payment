

# Shopinvader payment modules
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/shopinvader/odoo-shopinvader-payment/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/shopinvader/odoo-shopinvader-payment/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/shopinvader/odoo-shopinvader-payment/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/shopinvader/odoo-shopinvader-payment/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/shopinvader/odoo-shopinvader-payment/branch/18.0/graph/badge.svg)](https://codecov.io/gh/shopinvader/odoo-shopinvader-payment)
<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

Payment methods for Odoo Shopinvader

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[shopinvader_api_payment](shopinvader_api_payment/) | 16.0.1.1.0 (unported) |  | Shopinvader services to be able to pay (invoices, carts,...)
[shopinvader_api_payment_cart](shopinvader_api_payment_cart/) | 16.0.1.1.0 (unported) |  | Adds logic to be able to pay current cart
[shopinvader_api_payment_provider_custom](shopinvader_api_payment_provider_custom/) | 16.0.1.0.0 (unported) |  | Specific routes for custom payments (wire transfers...) from Shopinvader
[shopinvader_api_payment_provider_stripe](shopinvader_api_payment_provider_stripe/) | 16.0.1.0.0 (unported) |  | Specific routes for Stripe payments from Shopinvader

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Shopinvader
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
