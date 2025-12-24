"""
اسکریپت برای جایگزینی خودکار همه لینک‌های CDN با فایل‌های محلی
"""

import re
import sys
import io
from pathlib import Path

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent

# لیست جایگزینی‌ها: (pattern, replacement)
REPLACEMENTS = [
    # Bootstrap CSS
    (r'https://cdn\.jsdelivr\.net/npm/bootstrap@[\d.]+/dist/css/bootstrap\.min\.css', 
     r"{% static 'css/bootstrap.min.css' %}"),
    
    # Bootstrap JS
    (r'https://cdn\.jsdelivr\.net/npm/bootstrap@[\d.]+/dist/js/bootstrap\.(bundle\.)?min\.js',
     r"{% static 'js/bootstrap.bundle.min.js' %}"),
    
    # Bootstrap Icons
    (r'https://cdn\.jsdelivr\.net/npm/bootstrap-icons@[\d.]+/font/bootstrap-icons\.min\.css',
     r"{% static 'css/bootstrap-icons.css' %}"),
    
    # jQuery
    (r'https://code\.jquery\.com/jquery-[\d.]+\.min\.js',
     r"{% static 'js/jquery.min.js' %}"),
    
    # Popper.js
    (r'https://cdn\.jsdelivr\.net/npm/@popperjs/core@[\d.]+/dist/umd/popper\.min\.js',
     r"{% static 'js/popper.min.js' %}"),
    
    # Select2
    (r'https://cdn\.jsdelivr\.net/npm/select2@[\d.]+/dist/css/select2\.min\.css',
     r"{% static 'css/select2.min.css' %}"),
    (r'https://cdn\.jsdelivr\.net/npm/@ttskch/select2-bootstrap4-theme@[\d.]+/dist/select2-bootstrap4\.min\.css',
     r"{% static 'css/select2-bootstrap4.min.css' %}"),
    (r'https://cdn\.jsdelivr\.net/npm/select2@[\d.]+/dist/js/select2\.min\.js',
     r"{% static 'js/select2.min.js' %}"),
    
    # Persian Datepicker
    (r'https://cdn\.jsdelivr\.net/npm/persian-datepicker@latest/dist/css/persian-datepicker\.min\.css',
     r"{% static 'css/persian-datepicker.min.css' %}"),
    (r'https://cdn\.jsdelivr\.net/npm/persian-date@latest/dist/persian-date\.min\.js',
     r"{% static 'js/persian-date.min.js' %}"),
    (r'https://cdn\.jsdelivr\.net/npm/persian-datepicker@latest/dist/js/persian-datepicker\.min\.js',
     r"{% static 'js/persian-datepicker.min.js' %}"),
    
    # Chart.js
    (r'https://cdn\.jsdelivr\.net/npm/chart\.js',
     r"{% static 'js/chart.js' %}"),
    
    # Font Awesome
    (r'https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[\d.]+/css/all\.min\.css',
     r"{% static 'css/fontawesome.min.css' %}"),
    
    # Google Fonts (Vazirmatn) - حذف می‌شود
    (r'<link[^>]*href="https://fonts\.googleapis\.com[^"]*"[^>]*>',
     r'{% comment %} Google Font removed - using system fonts {% endcomment %}'),
]


def replace_in_file(filepath):
    """جایگزینی لینک‌های CDN در یک فایل"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        has_load_static = '{% load static %}' in content or '{%load static%}' in content
        
        # اگر static load نشده و نیاز داریم، اضافه کن
        if not has_load_static and any('{% static' in replacement[1] for replacement in REPLACEMENTS):
            # پیدا کردن اولین {% extends %} یا {% block %}
            if '{% extends' in content:
                content = re.sub(
                    r'({% extends[^%]+%})',
                    r'\1\n{% load static %}',
                    content,
                    count=1
                )
            elif '<!DOCTYPE' in content or '<html' in content:
                # اگر extends نداره، در ابتدای head اضافه کن
                content = re.sub(
                    r'(<head[^>]*>)',
                    r'\1\n{% load static %}',
                    content,
                    count=1
                )
            else:
                content = '{% load static %}\n' + content
        
        # انجام جایگزینی‌ها
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # حذف integrity و crossorigin از تگ‌های link و script
        content = re.sub(r'\s+integrity="[^"]*"', '', content)
        content = re.sub(r'\s+crossorigin="[^"]*"', '', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"خطا در پردازش {filepath}: {e}")
        return False


def main():
    """تابع اصلی"""
    print("جستجوی فایل‌های HTML...")
    
    templates_dir = BASE_DIR / 'templates'
    html_files = []
    
    # پیدا کردن همه فایل‌های HTML
    for html_file in templates_dir.rglob('*.html'):
        html_files.append(html_file)
    
    # همچنین در پوشه‌های app templates
    for app_dir in ['project', 'core', 'experiment']:
        app_templates = BASE_DIR / app_dir / 'templates'
        if app_templates.exists():
            for html_file in app_templates.rglob('*.html'):
                html_files.append(html_file)
    
    print(f"تعداد {len(html_files)} فایل HTML پیدا شد.\n")
    
    modified_count = 0
    for html_file in html_files:
        if replace_in_file(html_file):
            print(f"✓ تغییر داده شد: {html_file.relative_to(BASE_DIR)}")
            modified_count += 1
    
    print(f"\nخلاصه: {modified_count} فایل تغییر داده شد.")


if __name__ == '__main__':
    main()

