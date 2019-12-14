#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Maduka Sopulu Chris kingston
#
# Created:     20/04/2018
# Copyright:   (c) kingston 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
{
    'name': 'Internal Memo Vascon.',
    'version': '10.0.1.0.0',
    'author': 'Maduka Sopulu',
    'description':"""Internal memo application is a module that helps organization send according to organogram""",
    'category': 'Internal Memo',

    'depends': ['account','hr_expense','purchase'],
    'data': [
        'views/memo_view.xml',
        'security/security_group.xml',
        'security/ir.model.access.csv',
    ],
    'price': 14.99,
    'currency': 'USD',


    'installable': True,
    'auto_install': False,
}
