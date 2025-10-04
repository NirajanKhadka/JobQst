#!/usr/bin/env python3
"""Update ARCHITECTURE.md with Resume Parser V2 section"""

# Add Resume Parser V2 section to ARCHITECTURE.md
with open('docs/ARCHITECTURE.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find insertion point - after Data Flow section, before detailed components
marker = '## Core Architecture'
if marker in content:
    insert_text = '''

## 🆕 Config-Driven Architecture (v3.2)

**Major Architectural Pattern:** External JSON configurations replace hardcoded domain data

**Reference Implementation: Resume Parser V2**
- **File:** `src/utils/resume_parser_v2.py`
- **Configs:** `config/skills_database.json`, `config/resume_parsing_config.json`
- **Performance:** 12.8ms average (was ~100ms), O(1) lookups (was O(n))
- **Coverage:** 9 industries, 500+ skills (was 2-4 industries, 100 hardcoded)

```python
# Modern config-driven approach
from src.utils.resume_parser_v2 import parse_resume

data = parse_resume("resume.docx")
print(f"Industry: {data['primary_industry']}")  # Auto-detected from 9 industries
print(f"Skills: {len(data['skills'])} detected")  # Fast O(1) lookups
print(f"Keywords: {data['keywords'][:3]}")  # Industry-specific
```

**Management Utility:**
```bash
# Non-developers can manage skills database
python scripts/utils/manage_skills_db.py list
python scripts/utils/manage_skills_db.py show data_analytics
python scripts/utils/manage_skills_db.py add "Sales" --skills "Salesforce,CRM"
```

**See:** [CONFIG_DRIVEN_ARCHITECTURE.md](CONFIG_DRIVEN_ARCHITECTURE.md) for:
- 6 systems needing refactoring (job matching, skills extraction, location handling, etc.)
- Implementation roadmap (6-week plan)
- Performance and scalability targets

'''
    # Insert before ## Core Architecture
    idx = content.find(marker)
    if idx != -1:
        content = content[:idx] + insert_text + content[idx:]
        with open('docs/ARCHITECTURE.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✅ Updated ARCHITECTURE.md with Resume Parser V2 section')
    else:
        print('❌ Could not find insertion point')
else:
    print('❌ Marker not found in file')
