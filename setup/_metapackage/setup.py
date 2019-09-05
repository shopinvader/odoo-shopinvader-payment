import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-shopinvader-odoo-shopinvader-payment",
    description="Meta package for shopinvader-odoo-shopinvader-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-shopinvader_locomotive_payment_adyen',
        'odoo10-addon-shopinvader_payment',
        'odoo10-addon-shopinvader_payment_adyen',
        'odoo10-addon-shopinvader_payment_paypal',
        'odoo10-addon-shopinvader_payment_stripe',
        'odoo10-addon-shopinvader_quotation_payment',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
