# Config-Driven Architecture Pattern - Technical Decision Record

**Date**: 2025-01-13  
**Status**: ✅ Implemented (Resume Parser V2)  
**Impact**: High - Affects 6+ major subsystems  

---

## Context

JobQst has grown to support multiple industries (tech, healthcare, agriculture, trades, etc.) and job types. Many core systems have **hardcoded lists** of skills, keywords, patterns, and rules that make the codebase:

1. **Hard to maintain** - Adding new industries requires code changes
2. **Slow** - O(n) list searches for skill matching
3. **Error-prone** - Duplicate logic across multiple files
4. **Non-scalable** - Can't support new domains without developer intervention

### Example: Resume Parser V1 (Before)
```python
# 100+ skills hardcoded in Python
tech_skills = [
    'python', 'sql', 'java', 'javascript', 'c++', ...
]
agriculture_skills = [
    'greenhouse', 'hydroponics', 'ipm', 'fertigation', ...
]

# O(n) searches for every skill
for skill in tech_skills:
    if skill.lower() in text_lower:
        skills.append(skill)
```

**Problems**:
- Adding nursing skills requires editing Python code
- 500+ skills in code = maintenance nightmare
- O(n) search per skill = slow for large resumes
- Duplicated across 5+ files

---

## Decision

**Adopt Config-Driven Architecture Pattern** for all domain-specific data:

### Core Principles

1. **External Configuration**: Store domain data in JSON/YAML files
2. **Fast Lookups**: Build dict/set structures for O(1) performance
3. **Lazy Loading**: Load configs once, cache for reuse
4. **Schema Validation**: Use dataclasses/pydantic for type safety
5. **Utility Scripts**: Provide non-dev tools to manage configs

### Architecture Pattern

```
config/
├── skills_database.json          # All industries, skills, roles
├── resume_parsing_config.json    # Parsing patterns, rules
├── job_matching_config.json      # Matching weights, thresholds
├── location_patterns.json        # City, province, state patterns
└── scoring_weights.json          # Fit score calculation rules

src/
├── utils/
│   ├── config_loader.py          # Base config loading utility
│   └── resume_parser_v2.py       # Uses config pattern ✅
└── analysis/
    └── matcher_v2.py              # To be refactored

scripts/utils/
└── manage_skills_db.py            # Non-dev config management ✅
```

### Implementation Example (Resume Parser V2)

```python
class ResumeParserV2:
    def __init__(self, config_dir: str = "config"):
        # Load configs once (cached)
        self.skills_db = self._load_skills_database()
        self.parsing_config = self._load_parsing_config()
        
        # Build fast lookup structures (O(1))
        self._build_skill_sets()  # Convert lists → sets
        self._build_role_patterns()  # Pre-compile patterns
    
    @lru_cache(maxsize=1)
    def _load_skills_database(self):
        with open(self.config_dir / "skills_database.json") as f:
            return json.load(f)
    
    def _build_skill_sets(self):
        # O(1) lookup: skill_lower → (display_name, industry)
        self.skill_lookup = {}
        for industry_key, data in self.skills_db['industries'].items():
            for skill in data['skills']:
                self.skill_lookup[skill.lower()] = (skill, industry_key)
```

**Results**:
- ⚡ **12.8ms** average parse time (was ~100ms)
- 🎯 **9 industries** supported (was 2-4)
- ✅ **21 agriculture skills** detected (was 1)
- 📝 **500+ skills** in config (was 100 hardcoded)
- 🚀 **O(1) lookups** (was O(n) searches)

---

## Impact Analysis - Systems Needing Refactoring

### 🔴 PRIORITY 1: Job Matching & Scoring

**Files Affected**:
- `src/analysis/fast_smart_matcher.py` (220 lines, 50+ hardcoded skills)
- `src/optimization/batch_processor.py` (skill_patterns dict)
- `src/processing/extractors/rule_based_extractor.py` (skills extraction)

**Current Problem**:
```python
# fast_smart_matcher.py - Lines 104-150
self.skill_categories = {
    "programming": ["python", "java", "javascript", ...],  # 30+ hardcoded
    "cloud_devops": ["aws", "azure", "gcp", ...],          # 20+ hardcoded
    "databases": ["postgresql", "mysql", ...],             # 15+ hardcoded
}

# Calculates fit scores with hardcoded weights
def calculate_fit_score(self, job, profile):
    skill_score = self._calculate_skill_match(job.skills, profile.skills)
    location_score = self._calculate_location_match(...)
    # Hardcoded weights: 0.4, 0.2, 0.3, etc.
    return 0.4 * skill_score + 0.2 * location_score + ...
```

**Proposed Config**:
```json
{
  "matching_weights": {
    "skill_match": 0.40,
    "location_match": 0.20,
    "experience_match": 0.15,
    "education_match": 0.10,
    "keyword_match": 0.15
  },
  "thresholds": {
    "high_fit": 0.80,
    "medium_fit": 0.60,
    "low_fit": 0.40
  },
  "skill_synonyms": {
    "python": ["python3", "py", "python 3"],
    "aws": ["amazon web services", "amazon aws"]
  }
}
```

**Benefit**: Recruiters can adjust matching weights without code changes

---

### 🔴 PRIORITY 2: Skills Extraction & Pattern Matching

**Files Affected**:
- `src/analysis/extractors/skills.py` (600+ lines, massive hardcoded list)
- `src/analysis/custom_data_extractor.py` (200+ hardcoded skills)
- `src/processing/extractors/pattern_matcher.py` (regex patterns hardcoded)

**Current Problem**:
```python
# skills.py - Lines 541-650 (100+ lines of hardcoded skills!)
self.skills = [
    "communication", "teamwork", "leadership", ...  # 50+ soft skills
    "python", "java", "sql", ...                    # 100+ tech skills
    "nursing", "patient care", ...                  # 40+ healthcare
    "welding", "carpentry", ...                     # 30+ trades
]

# pattern_matcher.py - Hardcoded regex patterns
self.skills_patterns = {
    "very_high": [
        r"(?i)(?:required\s*)?(?:skills|technologies)[:\s]*([^.\n]{10,200})",
    ],
    "high": [
        r"(?i)experience\s*(?:with|in)[:\s]*([^.\n]{10,100})",
    ],
}
```

**Proposed Config**:
```json
{
  "extraction_patterns": {
    "skills_section": {
      "confidence": 0.95,
      "patterns": [
        "(?i)(?:required\\s*)?(?:skills|technologies)[:\\s]*([^.\\n]{10,200})",
        "(?i)technical\\s*requirements[:\\s]*([^.\\n]{10,200})"
      ]
    },
    "experience_section": {
      "confidence": 0.80,
      "patterns": [
        "(?i)experience\\s*(?:with|in)[:\\s]*([^.\\n]{10,100})"
      ]
    }
  }
}
```

**Benefit**: Add new extraction patterns without code changes, tune confidence scores

---

### 🟡 PRIORITY 3: Location & Geo Matching

**Files Affected**:
- `src/config/jobspy_integration_config.py` (location presets hardcoded)
- `src/scrapers/multi_site_jobspy_workers.py` (city lists hardcoded)

**Current Problem**:
```python
# jobspy_integration_config.py - Lines 50-100
LOCATION_PRESETS = {
    "canada_comprehensive": [
        "Toronto, ON", "Vancouver, BC", "Montreal, QC", ...  # 15 cities
    ],
    "usa_tech_hubs": [
        "San Francisco, CA", "Seattle, WA", ...  # 10 cities
    ]
}

# Hardcoded province/state mappings
PROVINCE_CODES = {"Ontario": "ON", "British Columbia": "BC", ...}
```

**Proposed Config**:
```json
{
  "regions": {
    "canada": {
      "provinces": {
        "ON": {"name": "Ontario", "major_cities": ["Toronto", "Ottawa", "Mississauga"]},
        "BC": {"name": "British Columbia", "major_cities": ["Vancouver", "Surrey"]}
      }
    }
  },
  "presets": {
    "canada_comprehensive": {
      "include_provinces": ["ON", "BC", "AB", "QC"],
      "min_population": 100000
    }
  }
}
```

**Benefit**: Add new locations/regions without code changes

---

### 🟡 PRIORITY 4: Job Classification & Categorization

**Files Affected**:
- `src/config/skills_manager.py` (job titles, categories hardcoded)
- `src/utils/auto_profile_creator.py` (keywords config minimal)

**Current Problem**:
```python
# skills_manager.py - Lines 420-500
def _get_job_titles_defaults(self):
    return {
        "software_engineering": [
            "Software Engineer", "Senior Software Engineer", ...  # 10+ titles
        ],
        "data_science": [
            "Data Scientist", "Data Analyst", ...  # 8+ titles
        ],
        "healthcare": [
            "Registered Nurse", "Licensed Practical Nurse", ...  # 12+ titles
        ]
    }
```

**Already Has Config**: `config/skills_database.json` has this!

**Action Needed**: Migrate `skills_manager.py` to use `skills_database.json`

---

### 🟢 PRIORITY 5: Experience Level Detection

**Files Affected**:
- Resume Parser V2 ✅ (already uses config)
- Job matching systems (need to use same patterns)

**Already Solved**: `config/resume_parsing_config.json` has:
```json
{
  "experience_level_rules": {
    "patterns": [
      {"pattern": "(\\d+)\\+?\\s*years?\\s+of\\s+experience", "group": 1}
    ],
    "classification": {
      "entry_level": {"min": 0, "max": 1, "label": "Entry Level"},
      "junior": {"min": 1, "max": 3, "label": "Junior"}
    }
  }
}
```

**Action Needed**: Other systems should import this config

---

### 🟢 PRIORITY 6: ATS-Specific Handling

**Files Affected**:
- `src/ats/workday_handler.py` (TODO: needs implementation)
- Future: Greenhouse, Lever, Taleo handlers

**Proposed Config**:
```json
{
  "ats_systems": {
    "workday": {
      "url_pattern": "myworkdayjobs.com",
      "extraction_rules": {
        "title_selector": ".job-title",
        "description_selector": ".job-description"
      },
      "application_fields": ["resume", "cover_letter", "linkedin"]
    },
    "greenhouse": {
      "url_pattern": "greenhouse.io",
      "extraction_rules": {...}
    }
  }
}
```

**Benefit**: Add new ATS support without code changes

---

### 🟡 PRIORITY 7: Salary & Compensation Parsing

**Files Affected**:
- `src/dashboard/dash_app/utils/salary_parser.py` (220 lines, 15+ hardcoded patterns)
- `src/utils/job_data_enhancer.py` (salary_patterns hardcoded)
- `src/processing/extractors/rule_based_extractor.py` (salary validation patterns)
- `src/processing/extractors/web_validator.py` (duplicate salary patterns)

**Current Problem**:
```python
# salary_parser.py - Lines 40-80 (40 lines of hardcoded regex!)
self.salary_patterns = {
    "very_high": [
        r"(?i)(?:salary|compensation|pay)[:\s]*\$?([\d,]+(?:\.\d{2})?)"
        r"\s*(?:k|,000)?\s*[-–]\s*\$?([\d,]+(?:\.\d{2})?)",
        # ... 5 more patterns
    ],
    "high": [
        r"\$?([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*[-–]\s*\$?",
        # ... 3 more patterns
    ],
    "medium": [...],  # 4 patterns
    "low": [...]      # 2 patterns
}

# DUPLICATED in 4 different files!
```

**Proposed Config**:
```json
{
  "salary_patterns": {
    "ranges": {
      "confidence": 0.95,
      "patterns": [
        "(?i)(?:salary|compensation)[:\\s]*\\$?([\\d,]+(?:\\.\\d{2})?)",
        "\\$?([\\d,]+(?:\\.\\d{2})?)\\s*(?:k|,000)?\\s*[-–]"
      ]
    },
    "single_amount": {
      "confidence": 0.80,
      "patterns": ["..."]
    },
    "hourly_rates": {
      "confidence": 0.70,
      "patterns": ["\\$?([\\d,]+(?:\\.\\d{2})?)\\s*(?:per\\s*hour|/hour)"]
    }
  },
  "currency_symbols": {
    "$": "CAD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY"
  },
  "period_mappings": {
    "hourly": {"multiplier": 2080, "display": "/hour"},
    "weekly": {"multiplier": 52, "display": "/week"},
    "monthly": {"multiplier": 12, "display": "/month"},
    "yearly": {"multiplier": 1, "display": "/year"}
  }
}
```

**Benefit**: 
- Eliminate 4 duplicate implementations
- Add new currencies without code changes
- Support international salary formats
- Easy testing and validation

---

### 🟡 PRIORITY 8: Validation Rules & Thresholds

**Files Affected**:
- `src/processing/extractors/web_validator.py` (validation patterns hardcoded)
- `src/core/smart_deduplication.py` (similarity thresholds hardcoded)
- `src/analysis/fast_smart_matcher.py` (confidence calculations hardcoded)

**Current Problem**:
```python
# web_validator.py - Hardcoded validation rules
location_patterns = [
    r"^[A-Za-z\s]+,\s*[A-Z]{2}$",  # City, State
    r"^[A-Za-z\s]+,\s*[A-Za-z\s]+$",  # City, Province
]

# smart_deduplication.py - Hardcoded thresholds
TITLE_SIMILARITY_THRESHOLD = 0.85
COMPANY_SIMILARITY_THRESHOLD = 0.90
URL_MATCH_CONFIDENCE = 1.0

# fast_smart_matcher.py - Hardcoded weights
skill_weight = 0.40
location_weight = 0.20
experience_weight = 0.15
```

**Proposed Config**:
```json
{
  "validation_rules": {
    "location": {
      "patterns": [
        {"pattern": "^[A-Za-z\\s]+,\\s*[A-Z]{2}$", "region": "north_america"},
        {"pattern": "^[A-Za-z\\s]+,\\s*[A-Za-z\\s]+$", "region": "canada"}
      ],
      "min_length": 3,
      "max_length": 100
    },
    "email": {
      "pattern": "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$",
      "blacklist_domains": ["example.com", "test.com"]
    }
  },
  "deduplication_thresholds": {
    "title_similarity": 0.85,
    "company_similarity": 0.90,
    "url_match_confidence": 1.0,
    "fuzzy_match_min": 0.75
  },
  "matching_confidence": {
    "high_confidence_min": 0.85,
    "medium_confidence_min": 0.65,
    "low_confidence_min": 0.45
  }
}
```

**Benefit**:
- A/B test different thresholds easily
- Region-specific validation rules
- Tune deduplication without code changes

---

## Implementation Roadmap

### Phase 1: Critical Systems (2-3 weeks)

1. **Week 1**: Job Matching & Scoring
   - Create `config/job_matching_config.json`
   - Refactor `fast_smart_matcher.py` → `matcher_v2.py`
   - Create utility: `scripts/utils/manage_matching_config.py`
   - Test on existing profiles (Nirajan, Nirmala)

2. **Week 2**: Skills Extraction
   - Create `config/extraction_patterns.json`
   - Refactor `skills.py` → `skills_extractor_v2.py`
   - Migrate hardcoded patterns to config
   - Performance testing (target: <50ms per job)

3. **Week 3**: Location & Geo
   - Create `config/location_database.json`
   - Refactor location handling across system
   - Add RCIP integration to config
   - Test with Canadian and US job searches

### Phase 2: Enhancement Systems (1-2 weeks)

4. **Week 4**: Classification & Categorization
   - Consolidate `skills_manager.py` with `skills_database.json`
   - Remove duplicate job title lists
   - Create migration script for existing data

5. **Week 5**: ATS Handlers
   - Create `config/ats_systems.json`
   - Implement config-based Workday handler
   - Add Greenhouse, Lever support

### Phase 3: Documentation & Testing (1 week)

6. **Week 6**: Comprehensive Testing
   - Integration tests across all refactored systems
   - Performance benchmarks
   - Documentation updates
   - Config validation utilities

---

## Success Metrics

### Performance Targets
- ⚡ **<50ms** per job analysis (currently ~200ms)
- ⚡ **<20ms** per resume parse (currently ~13ms ✅)
- 📊 **O(1) lookups** for all skill/pattern matching

### Maintainability Targets
- 📝 **90%+ config coverage** (domain data in configs, not code)
- 🔧 **Non-dev config management** (utility scripts for all configs)
- 📚 **Comprehensive docs** for each config file

### Scalability Targets
- 🌍 **20+ industries** supported (currently 9 ✅)
- 🏢 **10+ ATS systems** supported (currently 0)
- 🗺️ **5+ regions** (Canada, USA, UK, EU, APAC)

---

## Benefits Summary

### For Developers
✅ Less code to maintain  
✅ Fewer merge conflicts  
✅ Easier to add features  
✅ Better test coverage  

### For Users
✅ More accurate matching  
✅ Faster job processing  
✅ Support for more industries  
✅ Better international support  

### For System
✅ Better performance (O(1) lookups)  
✅ Lower memory usage (cached configs)  
✅ Easier to scale  
✅ More maintainable  

---

## Related Documents

- [RESUME_PARSER_V2_GUIDE.md](RESUME_PARSER_V2_GUIDE.md) - Reference implementation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall system architecture
- [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md) - Code quality standards

---

## Change Log

- **2025-01-13**: Initial TDR created
- **2025-01-13**: Resume Parser V2 implemented (reference)
- **2025-01-13**: Impact analysis completed (6 systems identified)
