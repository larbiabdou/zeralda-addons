{
    'name': 'Chicken production',
    'version': '17.0',
    'summary': 'Chicken production',
    'description': 'Chicken production',
    'category': 'Manufacturing',
    'depends': ['stock', 'import_folder'],
    'data': [
        'security/ir.model.access.csv',
        'views/chick_configuration_views.xml',
        'views/chicken_building_views.xml',
        'views/production_phase_views.xml',
        'views/chicken_production_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}