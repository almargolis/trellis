---
created_date: '2025-02-14'
published_date: '2025-02-14'
title: hugo
updated_date: '2024-12-21'
---

+++
date = '2024-11-08T14:21:30-08:00'
draft = false
title = 'Hugo'
summary = 'My into to the HUGO static website generator.'
+++

### HUGO Static Site Generator

[HUGO website gohugo.io](https://gohugo.io)

Hugo seems to have a nice architecture but I am having trouble learning what I need to know in ts documentation.  At least partially because I seem to be interested in a different set of issues than many web folk.

The theme I am using is called [Digital Garden](https://themes.gohugo.io/themes/hugo-digital-garden-theme/). I like the general concept but find I am wanting to introduce lots of variation.

### Page Bundles

[HUGO documentation](https://gohugo.io/content-management/page-bundles/)

Websites inherently are a collection of pages in a hierarchy. It is often helpful to categorize groups of pages into sections of some kind. Hugo handles this really well. All content is in a ../content/.. directory. Each entry represents a page. Those directory entries can be either stand-alone files or directories. A directory can be either (1) a set of files that are composed to produce one page, called a leaf bundle, or (2) a collection of pages that constitute a subsection of the site, called a branch bundle. Both leaf bundles and branch bundles are call page bundles. The root ../content/.. directory is just a branch bundle with a minimum of automagical features. Branch bundles can contain branch bundles to any practical depth.

Leaf bundles must contain an index.md file with the main content of the page. The directory name is used as the url name of the webpage.

Branch bundles, except for the root, must contain an _index.md file that contains content at the root level of that branch / section, such as a directory of child pages. The directory name is used as the url name of the section webpage.

### Images

[HUGO documentation](https://gohugo.io/render-hooks/images/)

\!\[cutie\]\(cutie-in-warehouse.jpeg "My Robot!"\)

The image file name above is accessed from the current page bundle directory

### Cheatsheet

These are commands that I need help remembering. There is no attempt to make this comprehensive. Some of the examples are specific to my theme and configuration.

| Command                             | Description |
| ----------------                    | ----        |
| hugo                                | generate site |
| hugo server -D | generate site and launch test server. Include drafts with "-D".
| hugo new content garden/example.md  | create content skelton |