# دليل النشر: Render Free + Neon

دليل عربي خطوة بخطوة لنشر منصة المدرسة مجاناً بالكامل، بدون بطاقة بنكية.

---

## ما ستحصل عليه

| الخدمة | ما تقدّمه مجاناً | الحد |
|---|---|---|
| **Render** (Web Service) | تشغيل Django + HTTPS + نطاق فرعي | 512MB RAM، ينام بعد 15 دقيقة خمول |
| **Neon Postgres** | قاعدة بيانات PostgreSQL | 1GB تخزين، 100 ساعة حساب/شهر |
| **Neon Object Storage** | تخزين الصور (S3 متوافق) | 5GB تخزين، 5GB نقل/شهر |

> **مهم:** Render لا يوفّر PostgreSQL مجاناً بشكل دائم (30 يوماً فقط)، لذلك نستخدم Neon.

---

## الخطوة 1 — إنشاء قاعدة البيانات على Neon

1. افتح <https://neon.com> وأنشئ حساباً (GitHub أو Google، بدون بطاقة).
2. أنشئ مشروعاً جديداً:
   - **Name:** `schoolplatform`
   - **Region:** `AWS eu-central-1` (Frankfurt) — نفس منطقة Render لتقليل التأخير.
   - **Postgres version:** الافتراضي (17 أو أحدث).
3. من صفحة المشروع، اضغط **Connect** واختر:
   - **Branch:** `main`
   - **Database:** `neondb`
   - **Role:** المالك
   - **Connection string:** ✅ فعّل **Connection pooling**
4. انسخ الرابط. سيكون بهذا الشكل:

```
postgresql://USER:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

> احتفظ بهذا الرابط، ستحتاجه باسم `DATABASE_URL`.
> وجود كلمة `-pooler` مهم: الإعدادات تكتشفه وتُعطّل المؤشرات من جهة الخادم تلقائياً.

---

## الخطوة 2 — إنشاء تخزين الصور على Neon

1. من لوحة Neon، افتح مشروعك ثم **Object Storage** (أو **Storage**).
2. أنشئ **Bucket** باسم: `media`
3. أنشئ **Credential** (مفتاح وصول) واختر صلاحية القراءة والكتابة على هذا الـ bucket.
4. انسخ هذه القيم الأربع من اللوحة:

| القيمة في اللوحة | المتغيّر في Render |
|---|---|
| Bucket name | `AWS_STORAGE_BUCKET_NAME` |
| Access key ID | `AWS_ACCESS_KEY_ID` |
| Secret access key | `AWS_SECRET_ACCESS_KEY` |
| Endpoint / S3 URL | `AWS_ENDPOINT_URL_S3` |
| Region | `AWS_REGION` |

> لا تخمّن الـ endpoint أو الـ region، انسخهما حرفياً من اللوحة.
> إذا لم تجد **Object Storage** في حسابك، تخطَّ هذه الخطوة: المنصة ستعمل وتخزّن الصور على قرص Render مؤقتاً (تُفقد عند إعادة النشر).

---

## الخطوة 3 — إنشاء خدمة الويب على Render

1. ارفع المشروع إلى GitHub (مستودع **خاص/Private** أفضل).
2. افتح <https://dashboard.render.com> → **New** → **Web Service**.
3. اربط مستودع GitHub واختره.
4. املأ الإعدادات:

| الحقل | القيمة |
|---|---|
| **Name** | `schoolplatform` |
| **Region** | `Frankfurt` |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |
| **Instance Type** | `Free` |
| **Health Check Path** | `/` |

> ملف `render.yaml` في المشروع يحتوي هذه الإعدادات، ويمكنك استخدام **Blueprint** بدل الإدخال اليدوي.

---

## الخطوة 4 — متغيّرات البيئة (Environment)

من تبويب **Environment** في Render، أضِف:

### إلزامية

| المتغيّر | القيمة |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | مفتاح عشوائي طويل (انظر أدناه) |
| `DJANGO_ALLOWED_HOSTS` | `schoolplatform.onrender.com` (ثم نطاقك لاحقاً) |
| `DATABASE_URL` | رابط Neon من الخطوة 1 |
| `PYTHON_VERSION` | `3.12.0` |
| `WEB_CONCURRENCY` | `1` |

توليد مفتاح سري قوي (شغّله على جهازك):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### تخزين الصور (من الخطوة 2)

| المتغيّر | القيمة |
|---|---|
| `AWS_STORAGE_BUCKET_NAME` | `media` |
| `AWS_ACCESS_KEY_ID` | من لوحة Neon |
| `AWS_SECRET_ACCESS_KEY` | من لوحة Neon |
| `AWS_ENDPOINT_URL_S3` | من لوحة Neon |
| `AWS_REGION` | من لوحة Neon |

### اختيارية

| المتغيّر | القيمة | ملاحظات |
|---|---|---|
| `OPENROUTER_API_KEY` | مفتاحك | لتشغيل المساعد الذكي |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://schoolplatform.onrender.com` | أضِف نطاقك المخصص لاحقاً |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` | **لا ترفعه فوق 0 إلا بعد تثبيت النطاق النهائي** |

> `DJANGO_ALLOWED_HOSTS` و`DJANGO_CSRF_TRUSTED_ORIGINS` يقبلان عدة قيم مفصولة بفاصلة.

### بريد استعادة كلمة المرور (اختياري)

بدون هذه المتغيّرات يظل زر «نسيت كلمة المرور» يعمل، لكن **رسالة الاستعادة تُطبَع في سجلات Render فقط** بدل إرسالها للمستخدم.

| المتغيّر | مثال | ملاحظات |
|---|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` | تركه فارغاً = الطباعة في السجلات |
| `EMAIL_PORT` | `587` | |
| `EMAIL_HOST_USER` | `school@gmail.com` | |
| `EMAIL_HOST_PASSWORD` | كلمة مرور التطبيقات | لحساب Gmail: **App Password** وليس كلمة المرور العادية |
| `DEFAULT_FROM_EMAIL` | `SchoolPlatform <school@gmail.com>` | يجب أن يطابق حساب الإرسال |
| `EMAIL_USE_TLS` | `1` | اتركه `1` مع المنفذ 587 |

> إن استخدمت بريداً مجانياً (Gmail/Brevo)، تحقّق أولاً من حد الإرسال اليومي (Gmail ≈ 500 رسالة). لمدرسة صغيرة هذا كافٍ.

---

## الخطوة 5 — أول نشر

1. اضغط **Create Web Service**. سيبدأ البناء (3–6 دقائق).
2. راقب **Logs**. أول سطر يجب أن يكون تنفيذ `migrate` بلا أخطاء.
3. عند ظهور `Your service is live`، افتح الرابط.
4. أنشئ حساب المدير:

   **الطريقة الأولى (من Render):** تبويب **Shell** ثم:

   ```bash
   python manage.py createsuperuser
   ```

   **الطريقة الثانية (من جهازك):**

   ```powershell
   $env:DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require"
   $env:DJANGO_SETTINGS_MODULE="config.settings.production"
   $env:DJANGO_SECRET_KEY="أي-نص-طويل-مؤقت"
   $env:DJANGO_ALLOWED_HOSTS="localhost"
   python manage.py createsuperuser
   ```

5. سجّل الدخول وابدأ بإعداد المدرسة من لوحة الإدارة.

> الطالب/المعلم يدخل برمز الدخول (مثل `STU000001`). بعد أول دخول، يجب تغيير كلمة المرور، والصورة الشخصية اختيارية.

---

## الخطوة 6 — ربط نطاقك الخاص

1. في Render: **Settings** → **Custom Domains** → **Add Custom Domain**.
2. أدخل النطاق، مثل `school.example.com`.
3. أضِف سجل CNAME عند مزوّد النطاق كما يطلب Render.
4. بعد التحقق، أضِف النطاق إلى المتغيّرات:

```
DJANGO_ALLOWED_HOSTS = schoolplatform.onrender.com,school.example.com
DJANGO_CSRF_TRUSTED_ORIGINS = https://schoolplatform.onrender.com,https://school.example.com
```

5. بعد 24 ساعة من عمل النطاق بثبات:

```
DJANGO_SECURE_HSTS_SECONDS = 31536000
```

> ⚠️ HSTS يُخبر المتصفح ألا يتصل بموقعك إلا عبر HTTPS لمدة سنة. لا تفعّله قبل أن يتأكد أن شهادة النطاق تعمل، وإلا سيتعذّر الوصول مؤقتاً.

---

## الخطوة 7 — منع نوم الخدمة

Render يوقف الخدمة المجانية بعد 15 دقيقة بلا زيارات، فيأخذ أول طلب بعدها 30–60 ثانية.

**الحل:** خدمة ping خارجية كل 12 دقيقة.

1. افتح <https://cron-job.org> أو <https://uptimerobot.com> (مجاناً).
2. أنشئ مهمة:
   - **URL:** `https://schoolplatform.onrender.com/`
   - **كل:** 12 دقيقة
3. لا تستخدم 5 دقائق ولا أقل.

> **سبب الـ 12 دقيقة:** Neon يمنح 100 ساعة حساب شهرياً. Ping كل 5 دقائق يستهلك ~720 ساعة، أي تُستنفد الحصة في ~16 يوماً. كل 12 دقيقة ≈ 60 ساعة فقط.
> بديل أفضل: أوقف الـ ping ليلاً (مثلاً 7 صباحاً – 7 مساءً) إن كانت المدرسة لا تحتاجه.

---

## الخطوة 8 — قائمة التحقق النهائية

- [ ] الموقع يفتح على `https://` وسهم القفل ظاهر.
- [ ] تسجيل الدخول برمز `SYS...` يعمل.
- [ ] رفع صورة شخصية يعمل، والصورة تظهر بعد إعادة النشر (تعني أن S3 مضبوط).
- [ ] إنشاء طالب من لوحة الإدارة يعمل.
- [ ] تسجيل غياب وحضور يعمل.
- [ ] `/admin/` يفتح لك فقط.
- [ ] لا توجد أسرار في GitHub (افحص أن `.env` غير مرفوع).

---

## استكشاف الأخطاء

| الرسالة | السبب | الحل |
|---|---|---|
| `DJANGO_SECRET_KEY must be set...` | المفتاح فارغ أو يبدأ بـ `django-insecure-` | ضع مفتاحاً عشوائياً طويلاً |
| `DJANGO_ALLOWED_HOSTS must list at least one host.` | المتغيّر فارغ | ضع `schoolplatform.onrender.com` |
| `DATABASE_URL must point to...` | لم تُضِف قاعدة البيانات | أضِف رابط Neon |
| `DisallowedHost` | نطاقك غير موجود في `DJANGO_ALLOWED_HOSTS` | أضِفه وأعِد النشر |
| `CSRF verification failed` | نطاقك غير موجود في `DJANGO_CSRF_TRUSTED_ORIGINS` | أضِفه بالصيغة `https://...` |
| `relation "..." does not exist` | لم تُنفَّذ الترحيلات | تأكد أن `migrate` داخل Start Command |
| الصور تختفي بعد كل نشر | S3 غير مضبوط | راجع الخطوة 2 ثم أعد النشر |
| الخدمة تبطؤ أول طلب | نوم Render المجاني | فعّل ping كل 12 دقيقة |
| `too many connections` من Neon | عدة عمليات بلا pooling | تأكد من استخدام رابط `-pooler` |

---

## الأمان بعد النشر

1. **غيّر كلمة مرور المدير** فوراً إن استخدمت كلمة مؤقتة.
2. **لا تشارك** `DJANGO_SECRET_KEY` ولا مفاتيح S3.
3. **لا ترفع** `.env` إلى GitHub.
4. **النسخ الاحتياطي:** Neon يحتفظ بنقطة استعادة (Restore) لعدة أيام في الخطة المجانية. للنسخ اليدوي:

```powershell
pg_dump "postgresql://...neon.tech/neondb?sslmode=require" -Fc -f backup.dump
```

5. **قبل أي ترقية كبيرة** خذ نسخة احتياطية، لأن `migrate` يعمل تلقائياً عند كل نشر.

---

## ملاحظات على القيود المجانية

- **Render:** 512MB RAM، عملية Gunicorn واحدة بـ 4 خيوط. كافٍ لمدرسة متوسطة (عشرات المستخدمين المتزامنين).
- **Neon:** عند تجاوز 100 ساعة حساب، تتوقف الحوسبة حتى الشهر التالي (البيانات تبقى سليمة).
- **الملفات الثابتة (CSS/JS):** تُخدَم عبر WhiteNoise من داخل التطبيق، لا تحتاج خدمة خارجية.
- **البريد الإلكتروني:** الإرسال غير مضبوط افتراضياً. استعادة كلمة المرور يدوياً من لوحة الإدارة إلى أن تُضيف مزوّد بريد مجاني.

---

## ترقية لاحقة (اختيارية)

| ما تريد | الحل |
|---|---|
| خدمة لا تنام | Render Starter بـ 7$/شهر أو Fly.io |
| قاعدة بيانات أكبر | Neon Launch |
| بريد إلكتروني للمستخدمين | Resend أو Brevo (مجاني محدود) |
| نسخ احتياطي تلقائي | GitHub Actions + `pg_dump` |
