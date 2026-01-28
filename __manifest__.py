{
    'name': 'Flight Management',
    'version': '19.0.1.0.0',
    'summary': 'Simple flight management with API sync',
    'author': 'Yaqoub',
    'category': 'Services',
    'depends': ['base', 'portal', 'website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/flight_security.xml',
        'views/flight_view.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'Flight_Task/static/src/css/portal_flights.css',
            'Flight_Task/static/src/js/portal_flights.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
