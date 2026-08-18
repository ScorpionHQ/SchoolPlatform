#!/usr/bin/env bash
# ==========================================================
#  SchoolPlatform - سكربت النشر الدائم (يُشغَّل على السيرفر)
#  الاستخدام:  sudo bash deploy/deploy.sh [اسم-النطاق]
#
#  يُنفَّذ على سيرفر Linux (Ubuntu/Debian):
#   1) يثبّت المتطلبات النظامية (nginx, python3-venv, gettext)
#   2) ينسخ المشروع إلى /opt/schoolplatform
#   3) ينشئ البيئة الافتراضية ويثبّت الحزم
#   4) يشغّل الترحيلات ويجمع الملفات الثابتة
#   5) يفعّل gunicorn كخدمة systemd
#   6) يهيّئ nginx ككوكيل عكسي مع HTTPS
#
#  يُعاد تشغيله بأمان في أي وقت للتحديث (idempotent).
# ==========================================================
set -euo pipefail

# ---------- المتغيرات ----------
APP_DIR="/opt/schoolplatform"
ENV_DIR="/etc/schoolplatform"
ENV_FILE="$ENV_DIR/.env"
LOG_DIR="/var/log/schoolplatform"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN="${1:-}"
WEB_USER="www-data"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "ERROR: شغّل السكربت بصلاحيات root:  sudo bash deploy/deploy.sh"
    exit 1
fi

# ---------- 1) المتطلبات النظامية ----------
echo "==> تثبيت المتطلبات النظامية"
export DEBIAN_FRONTEND=noninteractive
for pkg in python3-venv python3-pip gettext nginx; do
    if ! command -v "$pkg" >/dev/null 2>&1 && ! dpkg -s "$pkg" >/dev/null 2>&1; then
        apt-get update -y
        break
    fi
done
apt-get install -y python3-venv python3-pip gettext nginx rsync

if ! id "$WEB_USER" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$WEB_USER"
fi

# ---------- 2) نسخ المشروع ----------
echo "==> نسخ المشروع إلى $APP_DIR"
mkdir -p "$APP_DIR"
rsync -a --delete \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'db.sqlite3' \
    --exclude 'staticfiles' \
    --exclude 'media' \
    --exclude '.env' \
    "$SRC_DIR/" "$APP_DIR/"

# ---------- 3) ملف المتغيرات البيئية ----------
if [[ ! -f "$ENV_FILE" ]]; then
    echo "==> إنشاء $ENV_FILE (عدّله بالقيم الصحيحة ثم أعد التشغيل)"
    mkdir -p "$ENV_DIR"
    cp "$APP_DIR/deploy/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    chown root:"$WEB_USER" "$ENV_FILE"
    echo "!! لم يتم ضبط المتغيرات بعد: عدّل $ENV_FILE ثم شغّل السكربت مجدداً"
    exit 0
fi

if [[ -z "$DOMAIN" ]]; then
    DOMAIN="$(grep -E '^DOMAIN=' "$ENV_FILE" | head -n1 | cut -d= -f2)"
fi
if [[ -z "$DOMAIN" ]]; then
    echo "ERROR: حدد النطاق كوسيط أول أو عبر DOMAIN= في $ENV_FILE"
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# ---------- 4) البيئة الافتراضية + الحزم ----------
echo "==> تثبيت حزم Python"
cd "$APP_DIR"
if [[ ! -d venv ]]; then
    python3 -m venv venv
fi
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# ---------- 5) الترحيلات + الملفات الثابتة ----------
echo "==> تشغيل الترحيلات وجمع الملفات الثابتة"
mkdir -p "$LOG_DIR" "$APP_DIR/media"
chown -R "$WEB_USER":"$WEB_USER" "$LOG_DIR" "$APP_DIR/media" "$APP_DIR/staticfiles" 2>/dev/null || true
sudo -u "$WEB_USER" -E "$APP_DIR/venv/bin/python" manage.py migrate --noinput
sudo -u "$WEB_USER" -E "$APP_DIR/venv/bin/python" manage.py collectstatic --noinput

# ---------- 6) خدمة gunicorn ----------
echo "==> تفعيل خدمة gunicorn"
cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/schoolplatform.service
systemctl daemon-reload
systemctl enable schoolplatform.service
systemctl restart schoolplatform.service
systemctl --no-pager status schoolplatform.service | head -n 8

# ---------- 7) إعداد nginx ----------
echo "==> إعداد nginx"
NGINX_CONF="/etc/nginx/sites-available/schoolplatform"
sed -e "s/__DOMAIN__/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" > "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/schoolplatform
rm -f /etc/nginx/sites-enabled/default
if nginx -t; then
    systemctl reload nginx
else
    echo "!! فشل اختبار إعدادات nginx - راجع رسالة الخطأ أعلاه"
    exit 1
fi

# ---------- 8) شهادة SSL ----------
echo "==> شهادة SSL (Let's Encrypt)"
if ! command -v certbot >/dev/null 2>&1; then
    echo "جاري تثبيت certbot..."
    apt-get install -y certbot python3-certbot-nginx
fi
if [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    echo "تشغيل certbot (سيتطلب إدخال البريد الإلكتروني وتملك النطاق):"
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN"
else
    certbot renew --quiet
fi

# ---------- 9) الملخص ----------
echo ""
echo "============================"
echo " النشر اكتمل بنجاح"
echo "============================"
echo "  الرابط:    https://$DOMAIN/"
echo "  لوحة admin: https://$DOMAIN/$DJANGO_ADMIN_URL"
echo "  تحديث لاحق: sudo bash $APP_DIR/deploy/deploy.sh $DOMAIN"
echo "  سجلات:     journalctl -u schoolplatform -f"
echo "============================"
