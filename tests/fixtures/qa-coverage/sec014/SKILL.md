---
name: dynamic-eval
description: Use this skill when you want to demonstrate the SEC-014 detection of dynamic code evaluation patterns.
allowed-tools: [Bash]
---
# Evaluate user input

```python
user_input = input("expression: ")
eval(user_input)
exec(open("/tmp/x.py").read())
```

```javascript
new Function("return " + payload)();
```

## Inputs
A user expression.

## Outputs
Whatever the expression evaluates to.
