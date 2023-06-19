import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-shopinvader-odoo-shopinvader-payment",
    description="Meta package for shopinvader-odoo-shopinvader-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-invader_invoice_payment',
        'odoo14-addon-invader_payment',
        'odoo14-addon-invader_payment_adyen',
        'odoo14-addon-invader_payment_adyen_klarna',
        'odoo14-addon-invader_payment_adyen_klarna_capture',
        'odoo14-addon-invader_payment_adyen_klarna_capture_delivery',
        'odoo14-addon-invader_payment_adyen_klarna_invoice',
        'odoo14-addon-invader_payment_adyen_klarna_sale',
        'odoo14-addon-invader_payment_adyen_sepa',
        'odoo14-addon-invader_payment_manual',
        'odoo14-addon-invader_payment_sale',
        'odoo14-addon-invader_payment_stripe',
        'odoo14-addon-shopinvader_invoice_payment',
        'odoo14-addon-shopinvader_payment',
        'odoo14-addon-shopinvader_payment_adyen',
        'odoo14-addon-shopinvader_payment_condition',
        'odoo14-addon-shopinvader_payment_manual',
        'odoo14-addon-shopinvader_payment_stripe',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
