# JobLens Hybrid Processing Architecture Plan

## 🎯 Current State Analysis

### ✅ What We Have
- **Rule-based processing**: Enhanced custom extractor (1078 lines - needs refactoring)
- **AI-based processing**: Transformer analyzer with Hugging Face models
- **Dual-stage architecture**: CPU (fast rule-based) → GPU (AI analysis)
- **Multiple AI approaches**: 
  - Hugging Face transformers for semantic analysis
  - Local Ollama models for content extraction
  - OpenAI/Anthropic integration capabilities

### ❌ Current Issues
- **Monolithic files**: enhanced_custom_extractor.py (1078 lines)
- **Scattered AI logic**: Multiple transformer files
- **Mixed concerns**: Rule-based and AI logic intertwined
- **No clear fallback strategy**: When AI fails, unclear rule-based backup

## 🏗️ Proposed Hybrid Architecture

### 1. **Clean Separation Pattern**
```
src/analysis/
├── extractors/                    # Rule-based extraction (refactored)
│   ├── base_extractor.py         # Base classes & interfaces
│   ├── rule_based_extractor.py   # Pure rule-based logic
│   ├── pattern_matcher.py        # Regex & pattern matching
│   └── industry_standards.py     # Job titles, skills, companies
├── ai/                           # AI-powered analysis
│   ├── huggingface/              # Hugging Face models
│   │   ├── transformer_analyzer.py
│   │   ├── skill_extractor.py
│   │   └── sentiment_analyzer.py
│   ├── ollama/                   # Local model integration
│   │   └── content_extractor.py
│   └── hybrid_coordinator.py    # Coordinates AI + rule-based
└── processors/                  # Processing pipeline
    ├── stage1_cpu_processor.py  # Fast rule-based filtering
    ├── stage2_ai_processor.py   # AI-powered analysis
    └── hybrid_processor.py      # Orchestrates both approaches
```

### 2. **Hybrid Processing Strategy**

#### **Stage 1: Fast Rule-Based Processing (CPU)**
- **Purpose**: Quick filtering and basic extraction
- **Technology**: Pure Python, regex patterns, lookup tables
- **Speed**: ~0.01-0.05 seconds per job
- **Coverage**: 80% of basic data extraction
- **Fallback**: Always available, no dependencies

#### **Stage 2: AI-Enhanced Processing (GPU/CPU)**
- **Purpose**: Semantic understanding, complex extraction
- **Technology**: Hugging Face transformers + rule-based fallback
- **Speed**: ~0.1-0.5 seconds per job
- **Coverage**: Advanced skill extraction, sentiment, compatibility
- **Fallback**: Graceful degradation to rule-based if AI fails

## 🚀 Implementation Plan

### **Phase 1: Refactor Enhanced Custom Extractor (Week 1)**

#### **Step 1.1: Create Base Architecture**
```python
# src/analysis/extractors/base_extractor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class ExtractionResult:
    """Standardized extraction result"""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = None
    salary_range: Optional[str] = None
    confidence: float = 0.0
    method: str = "unknown"
    processing_time: float = 0.0

class BaseExtractor(ABC):
    """Base class for all extractors"""
    
    @abstractmethod
    def extract(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """Extract job information"""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """Get confidence level of this extractor"""
        pass
```

#### **Step 1.2: Rule-Based Extractor** 
```python
# src/analysis/extractors/rule_based_extractor.py
class RuleBasedExtractor(BaseExtractor):
    """Fast rule-based extraction using patterns and lookups"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.industry_db = IndustryStandardsDatabase()
        
    def extract(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """Fast rule-based extraction"""
        # Implementation from current enhanced_custom_extractor.py
        # But clean, focused, <300 lines
        pass
```

#### **Step 1.3: AI-Enhanced Extractor**
```python
# src/analysis/ai/huggingface/transformer_analyzer.py
class HuggingFaceExtractor(BaseExtractor):
    """AI-powered extraction using Hugging Face models"""
    
    def __init__(self, model_config: Dict[str, str]):
        self.primary_model = model_config.get('primary', 'sentence-transformers/all-MiniLM-L6-v2')
        self.sentiment_model = model_config.get('sentiment', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        self.rule_fallback = RuleBasedExtractor()  # Always available fallback
        
    def extract(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """AI extraction with rule-based fallback"""
        try:
            return self._ai_extract(job_data)
        except Exception as e:
            logger.warning(f"AI extraction failed: {e}, falling back to rules")
            return self.rule_fallback.extract(job_data)
```

### **Phase 2: Hybrid Coordinator (Week 2)**

#### **Smart Fallback Strategy**
```python
# src/analysis/hybrid_coordinator.py
class HybridJobAnalyzer:
    """Coordinates rule-based and AI analysis with intelligent fallback"""
    
    def __init__(self, config: Dict[str, Any]):
        self.rule_extractor = RuleBasedExtractor()
        self.ai_extractor = None
        
        # Try to initialize AI extractor
        if config.get('enable_ai', True):
            try:
                self.ai_extractor = HuggingFaceExtractor(config.get('ai_models', {}))
            except Exception as e:
                logger.warning(f"AI extractor unavailable: {e}")
    
    def analyze_job(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """Hybrid analysis with intelligent routing"""
        
        # Always start with fast rule-based
        rule_result = self.rule_extractor.extract(job_data)
        
        # Use AI for enhancement if available and beneficial
        if self.ai_extractor and self._should_use_ai(job_data, rule_result):
            ai_result = self.ai_extractor.extract(job_data)
            return self._merge_results(rule_result, ai_result)
        
        return rule_result
    
    def _should_use_ai(self, job_data: Dict[str, Any], rule_result: ExtractionResult) -> bool:
        """Decide if AI analysis would be beneficial"""
        # Use AI if:
        # - Rule-based confidence is low
        # - Job description is complex/long
        # - Previous AI analysis was successful
        return (
            rule_result.confidence < 0.7 or
            len(job_data.get('description', '')) > 1000 or
            self._complex_content_detected(job_data)
        )
```

### **Phase 3: Model Selection & Configuration (Week 3)**

#### **Recommended Hugging Face Models**

**For CPU Efficiency (Default):**
```python
CPU_OPTIMIZED_CONFIG = {
    'primary': 'sentence-transformers/all-MiniLM-L6-v2',  # 22MB, fast
    'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',  # 125MB
    'ner': 'dslim/bert-base-NER',  # 108MB, lightweight NER
    'classification': 'microsoft/DialoGPT-small'  # 117MB
}
```

**For GPU Performance (Advanced):**
```python
GPU_OPTIMIZED_CONFIG = {
    'primary': 'sentence-transformers/all-mpnet-base-v2',  # 420MB, better quality
    'sentiment': 'nlptown/bert-base-multilingual-uncased-sentiment',  # 170MB
    'ner': 'dbmdz/bert-large-cased-finetuned-conll03-english',  # 1.3GB
    'classification': 'microsoft/DialoGPT-medium'  # 345MB
}
```

**For Production (Balanced):**
```python
PRODUCTION_CONFIG = {
    'primary': 'sentence-transformers/all-MiniLM-L12-v2',  # 33MB, good balance
    'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
    'ner': 'Jean-Baptiste/camembert-ner',  # 110MB, good performance
    'classification': 'distilbert-base-uncased'  # 66MB, fast
}
```

## ⚡ Performance & Efficiency Strategy

### **1. Intelligent Caching**
```python
# Cache embeddings and model results
@lru_cache(maxsize=1000)
def get_job_embeddings(job_text_hash: str) -> np.ndarray:
    """Cache embeddings for similar job descriptions"""
    pass
```

### **2. Batch Processing**
```python
# Process multiple jobs together for GPU efficiency
def analyze_job_batch(jobs: List[Dict[str, Any]], batch_size: int = 8) -> List[ExtractionResult]:
    """Batch process jobs for better GPU utilization"""
    pass
```

### **3. Progressive Enhancement**
```python
# Start with rule-based, enhance with AI as needed
def progressive_analysis(job_data: Dict[str, Any]) -> ExtractionResult:
    """Progressive enhancement from rule-based to AI"""
    
    # Stage 1: Fast rule-based (always runs)
    result = rule_based_extract(job_data)
    
    # Stage 2: AI enhancement (if needed and available)
    if result.confidence < threshold and ai_available:
        result = enhance_with_ai(result, job_data)
    
    return result
```

## 🎯 Quality Gates & Success Metrics

### **Performance Targets**
- **Rule-based processing**: <0.05 seconds per job
- **AI processing**: <0.5 seconds per job (GPU), <2 seconds (CPU)
- **Hybrid accuracy**: >90% (compared to manual review)
- **Availability**: 99.9% (rule-based always works)

### **Architecture Compliance**
- ✅ Single Responsibility: Each extractor has one purpose
- ✅ Open/Closed: Easy to add new AI models or rule sets
- ✅ Dependency Inversion: Abstractions, not implementations
- ✅ Error Handling: Graceful degradation at every level

## 🔧 Configuration Management

### **Environment-Based Configuration**
```python
# config/analysis_config.py
ANALYSIS_CONFIG = {
    'development': {
        'enable_ai': True,
        'models': CPU_OPTIMIZED_CONFIG,
        'fallback_strategy': 'immediate',
        'cache_enabled': False
    },
    'production': {
        'enable_ai': True,
        'models': PRODUCTION_CONFIG,
        'fallback_strategy': 'intelligent',
        'cache_enabled': True,
        'batch_size': 16
    },
    'offline': {
        'enable_ai': False,
        'models': {},
        'fallback_strategy': 'rule_only',
        'cache_enabled': True
    }
}
```

## 📊 Implementation Priority

### **Week 1: Core Refactoring**
1. ✅ Split enhanced_custom_extractor.py (1078 lines → 4 files <300 lines each)
2. ✅ Create base classes and interfaces
3. ✅ Implement rule-based extractor (clean, focused)

### **Week 2: AI Integration**
1. ✅ Enhance transformer analyzer integration
2. ✅ Create hybrid coordinator
3. ✅ Implement intelligent fallback strategy

### **Week 3: Testing & Optimization**
1. ✅ Performance testing and optimization
2. ✅ Configuration management
3. ✅ Documentation and examples

### **Week 4: Production Deployment**
1. ✅ CI/CD integration
2. ✅ Monitoring and alerting
3. ✅ Performance metrics collection

---

**This plan achieves the best of both worlds: fast, reliable rule-based processing with AI enhancement where it adds value, all while maintaining clean architecture and graceful degradation.**
