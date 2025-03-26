---
layout: default
title: Mobile
nav_order: 8
---

# Intro

As of version 1.2 of BSTI mobile testing is officially supported, including static and dynamic analysis.

# Features
- static analysis with mobsf intigration 
- dynamic analysis with drozer
- decompile apks in both smali and java code
- parse apk for secrets 
- automatic screenshots based on android manifest
- export mobsf reports as csv in format that nessus2plextrac expects - filter out false positives as you go

# Usage

## Automated testing - Mobsf
For mobsf scans, simply navigate to the "Mobile Testing tab" and select the "Automated Testing" subtab

From here, you can right click any item to exclude it from the final export, you can also double click any item for more information on the finding.

Once you're finished with your changes, click the export report button to save the report in a location of your choice.

## Workflows
Repeat tasks can be easily executed via the workflow subtab - for actions such as ssl pinning bypass and installing drozer.

Note: this section is not a finished product and will be improved in future updates.

## Inspector
Easily view the android manifest of the most recently scanned mobile application - will auto populate upon scan completion

## Validator
Takes an android manifest as input, takes screenshots of findings and highlights the affected areas - an example of this is below.

## Decompiler
Provide an apk file and BSTI will decompile the application in both smali and java formats, you can then view and edit the files if you prefer.

## APK Secrets 
Parse an apk for secret items such as passwords, api-keys and other hardcoded sensitive information.

## Dynamic Testing - Drozer
Conduct dynamic testing against a loaded application. For more info on drozer please see: https://labs.withsecure.com/tools/drozer

