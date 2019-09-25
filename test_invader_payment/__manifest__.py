# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Test invader payment",
    "summary": "Test Invader payment",
    "version": "10.0.1.0.0",
    "category": "Shopinvader",
    "website": "www.akretion.com",
    "author": " Akretion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": [], "bin": []},
    "depends": [
        "invader_payment_stripe",
        "invader_payment_manual",
        "invader_payment_sips",
    ],
    "data": [],
    "demo": [],
    "qweb": [],
}
