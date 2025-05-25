{
    'name': 'Random Team Generator',
    'version': '1.0',
    'summary': 'Génère des équipes aléatoires avec un chef d’équipe',
    'category': 'Tools',
    'author': 'Kavola DIBI',
    'website': 'https://coconut.ci',
    'license': 'LGPL-3',
    'depends': ['base','contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_setting.xml',
        'views/team_views.xml',
        'views/res_partner_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': True,
}
