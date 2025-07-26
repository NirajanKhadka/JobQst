# OpenHermes 2.5 Setup Guide for AutoJobAgent

## 🎯 Overview

OpenHermes 2.5 is now configured as your **primary and exclusive** AI model for job analysis. This guide shows you how to set it up and use it effectively.

## 📋 Model Information

- **Model**: OpenHermes 2.5 (7B parameters)
- **Base**: Fine-tuned Mistral 7B by Teknium
- **Size**: 4.1GB (Q4_0 quantization)
- **Strengths**: Excellent instruction following, reasoning, and structured output
- **Template**: ChatML format with `<|im_start|>` and `<|im_end|>` tokens

## 🚀 Installation Steps

### Step 1: Install OpenHermes 2.5
```bash
# Pull the OpenHermes 2.5 model
ollama pull openhermes:v2.5

# Verify installation
ollama list

# Test the model
ollama run openhermes:v2.5
```

### Step 2: Start Ollama Service
```bash
# Start Ollama server
ollama serve

# Or start as background service (Linux/Mac)
sudo systemctl start ollama
sudo systemctl enable ollama

# Windows - run in background
start /B ollama serve
```

### Step 3: Verify Model is Working
```bash
# Test API endpoint
curl http://localhost:11434/api/tags

# Test generation
curl http://localhost:11434/api/generate -d '{
  "model": "openhermes:v2.5",
  "prompt": "Analyze this job: Python Developer position",
  "stream": false
}'
```

## ⚙️ Configuration Changes Made

### 1. **Primary Model Updated**
- **Before**: `mistral:7b`
- **After**: `openhermes:v2.5`

### 2. **Default Scores Updated**
- **Before**: `0.5` (neutral)
- **After**: `0.7` (more optimistic baseline)

### 3. **Files Updated**:
- `src/ai/enhanced_job_analyzer.py` - Primary analyzer
- `src/dashboard/enhanced_job_processor.py` - Job processor
- `src/ai/reliable_job_processor_analyzer.py` - Reliable analyzer

## 🔧 Model Configuration

### OpenHermes 2.5 Parameters:
```python
{
    "model": "openhermes:v2.5",
    "temperature": 0.3,      # Low for consistent analysis
    "max_tokens": 2048,      # Detailed responses
    "top_p": 0.9,           # High quality output
    "analysis_timeout": 30,  # 30 second timeout
    "stop": ["<|im_start|>", "<|im_end|>"]  # ChatML tokens
}
```

### Analysis Prompt Template:
```
<|im_start|>system
You are an expert job analysis AI powered by OpenHermes 2.5. Analyze job postings comprehensively and provide structured JSON output.
<|im_end|>
<|im_start|>user
CANDIDATE PROFILE:
- Skills: Python, SQL, Machine Learning, AWS
- Experience Level: Senior
- Location: Toronto, ON

JOB POSTING:
- Title: Senior Python Developer
- Company: TechCorp
- Location: Remote
- Description: [job description...]

Provide comprehensive analysis in JSON format...
<|im_end|>
<|im_start|>assistant
```

## 📊 Analysis Features

### What OpenHermes 2.5 Analyzes:

#### 1. **Salary Analysis**
```json
{
  "salary_analysis": {
    "extracted_range": "$80,000 - $120,000 CAD",
    "market_position": "above_average",
    "confidence": 0.85
  }
}
```

#### 2. **Experience Analysis**
```json
{
  "experience_analysis": {
    "level": "senior",
    "years_required": "5-7 years",
    "progression_path": "Lead Developer → Engineering Manager",
    "confidence": 0.9
  }
}
```

#### 3. **Location Analysis**
```json
{
  "location_analysis": {
    "primary_location": "Toronto, ON",
    "remote_policy": "hybrid",
    "relocation_required": false,
    "confidence": 0.8
  }
}
```

#### 4. **Skill Analysis**
```json
{
  "keyword_analysis": {
    "technical_skills": ["Python", "Django", "PostgreSQL", "AWS"],
    "soft_skills": ["Leadership", "Communication"],
    "emerging_tech": ["Kubernetes", "Machine Learning"],
    "confidence": 0.9
  }
}
```

#### 5. **Compatibility Scoring**
```json
{
  "match_score": {
    "overall": 0.87,           # Final compatibility (now defaults to 0.7 minimum)
    "skill_match": 0.9,        # Technical skill alignment
    "experience_match": 0.8,   # Experience level fit
    "location_match": 1.0,     # Location compatibility
    "cultural_fit": 0.8,       # Company culture alignment
    "growth_potential": 0.85   # Career growth opportunity
  }
}
```

## 🎯 Scoring Weights

OpenHermes 2.5 uses these weights for final scoring:
- **Skill alignment**: 40% (most important)
- **Experience level match**: 25%
- **Location compatibility**: 15%
- **Cultural fit**: 10%
- **Growth potential**: 10%

## 🔄 Fallback System

If OpenHermes 2.5 fails, the system falls back to:
1. **Llama3** (if available)
2. **Enhanced Rule-Based Analysis** (always available)
3. **Default Analysis** (0.7 score, basic data)

## 🧪 Testing Your Setup

### Test 1: Basic Model Test
```bash
python -c "
import requests
response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'openhermes:v2.5',
    'prompt': 'Hello, are you working?',
    'stream': False
})
print(response.json())
"
```

### Test 2: Job Processor Test
```bash
# Run the job processor test
python test_job_processor.py
```

### Test 3: Full Pipeline Test
```bash
# Test complete pipeline
python test_job_processor_demo.py
```

## 📈 Expected Performance

### With OpenHermes 2.5:
- **Analysis Quality**: Excellent (structured, detailed)
- **Response Time**: 2-5 seconds per job
- **Accuracy**: High (fine-tuned for instruction following)
- **Consistency**: Very good (low temperature setting)
- **Default Score**: 0.7 (more optimistic baseline)

### Success Indicators:
- ✅ Jobs get detailed analysis with all fields populated
- ✅ Compatibility scores are realistic (0.6-0.9 range)
- ✅ Skill matches are accurate and comprehensive
- ✅ Recommendations are actionable
- ✅ Processing completes without errors

## 🛠️ Troubleshooting

### Issue 1: Model Not Found
```bash
# Solution: Pull the model
ollama pull openhermes:v2.5
ollama list  # Verify it's installed
```

### Issue 2: Ollama Not Running
```bash
# Solution: Start Ollama
ollama serve
# Or check if running: curl http://localhost:11434/api/tags
```

### Issue 3: Analysis Fails
- Check Ollama logs: `ollama logs`
- Verify model is loaded: `ollama ps`
- Test model directly: `ollama run openhermes:v2.5`

### Issue 4: Slow Performance
```bash
# Optimize Ollama settings
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=1
ollama serve
```

## 🎉 Benefits of OpenHermes 2.5

### Compared to Mistral 7B:
- ✅ **Better instruction following**
- ✅ **More consistent JSON output**
- ✅ **Improved reasoning capabilities**
- ✅ **Better structured responses**

### Compared to Rule-Based:
- ✅ **Context understanding**
- ✅ **Nuanced analysis**
- ✅ **Cultural fit assessment**
- ✅ **Growth potential evaluation**

## 🚀 Next Steps

1. **Run the job processor** to see OpenHermes 2.5 in action
2. **Check the dashboard** for processed jobs with detailed analysis
3. **Review compatibility scores** - they should be more realistic now (0.7+ baseline)
4. **Generate documents** for high-scoring jobs
5. **Monitor performance** and adjust settings as needed

Your system is now optimized with OpenHermes 2.5 as the exclusive AI model with a 0.7 default score baseline!