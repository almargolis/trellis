---
created_date: '2025-02-14'
published_date: '2025-02-14'
title: building_an_app
updated_date: '2025-01-05'
---

+++
date = '2025-01-01T20:20:10-08:00'
draft = false
title = 'Building_an_app'
summary = "Building My First Mobile App With React Native and PouchDb"
+++
### Starting To Build

For step one I am just following a pattern:

[Building Offline First App in React Native using PouchDB and CouchDB](https://aboutreact.com/react-native-offline-app-using-pouchdb-couchdb/#google_vignette)

The first step of the build failed. The init command format in the article has been deprecated.

**npx @react-native-community/cli init <app name>**

Then 

npm install pouchdb-react-native --save

resulted in npn reporting a large number of critical vulnerabilities that I never was able to straighten out. I deleted the project, repeated the init then tried

npm install couchdb

which returned only a couple of moderate severity errors which were resolved with 

npm audit fix --force

Then I started to install following dependcies and discovered that

 npm install pouchdb-authentication

 was the major source of errors. I cleared those with uninstall and then 

 **STOP**

 There is no easy path here. I tried following several different articles, all of them provided a cascade of error messages. I even lost an hour of my life installing a Ruby Gem that was supposed to fix the Javascript. That had its own error messages that I had to fix on my way to getting a clean load of the Gem that, it turns out, did not actually solve the Javascript problem. I am taking a potentially long detour new to **REALLY** learn Javascript and React for browser applications and will pick up here as soon as possible. Look for articles regarding that journey to start appearing soon.