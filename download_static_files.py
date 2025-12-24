"""
اسکریپت برای دانلود فایل‌های CDN و قرار دادن آن‌ها در پوشه static
این اسکریپت باید یک بار اجرا شود تا همه فایل‌های خارجی به صورت محلی دانلود شوند.
"""

import os
import sys
import io
import urllib.request
from pathlib import Path

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'

# لیست فایل‌هایی که باید دانلود شوند
FILES_TO_DOWNLOAD = {
    # Bootstrap 5.3.6
    'css/bootstrap.min.css': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css',
    'js/bootstrap.bundle.min.js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js',
    
    # Bootstrap Icons
    'css/bootstrap-icons.css': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.12.1/font/bootstrap-icons.min.css',
    # Bootstrap Icons font files
    'fonts/bootstrap-icons.woff': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.12.1/font/fonts/bootstrap-icons.woff',
    'fonts/bootstrap-icons.woff2': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.12.1/font/fonts/bootstrap-icons.woff2',
    
    # jQuery
    'js/jquery.min.js': 'https://code.jquery.com/jquery-3.7.1.min.js',
    
    # Popper.js
    'js/popper.min.js': 'https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js',
    
    # Select2
    'css/select2.min.css': 'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
    'css/select2-bootstrap4.min.css': 'https://raw.githubusercontent.com/ttskch/select2-bootstrap4-theme/master/dist/select2-bootstrap4.min.css',
    'js/select2.min.js': 'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
    
    # Persian Datepicker
    'css/persian-datepicker.min.css': 'https://cdn.jsdelivr.net/npm/persian-datepicker@latest/dist/css/persian-datepicker.min.css',
    'js/persian-date.min.js': 'https://cdn.jsdelivr.net/npm/persian-date@latest/dist/persian-date.min.js',
    'js/persian-datepicker.min.js': 'https://cdn.jsdelivr.net/npm/persian-datepicker@latest/dist/js/persian-datepicker.min.js',
    
    # Chart.js
    'js/chart.js': 'https://cdn.jsdelivr.net/npm/chart.js@latest/dist/chart.umd.js',
    
    # Font Awesome
    'css/fontawesome.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    # Font Awesome font files (woff2 format)
    'fonts/fa-solid-900.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2',
    'fonts/fa-regular-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-regular-400.woff2',
    'fonts/fa-brands-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-brands-400.woff2',
}


def download_file(url, filepath):
    """دانلود یک فایل از URL و ذخیره در مسیر مشخص شده"""
    try:
        print(f"در حال دانلود: {url}")
        print(f"ذخیره در: {filepath}")
        
        # ایجاد پوشه‌ها در صورت نیاز
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # دانلود فایل
        urllib.request.urlretrieve(url, filepath)
        print(f"✓ موفق: {filepath.name}\n")
        return True
    except Exception as e:
        print(f"✗ خطا در دانلود {url}: {str(e)}\n")
        return False


def main():
    """تابع اصلی برای دانلود همه فایل‌ها"""
    print("=" * 60)
    print("شروع دانلود فایل‌های CDN...")
    print("=" * 60)
    print()
    
    success_count = 0
    fail_count = 0
    
    for relative_path, url in FILES_TO_DOWNLOAD.items():
        filepath = STATIC_DIR / relative_path
        
        # اگر فایل قبلاً وجود دارد، نادیده بگیر (می‌توانید این را حذف کنید)
        if filepath.exists():
            print(f"⚠ فایل از قبل وجود دارد: {relative_path}")
            print(f"  برای دانلود مجدد، فایل را حذف کنید.\n")
            success_count += 1
            continue
        
        if download_file(url, filepath):
            success_count += 1
        else:
            fail_count += 1
    
    print("=" * 60)
    print(f"خلاصه: {success_count} موفق, {fail_count} ناموفق")
    print("=" * 60)
    
    if fail_count == 0:
        print("\n✓ همه فایل‌ها با موفقیت دانلود شدند!")
        print("حالا می‌توانید لینک‌های CDN را در قالب‌ها تغییر دهید.")
    else:
        print(f"\n⚠ {fail_count} فایل دانلود نشد. لطفاً اتصال اینترنت خود را بررسی کنید.")


if __name__ == '__main__':
    main()

