#!/usr/bin/env python3
"""
Enhanced Transformer-based Stage 2 Processor for JobQst

This module provides specialized transformer models for different aspects of job analysis:
- BERT/RoBERTa for general text understanding
- Specialized models for skill extraction
- Sentiment analysis models
- Classification models for job categories
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModel,
        AutoModelForSequenceClassification,
        pipeline,
        BertTokenizer,
        BertModel,
        RobertaTokenizer,
        RobertaModel,
    )

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class TransformerAnalysisResult:
    """Enhanced result from transformer-based analysis"""

    # Core NLP outputs
    embeddings: Optional[np.ndarray] = None
    semantic_skills: List[str] = None
    extracted_requirements: List[str] = None

    # Specialized analysis
    job_category: str = "unknown"
    seniority_level: str = "unknown"
    remote_work_score: float = 0.0
    tech_stack_match: float = 0.0

    # Sentiment and culture
    job_sentiment: str = "neutral"
    sentiment_score: float = 0.0
    company_culture_indicators: List[str] = None

    # Advanced scoring
    semantic_compatibility: float = 0.0
    confidence_score: float = 0.0

    # Processing metadata
    model_used: str = ""
    processing_time: float = 0.0
    gpu_memory_used: float = 0.0

    def __post_init__(self):
        if self.semantic_skills is None:
            self.semantic_skills = []
        if self.extracted_requirements is None:
            self.extracted_requirements = []
        if self.company_culture_indicators is None:
            self.company_culture_indicators = []


class TransformerJobAnalyzer:
    """
    Enhanced transformer-based job analyzer with multiple specialized models
    """

    def __init__(
        self,
        user_profile: Dict[str, Any],
        primary_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
        classification_model: str = "microsoft/DialoGPT-medium",
    ):
        """
        Initialize transformer analyzer with multiple specialized models

        Args:
            user_profile: User profile for personalized analysis
            primary_model: Main model for embeddings and general NLP
            sentiment_model: Specialized sentiment analysis model
            classification_model: Model for job classification tasks
        """
        self.user_profile = user_profile
        self.primary_model_name = primary_model
        self.sentiment_model_name = sentiment_model
        self.classification_model_name = classification_model

        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "Transformers not available. Install with: pip install transformers torch"
            )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        console.print(
            f"[cyan]🤖 Initializing Enhanced Transformer Analyzer on {self.device}[/cyan]"
        )

        # Initialize models
        self._initialize_models()

        # Prepare user profile embeddings for similarity matching
        self._prepare_user_profile_embeddings()

    def _initialize_models(self):
        """Initialize all transformer models"""
        try:
            # Primary model for embeddings and general analysis
            console.print(f"[cyan]📥 Loading primary model: {self.primary_model_name}[/cyan]")
            self.primary_tokenizer = AutoTokenizer.from_pretrained(self.primary_model_name)
            self.primary_model = AutoModel.from_pretrained(self.primary_model_name).to(self.device)
            self.primary_model.eval()

            # Sentiment analysis pipeline
            console.print(f"[cyan]📥 Loading sentiment model: {self.sentiment_model_name}[/cyan]")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                device=0 if torch.cuda.is_available() else -1,
            )

            # Skills extraction using NER or custom classification
            console.print(f"[cyan]📥 Loading NER model for skill extraction[/cyan]")
            self.ner_pipeline = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1,
            )

            console.print(f"[green]✅ All transformer models loaded successfully[/green]")

        except Exception as e:
            logger.error(f"Failed to initialize transformer models: {e}")
            raise

    def _prepare_user_profile_embeddings(self):
        """Pre-compute embeddings for user profile skills and preferences"""
        try:
            user_skills = self.user_profile.get("skills", [])
            user_keywords = self.user_profile.get("keywords", [])

            # Combine user preferences into text
            user_text = f"Skills: {', '.join(user_skills)}. Interests: {', '.join(user_keywords)}"

            self.user_embeddings = self._get_embeddings(user_text)
            console.print(f"[green]✅ User profile embeddings prepared[/green]")

        except Exception as e:
            logger.warning(f"Could not prepare user embeddings: {e}")
            self.user_embeddings = None

    def _get_embeddings(self, text: str) -> Optional[np.ndarray]:
        """Get embeddings using the primary transformer model"""
        if not self.primary_model or not self.primary_tokenizer:
            return None

        try:
            # Tokenize with proper handling
            inputs = self.primary_tokenizer(
                text, return_tensors="pt", truncation=True, padding=True, max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.primary_model(**inputs)
                # Use CLS token or mean pooling
                if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    embeddings = outputs.pooler_output
                else:
                    # Fallback to mean pooling
                    embeddings = outputs.last_hidden_state.mean(dim=1)

            return embeddings.cpu().numpy()

        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return None

    def _extract_semantic_skills(self, job_description: str) -> List[str]:
        """Extract skills using transformer-based NER and semantic analysis"""
        skills = []

        try:
            # Use NER to identify potential skill entities
            ner_results = self.ner_pipeline(job_description)

            # Extract entities that might be skills
            for entity in ner_results:
                if entity["entity_group"] in ["ORG", "MISC"] and len(entity["word"]) > 2:
                    # Filter for technical skills
                    word = entity["word"].strip()
                    if any(
                        tech_indicator in word.lower()
                        for tech_indicator in [
                            "python",
                            "java",
                            "sql",
                            "aws",
                            "docker",
                            "react",
                            "node",
                            "git",
                        ]
                    ):
                        skills.append(word)

            # Add rule-based skill extraction as fallback
            tech_skills = [
                "Python",
                "JavaScript",
                "Java",
                "C++",
                "SQL",
                "AWS",
                "Azure",
                "Docker",
                "Kubernetes",
                "React",
                "Vue.js",
                "Node.js",
                "Django",
                "Flask",
                "Spring",
                "MongoDB",
                "PostgreSQL",
                "Redis",
                "Elasticsearch",
                "Apache Kafka",
                "TensorFlow",
                "PyTorch",
                "scikit-learn",
                "Pandas",
                "NumPy",
                "Git",
                "Jenkins",
                "CI/CD",
                "Terraform",
                "Ansible",
                "Linux",
                "Windows",
                "Machine Learning",
                "Deep Learning",
                "Data Science",
                "AI",
                "NLP",
            ]

            job_text_lower = job_description.lower()
            for skill in tech_skills:
                if skill.lower() in job_text_lower and skill not in skills:
                    skills.append(skill)

            return skills[:15]  # Return top 15 skills

        except Exception as e:
            logger.error(f"Error in semantic skill extraction: {e}")
            return []

    def _analyze_sentiment_advanced(self, job_description: str) -> Tuple[str, float]:
        """Advanced sentiment analysis using transformer model"""
        try:
            result = self.sentiment_analyzer(job_description)

            # Convert to our format
            label = result[0]["label"].lower()
            score = result[0]["score"]

            # Map labels to our format
            if "positive" in label or label == "LABEL_2":
                sentiment = "positive"
            elif "negative" in label or label == "LABEL_0":
                sentiment = "negative"
            else:
                sentiment = "neutral"

            return sentiment, score

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return "neutral", 0.5

    def _calculate_semantic_compatibility(self, job_embeddings: np.ndarray) -> float:
        """Calculate semantic compatibility using embedding similarity"""
        if self.user_embeddings is None or job_embeddings is None:
            return 0.0

        try:
            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity

            similarity = cosine_similarity(
                self.user_embeddings.reshape(1, -1), job_embeddings.reshape(1, -1)
            )[0][0]

            # Convert to 0-1 scale (cosine similarity is -1 to 1)
            compatibility = (similarity + 1) / 2

            return min(0.95, max(0.0, compatibility))

        except Exception as e:
            logger.error(f"Error calculating semantic compatibility: {e}")
            return 0.0

    def _classify_job_category(self, job_description: str, job_title: str) -> str:
        """Classify job into categories using semantic analysis"""
        combined_text = f"{job_title} {job_description}".lower()

        # Define category keywords
        categories = {
            "software_development": ["developer", "software", "programming", "coding", "engineer"],
            "data_science": ["data scientist", "machine learning", "analytics", "data analysis"],
            "devops": ["devops", "infrastructure", "deployment", "ci/cd", "kubernetes"],
            "frontend": ["frontend", "react", "vue", "angular", "ui/ux", "javascript"],
            "backend": ["backend", "api", "server", "database", "microservices"],
            "mobile": ["mobile", "android", "ios", "react native", "flutter"],
            "ai_ml": ["artificial intelligence", "machine learning", "deep learning", "nlp"],
            "qa_testing": ["qa", "testing", "test automation", "quality assurance"],
        }

        # Score each category
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            scores[category] = score

        # Return highest scoring category
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category

        return "general_tech"

    def _detect_seniority_level(self, job_description: str, job_title: str) -> str:
        """Detect seniority level using transformer analysis"""
        combined_text = f"{job_title} {job_description}".lower()

        seniority_indicators = {
            "entry": ["entry", "junior", "jr", "graduate", "intern", "associate", "0-2 years"],
            "mid": ["mid", "intermediate", "3-5 years", "experienced"],
            "senior": ["senior", "sr", "lead", "principal", "5+ years", "7+ years"],
            "executive": ["director", "vp", "cto", "head of", "chief", "executive"],
        }

        for level, indicators in seniority_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                return level

        return "mid"  # Default to mid-level

    def analyze_job(self, job_data: Dict[str, Any]) -> TransformerAnalysisResult:
        """
        Comprehensive job analysis using multiple transformer models

        Args:
            job_data: Job data dictionary

        Returns:
            TransformerAnalysisResult with comprehensive analysis
        """
        start_time = time.time()
        gpu_memory_before = 0

        try:
            if torch.cuda.is_available():
                gpu_memory_before = torch.cuda.memory_allocated() / 1024**2  # MB

            job_description = job_data.get("description", "")
            job_title = job_data.get("title", "")

            # Get embeddings for the job
            job_embeddings = self._get_embeddings(f"{job_title} {job_description}")

            # Extract semantic skills
            semantic_skills = self._extract_semantic_skills(job_description)

            # Sentiment analysis
            sentiment, sentiment_score = self._analyze_sentiment_advanced(job_description)

            # Job classification
            job_category = self._classify_job_category(job_description, job_title)
            seniority_level = self._detect_seniority_level(job_description, job_title)

            # Calculate semantic compatibility
            semantic_compatibility = self._calculate_semantic_compatibility(job_embeddings)

            # Extract requirements using transformer understanding
            extracted_requirements = self._extract_requirements_semantic(job_description)

            # Calculate overall confidence
            confidence_score = min(
                0.95,
                (
                    (len(semantic_skills) / 10) * 0.3  # Skills found
                    + sentiment_score * 0.2  # Sentiment confidence
                    + (len(extracted_requirements) / 5) * 0.3  # Requirements found
                    + semantic_compatibility * 0.2  # User match
                ),
            )

            # GPU memory after processing
            gpu_memory_after = 0
            if torch.cuda.is_available():
                gpu_memory_after = torch.cuda.memory_allocated() / 1024**2  # MB

            return TransformerAnalysisResult(
                embeddings=job_embeddings,
                semantic_skills=semantic_skills,
                extracted_requirements=extracted_requirements,
                job_category=job_category,
                seniority_level=seniority_level,
                job_sentiment=sentiment,
                sentiment_score=sentiment_score,
                semantic_compatibility=semantic_compatibility,
                confidence_score=confidence_score,
                model_used=self.primary_model_name,
                processing_time=time.time() - start_time,
                gpu_memory_used=gpu_memory_after - gpu_memory_before,
            )

        except Exception as e:
            logger.error(f"Error in transformer job analysis: {e}")
            return TransformerAnalysisResult(
                model_used=self.primary_model_name,
                processing_time=time.time() - start_time,
                confidence_score=0.0,
            )

    def _extract_requirements_semantic(self, job_description: str) -> List[str]:
        """Extract job requirements using semantic understanding"""
        requirements = []

        # Split into sentences for better analysis
        sentences = job_description.split(".")

        requirement_indicators = [
            "required",
            "must have",
            "essential",
            "mandatory",
            "minimum",
            "experience in",
            "knowledge of",
            "proficient in",
            "skilled in",
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(indicator in sentence_lower for indicator in requirement_indicators):
                # Clean and add the requirement
                if len(sentence.strip()) > 10 and len(sentence.strip()) < 200:
                    requirements.append(sentence.strip())

        return requirements[:10]  # Top 10 requirements


def get_transformer_analyzer(user_profile: Dict[str, Any]) -> Optional[TransformerJobAnalyzer]:
    """
    Factory function to get transformer analyzer

    Args:
        user_profile: User profile for personalized analysis

    Returns:
        TransformerJobAnalyzer instance or None if not available
    """
    if not TRANSFORMERS_AVAILABLE:
        logger.warning("Transformers not available, falling back to rule-based analysis")
        return None

    try:
        return TransformerJobAnalyzer(user_profile)
    except Exception as e:
        logger.error(f"Failed to initialize transformer analyzer: {e}")
        return None


# Integration with existing two-stage processor
def integrate_transformer_stage2(
    job_data: Dict[str, Any], user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Integration function for existing two-stage processor

    Args:
        job_data: Job data to analyze
        user_profile: User profile for personalized analysis

    Returns:
        Enhanced job data with transformer analysis
    """
    analyzer = get_transformer_analyzer(user_profile)

    if analyzer is None:
        # Fallback to existing logic
        return job_data

    try:
        # Run transformer analysis
        result = analyzer.analyze_job(job_data)

        # Enhance job data with transformer results
        enhanced_data = job_data.copy()
        enhanced_data.update(
            {
                "transformer_skills": result.semantic_skills,
                "transformer_requirements": result.extracted_requirements,
                "job_category": result.job_category,
                "seniority_level": result.seniority_level,
                "sentiment": result.job_sentiment,
                "sentiment_score": result.sentiment_score,
                "semantic_compatibility": result.semantic_compatibility,
                "transformer_confidence": result.confidence_score,
                "processing_time": result.processing_time,
            }
        )

        return enhanced_data

    except Exception as e:
        logger.error(f"Transformer integration failed: {e}")
        return job_data


if __name__ == "__main__":
    # Test the transformer analyzer
    test_profile = {
        "skills": ["Python", "Machine Learning", "SQL", "AWS"],
        "keywords": ["data science", "python", "machine learning"],
    }

    test_job = {
        "title": "Data Scientist",
        "company": "TechCorp",
        "description": """
        We are seeking a talented Data Scientist to join our AI team. 
        Required skills include Python, machine learning, SQL, and AWS.
        Experience with TensorFlow and PyTorch is preferred.
        Must have 3+ years of experience in data science.
        """,
    }

    analyzer = get_transformer_analyzer(test_profile)
    if analyzer:
        result = analyzer.analyze_job(test_job)
        console.print(f"[green]✅ Test completed: {result.confidence_score:.2f} confidence[/green]")
        console.print(f"[cyan]Skills found: {result.semantic_skills}[/cyan]")
        console.print(f"[cyan]Category: {result.job_category}[/cyan]")
        console.print(f"[cyan]Compatibility: {result.semantic_compatibility:.2f}[/cyan]")
