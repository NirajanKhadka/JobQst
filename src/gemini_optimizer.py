
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


# Create Gemini client using API key from environment

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
genai.configure(api_key=api_key)

class GeminiOptimizer:
    """
    A class to optimize resumes and cover letters using the Gemini API.
    """
    def __init__(self, model_name='gemini-1.5-pro'):
        """
        Initializes the optimizer with a specific Gemini model.
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)

    def build_optimization_prompt(self, job_description, resume, cover_letter):
        """
        Builds the detailed prompt for the Gemini API, instructing it to optimize content
        while preserving the exact original formatting.
        """
        return f"""
CRITICAL INSTRUCTION: You are a professional resume optimizer. Your primary task is to optimize content while maintaining EXACT formatting, spacing, and structure.

## FORMATTING RULES (MANDATORY):
1. **PRESERVE ALL FORMATTING**: Maintain every asterisk (*), pipe (|), dash (-), bullet point (•), spacing, and line breaks
2. **EXACT STRUCTURE**: Keep the same sections, headers, and layout
3. **NO FORMAT CHANGES**: Do not change bold markers (**text**), bullet styles, or spacing
4. **MAINTAIN ALIGNMENT**: Keep all alignment, indentation, and visual structure identical

## INPUT DOCUMENTS:

### JOB DESCRIPTION:
```
{job_description}
```

### ORIGINAL RESUME:
```
{resume}
```

### ORIGINAL COVER LETTER:
```
{cover_letter}
```

## OPTIMIZATION TASKS:

### 1. RESUME OPTIMIZATION:
- Analyze job requirements and tailor content accordingly
- Update OBJECTIVE section to match job focus
- Emphasize relevant skills and experience
- Quantify achievements where possible
- Add industry-specific keywords naturally
- **CRITICAL**: Keep exact same formatting, spacing, and structure

### 2. COVER LETTER OPTIMIZATION:
- Extract company name and position title from job description
- Customize opening paragraph for specific role
- Highlight most relevant experience
- Align language with job requirements
- **CRITICAL**: Maintain exact formatting and structure

### 3. ANALYSIS REQUIRED:
- Calculate job match percentage (0-100%)
- Identify top 5 key improvements made
- List relevant keywords added
- Suggest any additional optimizations

## OUTPUT FORMAT:
Your response must be in this exact JSON structure:

```json
{{
  "optimizedResume": "EXACT_FORMATTED_RESUME_TEXT_HERE",
  "optimizedCoverLetter": "EXACT_FORMATTED_COVER_LETTER_TEXT_HERE",
  "matchScore": 85,
  "keyImprovements": [
    "Tailored objective to match data analytics focus",
    "Emphasized Python and SQL skills",
    "Added marketing analytics keywords",
    "Quantified project impact metrics",
    "Customized cover letter for specific company"
  ],
  "keywordsAdded": ["marketing analytics", "campaign optimization", "data visualization"],
  "companyName": "TechCorp",
  "positionTitle": "Senior Data Analyst",
  "suggestions": [
    "Consider adding A/B testing experience",
    "Highlight customer segmentation projects"
  ]
}}
```

## CRITICAL REMINDERS:
- **FORMATTING IS SACRED**: Do not change any formatting elements
- **PRESERVE STRUCTURE**: Keep all sections, headers, and layout identical
- **CONTENT ONLY**: Only modify the actual text content, not structure
- **PROFESSIONAL TONE**: Maintain professional language throughout
- **ACCURACY**: Only add truthful enhancements based on existing experience

Begin optimization now:
"""

    def parse_gemini_response(self, raw_response):
        """
        Parses the raw JSON response from Gemini, extracting the structured data.
        """
        try:
            # Extract JSON from the response, handling potential markdown formatting
            json_match = raw_response.match(r"```json\n([\s\S]*?)\n```")
            if not json_match:
                # Fallback for responses that might not be in a markdown block
                return json.loads(raw_response)
            
            parsed_data = json.loads(json_match.group(1))
            
            # Validate that essential fields are present
            required_fields = ['optimizedResume', 'optimizedCoverLetter', 'matchScore']
            if not all(field in parsed_data for field in required_fields):
                raise ValueError("The optimized response is missing one or more required fields.")
                
            return parsed_data
        except (json.JSONDecodeError, AttributeError) as e:
            raise ValueError(f"Failed to parse the response from Gemini: {e}")

    async def optimize_documents(self, job_description, resume, cover_letter):
        """
        Orchestrates the optimization process by building the prompt, sending it to Gemini,
        and parsing the response.
        """
        prompt = self.build_optimization_prompt(job_description, resume, cover_letter)
        
        try:
            # Use the new google-genai SDK async client
            result = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = result.text
            return self.parse_gemini_response(response_text)
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during Gemini API call: {e}")

if __name__ == '__main__':
    # Example usage for testing purposes
    async def main():
        optimizer = GeminiOptimizer()
        
        # Dummy data for testing
        job_desc = "Seeking a software engineer with Python and cloud experience."
        resume_text = "**John Doe** | Software Engineer | (123) 456-7890"
        cover_letter_text = "Dear Hiring Manager, I am writing to express my interest..."
        
        try:
            optimized_data = await optimizer.optimize_documents(job_desc, resume_text, cover_letter_text)
            print("Successfully optimized documents:")
            print(json.dumps(optimized_data, indent=2))
        except (ValueError, RuntimeError) as e:
            print(f"Error: {e}")

    import asyncio
    asyncio.run(main())
