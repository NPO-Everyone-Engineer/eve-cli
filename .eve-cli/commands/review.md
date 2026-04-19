---
description: Code review checklist
allowed-tools: [Read, Glob, Grep]
---
Please review the code in this project for:

1. **Security issues** - Check for hardcoded secrets, SQL injection risks, path traversal, etc.
2. **Performance problems** - Look for inefficient loops, unnecessary allocations, etc.
3. **Code style** - Check for consistency with PEP 8 (if Python) or project conventions
4. **Error handling** - Ensure proper exception handling and edge cases

Focus on the files that were recently modified or are most critical.
Provide specific line numbers and suggestions for improvement.
