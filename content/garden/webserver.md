---
created_date: '2025-02-14'
published_date: '2025-02-14'
title: webserver
updated_date: '2024-11-07'
---

+++
date = '2024-11-03T13:57:43-08:00'
draft = false
title = 'Webserver Configuration'
+++
## Webserver Configuration Checklist

### Site Setup

1. configure DNS
2. apache2/site-available/*.conf
3. Let's Encrypt
4. mkdir /var/www/`<site document root>`
5. populate `<site document root>` depending on application type
6. apachectl configtest
7. systemctl reload apache2

### Server Setup

1. apt install apache2
2. apt install libapache2-mod-wsgi-py3
3. apt install certbot python3-certbot-py3
4. a2enmod rewrite

### Certbot Setup

<b>[Certbot Documentation](https://certbot.eff.org/instructions?ws=apache&os=ubuntubionic&tab=wildcard)</b>

1. sudo snap install --classic certbot 
2. sudo snap set certbot trust-plugin-with-root=ok