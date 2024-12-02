{
    'name': 'Import Folder',
    'version': '17.0',
    'summary': 'Import Folder',
    'description': 'Import Folder',
    'category': 'Purchase',
    'depends': ['purchase', 'stock_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        'views/import_folder_views.xml',
        'views/import_port_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}