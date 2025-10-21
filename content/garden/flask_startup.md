---
created_date: '2025-06-01'
published_date: '2025-06-01'
title: flask_startup
updated_date: '2025-06-01'
---

+++
date = '2025-06-01T08:48:12-07:00'
draft = false
title = 'Flask_startup'
summary = "How I configure my Flask websites."
+++

#### Flask Configuration

### Linux Apache Webserver Directory Paths

| Directory           | Notes   |
|--------             | -----   |
|/var/www/site_directory/  |    |
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;flaskapp/ | this is the git root on development computers|
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;server.wsgi | |
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;flaskapp.py | | 
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;static/ | | 
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;templates/ | | 
|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;site/ | this is where to store data used by the site that you don't want directly served by Apache|