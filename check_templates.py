import os

def check_templates():
    required_templates = [
        'templates/base.html',
        'templates/admin/dashboard.html',
        'templates/admin/reports.html',
        'templates/errors/404.html',
        'templates/errors/500.html',
        'templates/emails/verification.html'
    ]
    
    missing_templates = []
    for template in required_templates:
        if not os.path.exists(template):
            missing_templates.append(template)
    
    return missing_templates 