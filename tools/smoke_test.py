# -*- coding: utf-8 -*-
import django, os, io, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.test import Client, RequestFactory
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
c = Client(SERVER_NAME='localhost')

def run(name, fn):
    try:
        ok = fn()
    except Exception as e:
        ok = False
        print('   error:', repr(e))
    print(('PASS' if ok else 'FAIL'), name)
    return ok

results = []
results.append(run('login status 200', lambda: c.get('/accounts/login/').status_code == 200))
r = c.get('/accounts/login/')
html = r.content.decode('utf-8')
results.append(run('no EN "Login"', lambda: 'Login' not in html))
results.append(run('ar "تسجيل الدخول"', lambda: 'تسجيل الدخول' in html))
results.append(run('ar "كلمة المرور"', lambda: 'كلمة المرور' in html))
results.append(run('ar "المنصة المدرسية"', lambda: 'المنصة المدرسية' in html))

r2 = c.get('/nonexistent-xyz/')
h2 = r2.content.decode('utf-8')
results.append(run('dev 404 (Django technical page, expected)', lambda: r2.status_code == 404 and 'Page not found' in h2))

rf = RequestFactory()
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.exception import response_for_exception
from django.core.exceptions import PermissionDenied, BadRequest
from django.test.utils import override_settings

def mkreq():
    r = rf.get('/x')
    r.user = AnonymousUser()
    return r

with override_settings(DEBUG=False):
    r403 = response_for_exception(mkreq(), PermissionDenied()).content.decode('utf-8')
    results.append(run('handler403 ar "تم رفض الوصول"', lambda: 'تم رفض الوصول' in r403))
    r400 = response_for_exception(mkreq(), BadRequest('x')).content.decode('utf-8')
    results.append(run('handler400 ar "طلب غير صحيح"', lambda: 'طلب غير صحيح' in r400))

with override_settings(DEBUG=False):
    c2 = Client(SERVER_NAME='localhost')
    r404 = c2.get('/nonexistent-xyz/')
    h404 = r404.content.decode('utf-8')
    results.append(run('prod 404 ar "الصفحة غير موجودة"', lambda: r404.status_code == 404 and 'الصفحة غير موجودة' in h404))
    results.append(run('prod 404 no EN "Page not found"', lambda: 'Page not found' not in h404))

from django.template.loader import get_template
t404 = get_template('errors/404.html').render({})
results.append(run('errors/404.html ar "الصفحة غير موجودة"', lambda: 'الصفحة غير موجودة' in t404))
t500 = get_template('errors/500.html').render({})
results.append(run('errors/500.html ar "حدث خطأ غير متوقع"', lambda: 'حدث خطأ غير متوقع' in t500))

print('ALL PASS' if all(results) else 'SOME FAILED')
