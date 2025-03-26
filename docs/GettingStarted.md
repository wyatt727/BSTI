---
layout: default
title: Getting Started
nav_order: 2
---

# 🚀 Getting Started

### Prerequisites

Since BSTI v1.2 - ADB (Android Debug Bridge) is now required.

* https://developer.android.com/tools/adb

To take screenshots, wkhtmltopdf is required:

#### Windows

* https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe

#### MacOS

* https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg

#### Debian based OS

```bash 
sudo apt update && sudo apt install wkhtmltopdf -y
```

### 💻 Installation
> previously the recommended install was via venv - this is no longer the case and should be installed system-wide if possible.

Install the required Python packages:


``` bash
pip install -r requirements.txt
```