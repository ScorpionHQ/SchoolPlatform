# النشر على Vercel + Neon (بدون بطاقة بنكية)

Vercel يستضيف Django أصلاً (Python runtime) ويكتشف `manage.py` تلقائياً، ويشغّل
`collectstatic` بنفسه. لا يحتاج بطاقة، ويعطي رابطاً دائماً `*.vercel.app` مع إمكانية
ربط نطاقك الخاص مجاناً.

## الرابط الحالي (منشور ويعمل)

| الرابط | ملاحظة |
|---|---|
| <https://schoolplatform-iq.vercel.app> | الرابط الأساسي |
| <https://schoolplatform-app.vercel.app> | رابط بديل |
| <https://schoolplatform-beta.vercel.app> | الرابط الذي أنشأه Vercel تلقائياً |

المشروع على Vercel: `schoolplatform` (id: `prj_KUKYs6FB4vYas7Y8VbQYw5OvYnLH`).
آخر نشر ناجح: `dpl_FV5ZnFgTgzv5tXBBjwwrfcA36Q2n`.

> التحديثات المستقبلية: لا يوجد ربط Git بعد، لذا بعد كل `git push` أعد تشغيل سكربت
> النشر (`deploy_vercel_files.ps1`) أو اربط المستودع من **Project → Settings → Git**
> ليصبح النشر تلقائياً.

## 1) قاعدة البيانات (تمّت)

قاعدة Neon المجانية أُنشئت فعلاً:

| العنصر | القيمة |
|---|---|
| المشروع | `schoolplatform` |
| Region | `aws-eu-central-1` (فرانكفورت) |
| المضيف (pooled) | `ep-falling-rain-b98rh7rz-pooler.c-7.eu-central-1.aws.neon.tech` |
| القاعدة | `neondb` |

رابط الاتصال الكامل محفوظ محلياً في
`C:\Users\PC\AppData\Local\Temp\opencode\neon-uri.txt` — لا ترفعه إلى GitHub.

## 2) متغيّرات البيئة في Vercel

| المتغيّر | القيمة |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | مفتاح عشوائي طويل |
| `DJANGO_ALLOWED_HOSTS` | `.vercel.app` ثم نطاقك لاحقاً |
| `DATABASE_URL` | رابط Neon (Pooled) |
| `BOOTSTRAP_ADMIN_USERNAME` | `admin` |
| `BOOTSTRAP_ADMIN_PASSWORD` | كلمة مرور مؤقتة قوية |
| `PYTHON_VERSION` | `3.12` (اختياري) |

توليد مفتاح سري:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 3) البناء والتشغيل

`vercel.json` يضبط:

- `buildCommand`: `migrate` ثم `bootstrap_admin` (ينشئ المدير مرة واحدة فقط).
- `regions`: `fra1` قريب من قاعدة Neon في فرانكفورت.
- `functions`: مهلة 60 ثانية لدالة `config/wsgi.py`.

Vercel يشغّل `collectstatic` تلقائياً لأن `STATIC_ROOT` مضبوط، ويخدم الملفات
الثابتة من شبكته (CDN). لا حاجة إلى `whitenoise` في الإنتاج.

## 4) الملفات المرفوعة (صور الملفات الشخصية)

قرص Vercel مؤقت للقراءة فقط، لذا `config/settings/production.py` يستخدم
`core.storage.DatabaseStorage` تلقائياً عند غياب إعدادات S3. الصور تُخزَّن في
قاعدة Neon وتُخدَم عبر `/media/...`. الصور الكبيرة تُصغَّر داخل المتصفح قبل
الإرسال (حد Vercel للطلب 4.5MB)، ثم تُصغَّر مرة أخرى إلى 800px على الخادم.

## 5) النشر من لوحة Vercel

1. افتح <https://vercel.com/new> وسجّل الدخول بحساب GitHub.
2. اختر مستودع `ScorpionHQ/SchoolPlatform` ثم **Import**.
3. الصق متغيّرات البيئة من الجدول أعلاه ثم **Deploy**.
4. بعد 2–4 دقائق يصبح الرابط جاهزاً: `https://schoolplatform-xxxx.vercel.app`.

## 6) النشر عبر API (بدون لوحة)

```powershell
$token = (Get-Content C:\Users\PC\AppData\Local\Temp\opencode\api-keys.json -Raw | ConvertFrom-Json).vercel_token
$h = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }

# 1) إنشاء المشروع وربطه بـ GitHub
$project = @{ name = 'schoolplatform'; framework = 'django'; gitRepository = @{ type = 'github'; repo = 'ScorpionHQ/SchoolPlatform' } } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri 'https://api.vercel.com/v11/projects' -Method Post -Headers $h -Body $project

# 2) إضافة متغيّرات البيئة (لكل بيئة production/preview/development)
```

## 7) بعد النشر

- سجّل الدخول بالرمز `SYS000001` (أو اسم المستخدم `admin`) وكلمة المرور المؤقتة،
  وغيّرها فوراً.
- أضف نطاقك: **Project → Settings → Domains** ثم أضف النطاق إلى
  `DJANGO_ALLOWED_HOSTS`.
- HSTS مفعّل حالياً سنة كاملة (`DJANGO_SECURE_HSTS_SECONDS=31536000`, مع
  `includeSubDomains`). إن انتقلت إلى نطاق جديد فالنطاق القديم يبقى مثبّتاً في
  المتصفحات التي زارته — وهذا مقصود. لإيقافه مؤقتاً اضبط القيمة على `0`.

## 8) البريد (استعادة كلمة المرور) — مفعّل

البريد يعمل الآن عبر **Brevo** (مجاني، 300 رسالة/يوم، بلا بطاقة). المتغيّرات
مضبوطة على Vercel وقيم المفتاح مشفّرة هناك فقط — لا توجد في الكود ولا في Git.

| المتغيّر | القيمة |
|---|---|
| `EMAIL_HOST` | `smtp-relay.brevo.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `1` |
| `EMAIL_HOST_USER` | `c15211001@smtp-brevo.com` (SMTP login من Brevo، وليس بريدك العادي) |
| `EMAIL_HOST_PASSWORD` | مفتاح SMTP (`xsmtpsib-...`)، مشفّر |
| `DEFAULT_FROM_EMAIL` | `SchoolPlatform <scorpionhq26@gmail.com>` |

نقاط مهمة:

- **عنوان المُرسِل يجب أن يكون موثّقاً في Brevo** (Senders)، وإلا يرفض الإرسال.
  لتوثيق نطاق المدرسة لاحقاً: Brevo → Domains → إضافة سجلات DNS.
- **نموذج الاستعادة يطلب «كود الدخول» لا البريد** (مثل `SYS000001`).
- حساب `SYS000001` مربوط بالبريد `scorpionhq26@gmail.com`؛ بدون بريد مسجّل
  لا تُرسل أي رسالة (الصفحة تُظهر نفس الرسالة في كل الأحوال لمنع كشف الحسابات).
- فشل الإرسال يُسجَّل في سجلات Vercel بدل أن يُبتلع بصمت.

اختبار الإرسال محلياً (يتطلب نفس متغيّرات البيئة):

```bash
python manage.py send_test_email you@example.com
```

## 9) التخزين المؤقت المشترك

حد المحاولات يستخدم قاعدة البيانات (`DatabaseCache`) لأن Vercel يشغّل عدة
نسخ من الدالة، ولكل نسخة ذاكرة مستقلة. جدول `django_cache` يُنشأ تلقائياً في
أمر البناء عبر `python manage.py createcachetable` (idempotent).
تغيير اسم الجدول: `DJANGO_CACHE_TABLE`.

## 10) مسار لوحة الإدارة

`DJANGO_ADMIN_URL` يحدد مسار لوحة Django. القيمة الحالية سرية ومخزّنة في
متغيّرات البيئة (وليست في الكود)، و`/admin/` لم يعد يعمل.
لتغييرها: عدّل المتغيّر ثم أعد النشر.

## 11) النسخ الاحتياطي

```powershell
$env:NEON_API_KEY="napi_..."
$env:NEON_PROJECT_ID="frosty-dawn-46163110"
python deploy\neon_backup.py
```

ينشئ فرعاً باسم `backup-YYYYMMDD-HHMM` (نسخة فورية copy-on-write داخل Neon)
ويحذف الأقدم تلقائياً مع إبقاء 5 نسخ (`NEON_BACKUP_KEEP`).

أول نسخة أُنشئت: `backup-20261103-1712` (الفرع الأساسي `main`).

للجدولة الأسبوعية على Windows:

```powershell
schtasks /Create /SC WEEKLY /D SUN /TN "SchoolPlatformBackup" /TR "python E:\Desktop\SchoolPlatform\deploy\neon_backup.py" /ST 03:00
```

الاستعادة: أنشئ رابط اتصال من فرع النسخة في لوحة Neon وضعه في `DATABASE_URL`
ثم أعد النشر (أو انسخ البيانات إلى الفرع الأساسي).

## 12) المراقبة والنشر التلقائي

- **المراقبة:** `.github/workflows/uptime.yml` يفحص صفحة الدخول كل 30 دقيقة
  ويفشل عند أي رد غير 200 (فعّل إشعارات GitHub ليصلك بريد).

### النشر

المشروع **ليس مربوطاً بـ Git** على Vercel (الربط يتطلب Login Connection مع
GitHub). لذلك يوجد مسارَان:

**أ) تلقائي عبر GitHub Actions (المستخدَم حالياً)**

`.github/workflows/deploy.yml` ينشر عند كل `push` إلى `main` باستخدام
`deploy/vercel_deploy.py` وواجهة Vercel البرمجية. يلزم سر واحد فقط:

1. <https://vercel.com/account/tokens> → **Create Token** (صلاحية كاملة، نطاق
   المشروع أو الحساب).
2. GitHub → **Settings → Secrets and variables → Actions → New repository
   secret** بالاسم `VERCEL_TOKEN`.
3. **Actions → Deploy → Run workflow** لتجربة أول نشر.

**ب) يدوي من أي جهاز**

```powershell
$env:VERCEL_TOKEN = "..."
python deploy\vercel_deploy.py
```

السكربت يرفع الملفات المتغيّرة فقط (بصمة SHA-1)، ويرفع بالتوازي (8 عمال)،
ثم ينتظر حتى تصبح الحالة `READY`. يتجاوز `.git` و`media` و`staticfiles`
و`venv` و`.env*` تلقائياً.

**ج) الربط الرسمي بـ Git (الأفضل لاحقاً)**

أضف Login Connection من
<https://vercel.com/account/settings/authentication> ثم
**Project → Settings → Git → Connect Git Repository**. بعدها يمكن حذف
الوركفلو، لأن Vercel سينشر بنفسه.

> آخر نشر: `dpl_FV5ZnFgTgzv5tXBBjwwrfcA36Q2n` — 348 ملفاً، 315 بصمة فريدة،
> البناء `READY` على `fra1`.


## حدود الخطة المجانية

| الحد | القيمة |
|---|---|
| طلبات الدالة | غير محدودة عملياً للاستخدام المدرسي |
| مدة الطلب | 60 ثانية |
| حجم الطلب | 4.5MB |
| النطاقات المخصصة | مجانية |
| البطاقة البنكية | غير مطلوبة |

> إن احتجت لاحقاً تشغيلاً بلا أي حدود، يمكن نقل المشروع إلى أي VPS عبر
> `gunicorn` (نفس `config.settings.production`).
