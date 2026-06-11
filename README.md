---
services: app-service\web,app-service
platforms: python
author: Stephen Mburu
---

# Data Capture Tool Hosted on Microsoft Azure App Service

This is a production application used by AFRO member countries to share data with WHO Regional Office for Africa iAHO Repository

The database connection information is specified via environment variables `DBHOST`, `DBPASS`, `DBUSER`, and `DBNAME`. This app always uses the default MariaDB port.

## Azure App Service deployment

The Linux App Service startup command should be:

```bash
bash startup.sh
```

The startup script sets `DJANGO_ENV=production`, runs `collectstatic`, and starts
Gunicorn. It does not run migrations automatically, so database changes remain a
separate controlled operation.

# Contributing

Development of this app has been guided by [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
