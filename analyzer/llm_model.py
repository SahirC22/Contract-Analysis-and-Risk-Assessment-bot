#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
llm_model.py - Advanced Legal Analysis Engine with UTF-8 Support

Enhanced with:
- Sophisticated legal reasoning prompts
- Multi-layered risk assessment
- Confidence scoring and uncertainty quantification
- Detailed clause scoring methodology
- Professional legal-grade analysis
- Hindi language support
- Complete UTF-8 encoding handling
"""

from __future__ import annotations

import os
import sys

# ============================================================================
# CRITICAL: UTF-8 Configuration - Must be set BEFORE any other operations
# ============================================================================

os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
import time

from openai import OpenAI, APIError, RateLimitError, APIConnectionError

try:
    from .risk_rules import evaluate_rules, aggregate_risk_from_rules
    from .report import ClauseAnalysis, ContractSummary, ContractReport
except ImportError:
    from risk_rules import evaluate_rules, aggregate_risk_from_rules
    from report import ClauseAnalysis, ContractSummary, ContractReport

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    encoding='utf-8' if sys.version_info >= (3, 9) else None
)

# Reconfigure stdout/stderr
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)



# Advanced legal analysis system prompt
LEGAL_EXPERT_SYSTEM_PROMPT = """You are a senior corporate attorney with 15+ years of experience in contract law,
specializing in commercial agreements, employment contracts, service agreements, and vendor contracts.

Your analysis must be:
1. OBJECTIVE: Base assessments solely on contractual language, obligations, rights, liabilities, and legal principles
2. UNBIASED: Never consider party names, demographics, nationalities, or any personal attributes
3. THOROUGH: Examine legal implications, enforceability, ambiguities, and potential disputes
4. PRACTICAL: Provide actionable insights for business decision-makers
5. PRECISE: Use specific legal reasoning with clear cause-and-effect explanations

CRITICAL ASSESSMENT FRAMEWORK:
- Obligations: Who must do what, by when, and under what conditions?
- Rights: What can each party demand or enforce?
- Liabilities: What are the consequences of breach or non-performance?
- Risks: What ambiguities, imbalances, or unfavorable terms exist?
- Enforceability: Are terms clear, definite, and legally sound?

You must NEVER allow demographic information to influence legal risk assessment."""

# Advanced clause analysis prompt template
CLAUSE_ANALYSIS_PROMPT = """Analyze the following contract clause with legal precision:

CLAUSE TEXT:
{clause_text}

ANALYSIS REQUIREMENTS:

1. PLAIN LANGUAGE EXPLANATION (150-200 words):
   - Explain what this clause legally requires or permits
   - Identify the key obligations, rights, or restrictions
   - Clarify any technical or legal terminology
   - Describe practical business implications

2. RISK ASSESSMENT:
   - Evaluate: Low (minimal concern), Medium (notable concern), or High (significant concern)
   - Consider: obligation severity, liability scope, ambiguity level, enforceability issues
   - Factor in: payment terms, termination rights, indemnification, warranties, IP rights

3. DETAILED RISK REASONING (100-150 words):
   - Explain WHY the risk level is assigned
   - Identify specific problematic language or terms
   - Describe potential adverse outcomes or disputes
   - Note any missing protections or one-sided provisions
   - Reference specific legal principles or concerns

4. CONFIDENCE ASSESSMENT:
   - Rate confidence in this analysis: High (90-100%), Medium (70-89%), Low (<70%)
   - Note any ambiguities requiring legal counsel review

5. AFFECTED PARTY ANALYSIS:
   - Identify: Buyer, Seller, Vendor, Service Provider, Client, Both Parties, Employer, Employee, or Unclear
   - Explain which party bears greater burden or risk

6. ALTERNATIVE CLAUSE (100-150 words):
   - Provide balanced, fair alternative language
   - Address identified risks and ambiguities
   - Include specific terms, conditions, and protections
   - Maintain enforceability and clarity

7. NEGOTIATION STRATEGY (75-100 words):
   - Provide tactical negotiation advice
   - Suggest specific changes or additions
   - Identify leverage points and fallback positions

RESPONSE FORMAT (JSON ONLY):
{{
  "plain_english_explanation": "string",
  "risk_level": "Low|Medium|High",
  "risk_reason": "string",
  "confidence_level": "High|Medium|Low",
  "confidence_percentage": number,
  "affected_party": "string",
  "party_impact_reasoning": "string",
  "suggested_alternative_clause": "string",
  "negotiation_insight": "string",
  "legal_concerns": ["concern1", "concern2"],
  "missing_protections": ["protection1", "protection2"],
  "ambiguous_terms": ["term1", "term2"]
}}"""

# Advanced contract summary prompt
SUMMARY_ANALYSIS_PROMPT = """Conduct a comprehensive legal analysis of this contract:

CONTRACT EXCERPT:
{contract_text}

TOTAL DOCUMENT: {word_count} words

COMPREHENSIVE ANALYSIS REQUIREMENTS:

1. EXECUTIVE SUMMARY (200-300 words):
   - Contract type and purpose
   - Parties and their roles
   - Core obligations and deliverables
   - Payment structure and terms
   - Duration and termination provisions
   - Liability framework and limitations
   - Intellectual property rights
   - Dispute resolution mechanism
   - Key business implications

2. OVERALL RISK ASSESSMENT:
   - Evaluate: Low, Medium, or High
   - Consider: aggregated clause risks, missing provisions, unfavorable balance
   - Base on: legal enforceability, business exposure, operational constraints

3. TOP BUSINESS RISKS (Identify 3-5):
   - List most significant legal or business concerns
   - Prioritize by potential impact and likelihood
   - Be specific about exposure or consequences

4. CONTRACT QUALITY METRICS:
   A. COMPLETENESS SCORE (0-100):
      Rate based on presence and adequacy of:
      - Parties identification and capacity (10 points)
      - Scope of work/deliverables (10 points)
      - Payment terms and schedule (10 points)
      - Contract duration and renewal (10 points)
      - Termination rights and procedures (15 points)
      - Liability and indemnification (15 points)
      - Intellectual property provisions (10 points)
      - Dispute resolution mechanism (10 points)
      - Confidentiality provisions (5 points)
      - Warranties and representations (5 points)
   
   B. IDENTIFY STRUCTURAL ISSUES:
      - Conflicting clauses (describe each conflict)
      - Duplicate or inconsistent terms
      - Ambiguous definitions or undefined terms
      - Missing critical clauses for this contract type

5. STRATEGIC NEGOTIATION RECOMMENDATIONS (3-5 specific actions):
   - Prioritize by importance and negotiability
   - Provide tactical approach for each
   - Include specific language suggestions where applicable

RESPONSE FORMAT (JSON ONLY):
{{
  "business_summary": "string",
  "overall_risk": "Low|Medium|High",
  "overall_risk_reasoning": "string",
  "top_3_business_risks": ["risk1", "risk2", "risk3"],
  "contract_completeness_score": number,
  "completeness_breakdown": {{
    "parties": number,
    "scope": number,
    "payment": number,
    "duration": number,
    "termination": number,
    "liability": number,
    "ip_rights": number,
    "disputes": number,
    "confidentiality": number,
    "warranties": number
  }},
  "conflicting_clauses": ["conflict1", "conflict2"],
  "duplicate_or_ambiguous_terms": ["term1", "term2"],
  "missing_critical_clauses": ["clause1", "clause2"],
  "negotiation_recommendations": ["rec1", "rec2", "rec3"],
  "document_length_words": number,
  "contract_type_classification": "string",
  "jurisdiction_concerns": ["concern1"]
}}"""

@dataclass
class LLMConfig:
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 3000
    max_retries: int = 3
    retry_delay: float = 2.0

class ContractAnalyzer:
    def __init__(self, api_key: str, config: LLMConfig | None = None):
        self.client = OpenAI(api_key=api_key)
        self.config = config or LLMConfig()
        self._analysis_cache = {}
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to ensure UTF-8 compatibility"""
        try:
            if not isinstance(text, str):
                text = str(text)
            
            # Encode to UTF-8 and decode back, replacing errors
            text = text.encode('utf-8', errors='replace').decode('utf-8')
            
            # Remove null bytes and other problematic characters
            text = text.replace('\x00', '')
            
            return text
        except Exception as e:
            logger.error(f"Failed to sanitize text: {e}")
            # Fallback: convert to safe string
            try:
                return str(text)
            except Exception:
                return ""
    
    def _chat(self, system: str, user: str, max_retries: Optional[int] = None) -> str:
        """Enhanced API call with retry logic and UTF-8 handling"""
        retries = max_retries if max_retries is not None else self.config.max_retries
        
        # Sanitize inputs to ensure UTF-8 compatibility
        try:
            system = self._sanitize_text(system)
            user = self._sanitize_text(user)
        except Exception as e:
            logger.error(f"Failed to sanitize input: {e}")
            return ""
        
        # Simple cache key (using sanitized text)
        cache_key = hash((system[:100], user[:100]))
        if cache_key in self._analysis_cache:
            logger.info("Using cached analysis result")
            return self._analysis_cache[cache_key]
        
        last_error = None
        for attempt in range(retries):
            try:
                logger.info(f"API call attempt {attempt + 1}/{retries}")
                
                resp = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=90.0,
                )
                
                content = resp.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Empty response from API")
                
                logger.info(f"API call successful on attempt {attempt + 1}")
                
                # Sanitize response
                content = self._sanitize_text(content.strip())
                
                # Cache successful result
                self._analysis_cache[cache_key] = content
                return content
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
            except APIConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < retries - 1:
                    time.sleep(self.config.retry_delay)
            
            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < retries - 1:
                    time.sleep(self.config.retry_delay)
            
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                logger.error(f"Unicode error on attempt {attempt + 1}: {e}")
                last_error = e
                # Try to sanitize more aggressively by removing non-ASCII
                try:
                    system = ''.join(c for c in system if ord(c) < 128)
                    user = ''.join(c for c in user if ord(c) < 128)
                    logger.info("Stripped to ASCII, retrying...")
                except Exception:
                    pass
                if attempt < retries - 1:
                    time.sleep(self.config.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}")
                last_error = e
                if attempt < retries - 1:
                    time.sleep(self.config.retry_delay)
        
        logger.error(f"All {retries} attempts failed. Last error: {last_error}")
        # Return empty string instead of raising to allow analysis to continue
        return ""
    
    def _parse_json_response(self, raw_response: str, fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced JSON parsing with better cleanup"""
        if not raw_response or not raw_response.strip():
            logger.warning("Empty response received, using fallback")
            return fallback_data
        
        cleaned = raw_response.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```"):
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].strip()
            else:
                cleaned = cleaned[3:].strip()
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        
        # Remove single backticks
        if cleaned.startswith("`") and cleaned.endswith("`"):
            cleaned = cleaned[1:-1].strip()
        
        try:
            parsed = json.loads(cleaned)
            logger.info("Successfully parsed JSON response")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            
            # Try to extract JSON from text
            try:
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = cleaned[start:end]
                    parsed = json.loads(json_str)
                    logger.info("Extracted JSON from response")
                    return parsed
            except Exception:
                pass
        
        logger.warning("Using fallback data")
        return fallback_data
    
    def analyze_clause(
        self, clause_text: str, clause_index: int, anonymised_text: str, language: str = "English"
    ) -> ClauseAnalysis:
        """Advanced clause analysis with detailed legal reasoning"""
        if not clause_text or len(clause_text.strip()) < 10:
            logger.warning(f"Clause {clause_index} is too short or empty")
            return self._create_fallback_clause_analysis(clause_index, clause_text, anonymised_text)
        
        # Sanitize clause text
        clause_text = self._sanitize_text(clause_text)
        
        # Rule-based analysis
        rule_matches = evaluate_rules(clause_text)
        rules_risk = aggregate_risk_from_rules(rule_matches)
        
        # Language instruction
        if language == "Hindi":
            lang_instruction = """
IMPORTANT: You MUST write ALL explanations, reasoning, and recommendations in Hindi (Devanagari script).
Only the following fields should be in English: risk_level, confidence_level, affected_party
All other text fields (plain_english_explanation, risk_reason, suggested_alternative_clause, negotiation_insight, etc.) MUST be in Hindi."""
        else:
            lang_instruction = "Provide all explanations in English."
        
        system_msg = LEGAL_EXPERT_SYSTEM_PROMPT + "\n\n" + lang_instruction + "\n\nRespond ONLY with valid JSON."
        user_prompt = CLAUSE_ANALYSIS_PROMPT.format(clause_text=clause_text)
        
        fallback = {
            "plain_english_explanation": (
                "This clause establishes specific contractual obligations, rights, or conditions "
                "that require careful legal review. The language used may create binding commitments "
                "or limitations that could affect the business relationship between the parties."
            ),
            "risk_level": "Medium",
            "risk_reason": (
                "Standard contractual provision requiring detailed analysis of obligations, "
                "performance requirements, and potential liability exposure. Legal counsel should "
                "review to ensure terms are acceptable and enforceable."
            ),
            "confidence_level": "Medium",
            "confidence_percentage": 75,
            "affected_party": "Both Parties",
            "party_impact_reasoning": "Standard provision affecting multiple parties",
            "suggested_alternative_clause": (
                "Revise to include: (1) clear definitions of key terms, (2) specific performance "
                "timelines and metrics, (3) balanced obligations for both parties, (4) reasonable "
                "liability limitations, and (5) explicit termination or modification procedures."
            ),
            "negotiation_insight": (
                "Ensure all terms are clearly defined with measurable criteria. Request specific "
                "timelines and performance standards. Negotiate balanced liability provisions."
            ),
            "legal_concerns": ["Ambiguous language", "Undefined terms"],
            "missing_protections": ["Limitation of liability", "Termination rights"],
            "ambiguous_terms": ["Reasonable efforts", "Timely manner"]
        }
        
        try:
            raw = self._chat(system_msg, user_prompt)
            if not raw:
                logger.warning(f"Empty response for clause {clause_index}, using fallback")
                return self._create_fallback_clause_analysis(clause_index, clause_text, anonymised_text)
            
            parsed = self._parse_json_response(raw, fallback)
        except Exception as e:
            logger.error(f"Failed to analyze clause {clause_index}: {e}")
            return self._create_fallback_clause_analysis(clause_index, clause_text, anonymised_text)
        
        # Extract and validate fields
        llm_risk = parsed.get("risk_level", "Medium").title()
        final_risk = self._combine_risks(llm_risk, rules_risk)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            final_risk,
            parsed.get("confidence_percentage", 75),
            len(rule_matches),
            parsed.get("legal_concerns", []),
            parsed.get("missing_protections", [])
        )
        
        return ClauseAnalysis(
            clause_index=clause_index,
            original_text=clause_text,
            anonymised_text=anonymised_text,
            plain_english_explanation=parsed.get("plain_english_explanation", fallback["plain_english_explanation"]),
            risk_level_llm=llm_risk,
            risk_level_rules=rules_risk,
            risk_level_final=final_risk,
            risk_reason_llm=parsed.get("risk_reason", fallback["risk_reason"]),
            suggested_alternative_clause=parsed.get("suggested_alternative_clause", fallback["suggested_alternative_clause"]),
            affected_party=parsed.get("affected_party", "Unclear"),
            final_risk_score=risk_score,
            negotiation_insight=parsed.get("negotiation_insight", fallback["negotiation_insight"]),
            rule_hits=[{
                "rule_id": rm.rule_id,
                "description": rm.description,
                "risk_level": rm.risk_level
            } for rm in rule_matches],
        )
    
    def _calculate_risk_score(
        self,
        risk_level: str,
        confidence: int,
        rule_count: int,
        concerns: List[str],
        missing: List[str]
    ) -> float:
        """Calculate numerical risk score (0-100)"""
        base_scores = {"Low": 25, "Medium": 50, "High": 80}
        score = base_scores.get(risk_level, 50)
        
        # Adjust for confidence
        if confidence < 70:
            score += 5
        
        # Adjust for rule hits
        score += min(rule_count * 3, 15)
        
        # Adjust for concerns
        score += min(len(concerns) * 2, 10)
        score += min(len(missing) * 3, 10)
        
        return min(score, 100.0)
    
    def _create_fallback_clause_analysis(
        self, clause_index: int, clause_text: str, anonymised_text: str
    ) -> ClauseAnalysis:
        """Enhanced fallback analysis"""
        rule_matches = evaluate_rules(clause_text)
        rules_risk = aggregate_risk_from_rules(rule_matches)
        
        return ClauseAnalysis(
            clause_index=clause_index,
            original_text=clause_text,
            anonymised_text=anonymised_text,
            plain_english_explanation=(
                "This clause requires professional legal review for comprehensive analysis. "
                "Automated assessment is limited due to complex legal language or formatting issues."
            ),
            risk_level_llm="Medium",
            risk_level_rules=rules_risk,
            risk_level_final=rules_risk if rules_risk != "Low" else "Medium",
            risk_reason_llm="Automated analysis unavailable. Manual legal review recommended.",
            suggested_alternative_clause="Consult legal counsel for alternative drafting recommendations.",
            affected_party="Unclear",
            final_risk_score=50.0,
            negotiation_insight="Seek professional legal advice for negotiation strategy.",
            rule_hits=[{
                "rule_id": rm.rule_id,
                "description": rm.description,
                "risk_level": rm.risk_level
            } for rm in rule_matches],
        )
    
    @staticmethod
    def _combine_risks(llm_risk: str, rules_risk: str) -> str:
        """Conservative risk combination"""
        order = {"Low": 0, "Medium": 1, "High": 2}
        llm_score = order.get(llm_risk.title(), 1)
        rules_score = order.get(rules_risk.title(), 1)
        final_score = max(llm_score, rules_score)
        
        for k, v in order.items():
            if v == final_score:
                return k
        return "Medium"
    
    def summarize_contract(
        self, full_text: str, overall_rules_risk: str, language: str = "English"
    ) -> ContractSummary:
        """Advanced contract summary with comprehensive metrics"""
        
        # Sanitize input text
        full_text = self._sanitize_text(full_text)
        
        if language == "Hindi":
            lang_instruction = """
CRITICAL: You MUST write the ENTIRE analysis in Hindi (Devanagari script).
Only risk level labels (Low/Medium/High) should remain in English.
All descriptions, summaries, recommendations, and explanations MUST be in Hindi.
This is mandatory - do not provide English text."""
        else:
            lang_instruction = "Write all analysis in English."
        
        system_msg = LEGAL_EXPERT_SYSTEM_PROMPT + "\n\n" + lang_instruction + "\n\nRespond ONLY with valid JSON."
        
        text_sample = full_text[:12000] if len(full_text) > 12000 else full_text
        word_count = len(full_text.split())
        
        user_prompt = SUMMARY_ANALYSIS_PROMPT.format(
            contract_text=text_sample,
            word_count=word_count
        )
        
        fallback = {
            "business_summary": (
                "This is a commercial agreement establishing business terms between parties. "
                "Key provisions cover obligations, payment terms, duration, liability, "
                "termination rights, and dispute resolution. Comprehensive legal review is "
                "recommended to ensure all terms align with business objectives and risk tolerance."
            ),
            "overall_risk": overall_rules_risk,
            "overall_risk_reasoning": "Assessment based on aggregated clause-level risks and structural analysis.",
            "top_3_business_risks": [
                "Potential liability exposure requiring review of indemnification provisions",
                "Termination conditions may not adequately protect business interests",
                "Payment terms and dispute resolution mechanism require clarification"
            ],
            "contract_completeness_score": 65,
            "completeness_breakdown": {
                "parties": 8, "scope": 7, "payment": 6, "duration": 7,
                "termination": 6, "liability": 6, "ip_rights": 5, "disputes": 6,
                "confidentiality": 4, "warranties": 5
            },
            "conflicting_clauses": [],
            "duplicate_or_ambiguous_terms": [],
            "missing_critical_clauses": [],
            "negotiation_recommendations": [
                "Clarify all material obligations with specific performance metrics",
                "Negotiate balanced liability limitations and indemnification provisions",
                "Ensure termination rights are mutual and include reasonable notice periods"
            ],
            "document_length_words": word_count,
            "contract_type_classification": "Commercial Agreement",
            "jurisdiction_concerns": []
        }
        
        try:
            raw = self._chat(system_msg, user_prompt)
            if not raw:
                logger.warning("Empty response for summary, using fallback")
                parsed = fallback
            else:
                parsed = self._parse_json_response(raw, fallback)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            parsed = fallback
        
        llm_overall = parsed.get("overall_risk", "Medium").title()
        final_overall = self._combine_risks(llm_overall, overall_rules_risk)
        
        return ContractSummary(
            business_summary=parsed.get("business_summary", fallback["business_summary"]),
            overall_risk_llm=llm_overall,
            overall_risk_rules=overall_rules_risk.title(),
            overall_risk_final=final_overall,
            top_risks=parsed.get("top_3_business_risks", fallback["top_3_business_risks"]),
            missing_critical_clauses=parsed.get("missing_critical_clauses", []),
            contract_completeness_score=parsed.get("contract_completeness_score", 65),
            conflicting_clauses=parsed.get("conflicting_clauses", []),
            duplicate_or_ambiguous_terms=parsed.get("duplicate_or_ambiguous_terms", []),
            negotiation_insights=parsed.get("negotiation_recommendations", fallback["negotiation_recommendations"]),
            document_length_words=parsed.get("document_length_words", word_count)
        )
    
    def analyze_contract(
        self,
        original_clauses: List[str],
        anonymised_clauses: List[str],
        full_text: str,
        language: str = "English",
    ) -> ContractReport:
        """Main analysis pipeline with progress tracking"""
        logger.info(f"Starting comprehensive analysis of {len(original_clauses)} clauses")
        
        clause_results: List[ClauseAnalysis] = []
        
        for idx, (orig, anon) in enumerate(zip(original_clauses, anonymised_clauses), start=1):
            try:
                logger.info(f"Analyzing clause {idx}/{len(original_clauses)}")
                
                clause_result = self.analyze_clause(
                    clause_text=orig,
                    clause_index=idx,
                    anonymised_text=anon,
                    language=language
                )
                
                clause_results.append(clause_result)
                
                # Rate limiting
                if idx % 5 == 0:
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error analyzing clause {idx}: {e}")
                clause_results.append(
                    self._create_fallback_clause_analysis(idx, orig, anon)
                )
        
        # Aggregate rule-based risk
        all_rule_matches = []
        for c in original_clauses:
            all_rule_matches.extend(evaluate_rules(c) or [])
        overall_rules_risk = aggregate_risk_from_rules(all_rule_matches)
        
        # Generate summary
        logger.info("Generating comprehensive contract summary")
        summary = self.summarize_contract(full_text, overall_rules_risk, language=language)
        
        report = ContractReport(
            summary=summary,
            clauses=clause_results,
            anonymisation_map={},
        )
        
        logger.info("Analysis complete")
        return report
