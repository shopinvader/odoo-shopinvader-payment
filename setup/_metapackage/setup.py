import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-shopinvader-odoo-shopinvader-payment",
    description="Meta package for shopinvader-odoo-shopinvader-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-shopinvader_api_payment>=16.0dev,<16.1dev',
        'odoo-addon-shopinvader_api_payment_cart>=16.0dev,<16.1dev',
        'odoo-addon-shopinvader_api_payment_provider_custom>=16.0dev,<16.1dev',
        'odoo-addon-shopinvader_api_payment_provider_sips>=16.0dev,<16.1dev',
        'odoo-addon-shopinvader_api_payment_provider_stripe>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
