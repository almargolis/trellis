---
created_date: '2025-02-14'
published_date: '2025-02-14'
title: couchdb
updated_date: '2025-01-01'
---

+++
date = '2024-12-31T20:02:54-08:00'
draft = false
title = 'Couchdb'
summary = "Getting Started with Couchdb"
+++

### Installation

CouchDb is not in the standard Debian or Ubuntu repositories. The official installation instructions are apparently out of date since at least Ubuntu 24.04. If you follow them, "apt update" will report a security issue. There are at least two issues: (1) Debian and/or Ubuntu have changed how source lists and PGP keys are managed and (2) as of 1/1/25 Apache has not gotten around to updating its published software for Ubuntu 24.04. I found other instructions that purport to be specific to Ubuntu 24.04 but they also failed.

[Official Non-Working Installation Instructions](https://docs.couchdb.org/en/stable/install/unix.html)

[Canonical has this resolved in a SNAP](https://snapcraft.io/couchdb)

I don't really like the idea of SNAP but several widely used packages, particularly Let's Encrypt, rely on them so I don't fight them very hard any longer.

[Make sure to follow Canonical's CouchDb directions](https://github.com/apache/couchdb-pkg/blob/main/README-SNAP.md)

The above give very strong hints as to how to configure Erlang and CouchDb but do require a fair amount of judgement and experience.

Since this was running on a Digital Ocean VM in a datacenter, I edited 

/var/snap/couchdb/current/etc/local.ini 

* to uncomment the bind address and change that to 0.0.0.0 
* and uncomment the admin user and assign it a reasonable password

and then

snap restart couchdb

which seemed to do nothing until I opened port 5984 on my firewall to get the CouchDb greeting dump in my browser.

I then tried 

http://0.0.0.0:5984/_utils/

Which wonderfully brought up the Futon login which I don't dare use until I figure out how to enable SSL. I also tried some curl command line requests and verified that worked.

I then searched for CouchDb ssl and security and found lots of questions and very few helpful sounding answers. I added letsencrypt.com to the search and found more of the same. CouchDb has built-in SSL support but certificates are complicated and apparently none of the big projects consider CouchDb important enough to provide specific support. The one success story I found was somebody using Nginx as a reverse proxy. I reset the CouchDb binding to 127.0.0.1 and verified that my remote access was disabled and then removed the firewall rule.

A quick search found

[Configuring Apache Reverse Proxy](https://www.howtogeek.com/devops/how-to-set-up-a-reverse-proxy-with-apache/)

Which was all I needed to get going. I followed the instructions with required adaptation, verified remote http access and then ran certbot to enable https. Bang!

Now onto React Native and PouchDb ...