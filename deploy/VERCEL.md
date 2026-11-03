# النشر على Vercel + Neon (بدون بطاقة بنكية)

Vercel يستضيف Django أصلاً (Python runtime) ويكتشف `manage.py` تلقائياً، ويشغّل
`collectstatic` بنفسه. لا يحتاج بطاقة، ويعطي رابطاً دائماً `*.vercel.app` مع إمكانية
ربط نطاقك الخاص مجاناً.

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
قاعدة Neon وتُخدَم عبر `/media/...` (بحد أقصى 4.5MB للطلب الواحد، والصور
تُصغَّر إلى 800px مسبقاً).

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
- فعّل HSTS بعد ثبات النطاق: `DJANGO_SECURE_HSTS_SECONDS=31536000`.

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
