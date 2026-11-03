# المنصة المدرسية — SchoolPlatform

نظام إدارة مدرسية احترافي مبني بـ **Django**، مصمم للمدارس الأهلية والمعاهد والمراكز التعليمية، بواجهة عربية كاملة (دعم RTL) مع إمكانية التبديل إلى الإنجليزية.

## المميزات

### بوابات مخصصة لكل دور
- **الطلاب**: لوحة تحكم، موادي الدراسية، درجاتي، سجلات الحضور، الملف الشخصي.
- **أولياء الأمور**: لوحة تحكم، أبنائي، درجات الأبناء، سجلات الحضور، الملف الشخصي.
- **المعلمون**: لوحة تحكم، طلابي، جلسات تسجيل الحضور، إدخال الدرجات.
- **الإدارة (مدير / مساعد مدير / مدير النظام)**: لوحة تحكم مركزية مع إحصائيات.

### إدارة المؤسسات التعليمية
- إدارة متعددة المؤسسات (مدارس / معاهد / مراكز).
- تخصيص اسم المؤسسة وشعارها وألوانها ومعلومات التواصل.
- الصفوف، المواد، الطلاب، المعلمون، أولياء الأمور.

### الأكاديمي
- تسجيل الحضور (جلسات + تسجيل جماعي "الجميع حاضر").
- إدخال الدرجات للامتحانات مع التحقق من صحة الدرجات.
- حساب متوسط الدرجات ونسب الحضور تلقائياً.

### الاستيراد الجماعي
- استيراد الطلاب من ملفات **Excel** مع إنشاء حسابات تلقائياً.
- دعم العناوين بالعربية أو الإنجليزية في رأس الملف.
- عرض تقرير بالنتائج (مستورد / متخطى / أخطاء).

### تطبيق ويب قابل للتثبيت (PWA)
- المنصة تعمل كتطبيق يُثبَّت على الهواتف والكمبيوتر (أيقونة + ملء شاشة) بدون متاجر.
- ملفات جاهزة: `static/pwa/manifest.webmanifest` وأيقونات + خدمة Worker.
- يُفعَّل التثبيت تلقائياً بعد نشر المنصة عبر **HTTPS**.
- الوضع الليلي يغيّر لون شريط المتصفح تلقائياً (`theme-color`).

### الأمان
- كود دخول فريد لكل مستخدم (SYS / ADM / ASM / TCH / STU / PAR).
- إجبار المستخدم على تغيير كلمة المرور المؤقتة عند أول تسجيل دخول (Middleware + على مستوى العرض).
- فصل صارم للصلاحيات بين الأدوار (ممنوع الوصول عبر مباشرة الروابط).
- حذف السجلات عبر طلبات POST فقط (حماية من CSRF).
- لوحة الإدارة على رابط مخصص قابل للتهيئة عبر `DJANGO_ADMIN_URL`.
- كلمة مرور إدارية عبر متغير بيئة `DJANGO_SECRET_KEY` بدلاً من القيمة الثابتة.
- رسائل خطأ عامة في الإنتاج بدون كشف التفاصيل التقنية.
- اختبارات آلية لتسجيل الدخول والصلاحيات والاستيراد (`python manage.py test`).

### اللغة
- عربي كامل (RTL + خط Cairo) مع إمكانية التبديل للإنجليزية من الشريط العلوي.
- ملفات ترجمة جاهزة: `locale/ar/LC_MESSAGES/django.po` (214 رسالة مترجمة 100%).

## بيانات الدخول الافتراضية

تم تسليم المنصة بقاعدة بيانات فارغة تماماً (لا طلاب ولا معلمون ولا أولياء أمور ولا صفوف)، مع حساب مدير نظام واحد فقط:

| الدور | كود الدخول | كلمة المرور المؤقتة |
| --- | --- | --- |
| مدير النظام | `SYS000001` | `School@2026#Admin` |

> سيُطلب منك تغيير كلمة المرور فور أول تسجيل دخول (إجراء أمني إلزامي). لا تنشر هذه البيانات، وغيّر كلمة المرور فور الاستلام.

لإنشاء مدير إضافي:

```bash
python manage.py createsuperuser
```

## تشغيل المشروع

### المتطلبات
- Python 3.12+
- gettext (لترجمة الرسائل عند الحاجة)

### 1) إنشاء البيئة الافتراضية

```bash
python -m venv venv
```

### 2) تفعيل البيئة

- Windows:

```bash
venv\Scripts\activate
```

- Linux / macOS:

```bash
source venv/bin/activate
```

### 3) تثبيت الحزم

```bash
pip install -r requirements.txt
```

### 4) تشغيل الترحيلات

```bash
python manage.py migrate
```

### 5) إنشاء مدير النظام (مرة واحدة)

```bash
python manage.py createsuperuser
```

أو استخدم بيانات الحساب الجاهزة أعلاه في قسم "بيانات الدخول الافتراضية".

### 6) تشغيل الخادم

```bash
python manage.py runserver
```

ثم افتح:

```
http://127.0.0.1:8000/
```

### إعداد متغير البيئة (اختياري لكن موصى به في الإنتاج)

```bash
export DJANGO_SECRET_KEY="secret-key-صعب-و-طويل"
```

## إعادة بناء ملفات الترجمة (للمطورين)

يجب تثبيت `gettext` ثم:

```bash
python manage.py makemessages -l ar
# عدّل locale/ar/LC_MESSAGES/django.po
python manage.py compilemessages
```

## النشر (فريق السيرفرات)

إعدادات الإنتاج معدة مسبقاً عبر `config.settings.production`:

- `DEBUG=False` افتراضياً، و`config/wsgi.py` و`config/asgi.py` يثبّتان إعدادات **الإنتاج** افتراضياً (وليس التطوير).
- `SECRET_KEY` من `DJANGO_SECRET_KEY` مع رفض المفاتيح القصيرة أو الضعيفة.
- `ALLOWED_HOSTS` من `DJANGO_ALLOWED_HOSTS` (قيم مفصولة بفواصل). على Vercel وRender يُضاف نطاق الخدمة تلقائياً.
- سياسات أمان HTTPS مفعلة: إعادة توجيه SSL، كوكيز آمنة، `SECURE_PROXY_SSL_HEADER`، منع XSS و clickjacking. HSTS **مُعطَّل عن قصد** حتى تثبيت النطاق النهائي.
- قاعدة البيانات **PostgreSQL إلزامية** عبر `DATABASE_URL` (Neon أو أي مزوّد). لا يوجد fallback إلى SQLite في الإنتاج.
- الملفات المرفوعة تُخزَّن في أي S3 متوافق عند ضبط `AWS_*`، وإلا ففي قاعدة البيانات (لأن أقراص الاستضافات المجانية مؤقتة). تُخدَم عبر `/media/...`.
- البريد (استعادة كلمة المرور) عبر `EMAIL_HOST` وأخواته. عند تركه فارغاً تُطبَع الرسائل في سجلات الخادم.
- `gunicorn` و`whitenoise` و`dj-database-url` و`psycopg` مضمّنة في `requirements.txt`.

### نشر مجاني سريع (Vercel + Neon)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ScorpionHQ/SchoolPlatform&env=DJANGO_SETTINGS_MODULE,DJANGO_SECRET_KEY,DJANGO_ALLOWED_HOSTS,DATABASE_URL,BOOTSTRAP_ADMIN_PASSWORD&envDefaults=%7B%22DJANGO_SETTINGS_MODULE%22%3A%22config.settings.production%22%2C%22DJANGO_ALLOWED_HOSTS%22%3A%22.vercel.app%22%7D)

1. أنشئ قاعدة مجانية على [neon.tech](https://neon.tech) (تسجيل عبر GitHub، بلا بطاقة بنكية) وانسخ **Pooled connection string**.
2. اضغط الزر أعلاه، وسجّل الدخول إلى Vercel عبر GitHub، ثم الصق `DATABASE_URL` وبقية القيم.
3. انتظر 2–4 دقائق. رابطك سيكون: `https://schoolplatform-xxxx.vercel.app`.
4. ينشئ البناء مدير النظام تلقائياً من `BOOTSTRAP_ADMIN_PASSWORD`، ثم سجّل الدخول وغيّر كلمة المرور.
5. أضف نطاقك المخصص من **Settings → Domains** وحدّث `DJANGO_ALLOWED_HOSTS`.

> Vercel يكتشف Django تلقائياً ويشغّل `collectstatic` بنفسه؛ لا حاجة لإعداد خادم أو بطاقة.
> الدليل العربي الكامل: `deploy/VERCEL.md`. (دليل Render يبقى في `deploy/RENDER_NEON.md` لكن Render صار يطلب بيانات دفع حتى للخطة المجانية.)

### حزمة النشر الجاهزة `deploy/`

| الملف | الوظيفة |
| --- | --- |
| `deploy/deploy.sh` | سكربت نشر آلي كامل: تثبيت المتطلبات + نسخ المشروع + gunicorn + nginx + SSL |
| `deploy/.env.example` | نموذج متغيرات البيئة (يُنسخ إلى `/etc/schoolplatform/.env`) |
| `deploy/nginx.conf` | إعداد nginx كوكيل عكسي مع HTTPS وتخزين مؤقت للملفات الثابتة |
| `deploy/gunicorn.service` | خدمة gunicorn لنظام systemd |

**الطريقة السريعة (موصى بها):** ارفع المشروع إلى السيرفر ثم:

```bash
sudo bash deploy/deploy.sh
```

السكربت ينسخ المشروع إلى `/opt/schoolplatform`، وينشئ ملف `.env` (عدّله وضبط النطاق والمفتاح السري ثم أعد التشغيل)، ويجهّز كل شيء. قابل لإعادة التشغيل بأمان للتحديثات.

### المتغيرات البيئية المطلوبة

| المتغير | الوصف | مثال |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | المفتاح السري (إجباري) | `خط-سري-طويل-وصعب` |
| `DJANGO_ALLOWED_HOSTS` | النطاقات المسموحة مفصولة بفواصل | `school.example.com` |
| `DJANGO_ADMIN_URL` | رابط لوحة الإدارة (يُفضّل سري) | `school-admin-9x4/` |
| `DJANGO_DB_NAME/USER/PASSWORD/HOST` | بيانات PostgreSQL (اختياري) | `school_db` |

### خطوات النشر على سيرفر Linux (VPS)

1. تثبيت Python 3.12+ و gettext و nginx و PostgreSQL (اختياري).
2. رفع المشروع إلى السيرفر (باستثناء `venv/`, `db.sqlite3`, `media/`, `staticfiles/`).
3. إنشاء البيئة الافتراضية وتثبيت الحزم:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# لإزالة اعتماد PostgreSQL لو استخدمت SQLite: احذف سطر psycopg من requirements.txt
```

4. ضبط المتغيرات البيئية (انسخ `deploy/.env.example` إلى `/etc/schoolplatform/.env` وعدّله، أو عبر `~/.bashrc`):

```bash
export DJANGO_SECRET_KEY="مفتاح-سري-طويل-و-صعب"
export DJANGO_ALLOWED_HOSTS="example.com,www.example.com"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://example.com,https://www.example.com"
export DJANGO_ADMIN_URL="school-admin-9x4/"
```

5. تجهيز المشروع:

```bash
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
python manage.py check --deploy
```

6. التشغيل عبر gunicorn (مثبّت مسبقاً ضمن requirements.txt):

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
```

7. إعداد nginx كوكيل عكسي (نقل الطلبات من المنفذ 80/443 إلى 8000) وتهيئة شهادة SSL عبر Certbot.

8. التحقق النهائي:

```bash
curl -I https://example.com/          # يجب أن يعيد 200 أو 302
curl -I http://example.com/           # يجب أن يعيد 301 (HTTPS)
```

## ملاحظات

- المشروع مكتوب بأسلوب Django واضح وقابل للصيانة دون تعقيد غير ضروري.
- التوقيت الافتراضي: `Asia/Baghdad`.
- لتشغيل الاختبارات الآلية:

```bash
python manage.py test
```

- كلمات مرور الطلاب المستوردين من Excel مؤقتة وسيُجبَرون على تغييرها عند أول تسجيل دخول.
