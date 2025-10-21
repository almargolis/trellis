---
created_date: '2025-02-14'
published_date: '2025-02-14'
title: javascript_orientation
updated_date: '2025-01-05'
---

+++
date = '2025-01-05T09:12:59-08:00'
draft = false
title = 'Javascript_orientation'
summary = 'Javascript Orientation'
+++
### What "Real" Programmers Need To Know About Javascript

Javascript can fool you. It fools me all the time.

Javascript looks like a normal programming language if you look at a one or two line example. By normal I mean **MY** favored languages like Python, C, BASIC and COBOL which all have strong, comprehensive designs that seem to be universally applied. Javascript on the other hand is a fluid mess. Almost any question you may ask has twenty different answers that generally arrive with little no guidance as two what contexts it applies to.

I have done my best to avoid as much of that mess as possible by doing as much processing on the server side as possible. That means that I could get away with learning about and using a very small subset of Javascript that works almost universally. That also means that my applications have a 1999 look and feel. That is satisfactory and potentially an advantage in accounting systems but probably isn't acceptable for the next "big thing".

It's now 2025 and I feel the need to write an application that runs natively on mobile devices. After hemming and hawing for a few years, I have finally accepted that React Native is the most viable tool for this project.

[My experiences of React Native vs Swift for iOS development](https://medium.com/@sam_ollason/react-native-vs-swift-ios-c144496f1519) does a good job explaining why from one perspective. My application is also IOS first and potentially Android never, so React Native's cross-platform capabilities are nice but not crucial for me. The Apple tools are all nicely designed and well structured but, for me, over controlled. As a developer I have my own quirks in how I work and think about programs and I would have to give up too much of that to use the Apple tools. I'd rather fight through the Javascript mess to find a development environment that works the way I do than conform to the Apple straightjacket.

If you have programmed in any other language, you should be able to look at javascript code and identify the basic language components like variables, operators, function declarations and function codes. If you know just a bit about parsers and programming language design you can probably make some pretty good guesses as to what even complex code does. You might also wonder why the developers didn't apply lessons learned about basic programming structuring in the 1970's.  

Aas you begin digging into heavy Javascript code, it would be a good idea to learn a bit about bundlers. [The What, Why and How of JavaScript bundlers](https://dev.to/sayanide/the-what-why-and-how-of-javascript-bundlers-4po9) provides a good overview of what they do. It seems that React Native development essentially requires a bundler called [Metro](https://metrobundler.dev)