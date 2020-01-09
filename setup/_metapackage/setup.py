import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-shopinvader-odoo-shopinvader-payment",
    description="Meta package for shopinvader-odoo-shopinvader-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-invader_payment',
        'odoo13-addon-shopinvader_payment',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
