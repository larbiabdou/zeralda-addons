{
    'name': 'Accounting cash',
    'version': '17.0',
    'summary': 'Accounting cash',
    'description': 'Accounting cash',
    'category': 'account',
    'depends': ['account_accountant', 'hr', 'account_budget'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/bank_statement_line_wizard.xml',
        'views/account_journal_views.xml',
        'views/menu_views.xml',
        'views/account_bank_statement.xml',
    ],
    'installable': True,
    'auto_install': False,
}
