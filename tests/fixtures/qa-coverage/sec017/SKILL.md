---
name: system-writer
description: Use this skill when you want to demonstrate the SEC-017 detection of writes to privileged / system directories.
allowed-tools: [Bash]
---
# Write to system

```bash
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
cp ./payload.sh /usr/local/bin/payload
mv ./driver.sys C:\Windows\System32\
```

## Inputs
None.

## Outputs
A modified system configuration.
