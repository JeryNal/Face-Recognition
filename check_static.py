import os

def check_static_files():
    required_files = [
        'static/css/style.css',
        'static/js/main.js',
        'static/js/charts.js',
        'static/js/notifications.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files 