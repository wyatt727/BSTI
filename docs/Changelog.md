---
layout: default
title: Changelog
nav_order: 7
---

# Changelog

## v0.1
- log viewer & session logging
- file transfer tab
- reworked menu bar
- reworked terminal to open in local terminal rather than browser
- BSTG and module search filter
- create new modules
- added useful links to homepage - bstg's specific nessus and plextrac for now
- fixed close tab UI bug 
- buffers for thread safety and increased performance
- screenshot logs
- remove ANSI codes from screenshot output
- file upload metadata
- added ssh key upload -> need to add section in readme
- tmux session attaching
- test if drone is up before connecting
- fixes to '_' being required instead of spaces for module descriptions
- NMB integrated fully
- tempfile used as execution script if edits are made, saving makes it permanent 
- n2p somewhat viable - no reportgen yet
- view nmb logs in the UI now
- pause button for nmb
- metadata for modules to map to nessus findings, then convert to md5 when saving the screenshot
- plugin_manager and create report functionality added
## v1.1
- fixed n2p import issue 
- added survilence and webapp tags 
- started zeus integration 
- added prefixes to survilence and webapp => prevents flawID from duplicating
- Potentially Unnecessary or Insecure Services added as plugin category
## v1.2
- fixed n2p bug with non-core custom fields 
- added full mobile testing support for workflows, automated scans, export in N2P format
- addons menu option to download apk-mitmv2 and zeus binaries per platform
- dropped all packages needing python3.9 - tested on 3.10 and working fine 
- added mobile tag support for n2p 
- android testing support tools, inspector, validator, decompiler etc.
- migrate docs to jekyll
- nuclei support
- client specifc configs db start and n2p support