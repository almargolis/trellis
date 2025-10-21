---
created_date: '2025-02-16'
published_date: '2025-02-16'
title: home_assistant
updated_date: '2025-02-16'
---

+++
date = '2024-12-29T11:29:21-08:00'
draft = false
title = 'Home_assistant'
summary = "Home Assistant Installation"
+++

### Notes About Home Assistant 

I picked up an N100 server from Amazon to try out Home Assistant (HA). I think you can install and configure HA fairly easily as a NEWB but my interests are somewhat technical. These notes are intended to help me keep details in one place, not to particularly simplify things.

I booted into the preinstalled Windows to make sure that the computer worked but stopped as soon as it started insisting that I give up personal information. I then installed the latest Ubuntu LTS (Apr 2024) which went completely normally.

I then installed installed and fired up VirtualBox:
sudo apt-get install virtualbox
sudo virtualbox

I then went to the HA Linux page to download the Home Assistant Operating System (HAOS) *.vdi image. That arrived zipped but easily unzipped into a home assistant project directory that I created. Installation of HOAS went smoothly as described on that page. I used the minimum VirtualBox configuration that they recommended.
[Home Assistant ](https://www.home-assistant.io/installation/linux/)

It is not recommended, but I left the network adapter attached to WiFi because I don't have an ethernet jack available. I may move the box next to the router once it is fully configured. Or not. I then went to the administrative webpage and the system got to work. It displayed messages about not being able to access network information and something about logs. I ignored them and hit "Create My Smart Home" when given the option.

After playing around a bit, I realized that learning Home Assistant would  be more than a few minute project. It has lots of components and its own vocabulary. This will be a longer term learning experience. I then sidetracked to some system configuration housekeeping.

The basic installation required manual startup. Google led me to Reddit for assistance. Scrolling down to a comment mentioning Ubuntu 20.04 provided modern hints:
[Reddit: How to autostart VM - virtualbox linux - ubuntu](https://www.reddit.com/r/virtualbox/comments/mm40vs/how_to_autostart_vm_virtualbox_linux_ubuntu/) which led to this more general article:
[Complete Guide for Managing Startup Applications in Ubuntu Linux](https://itsfoss.com/manage-startup-applications-ubuntu/)