"""
main.py

Backend execution pipeline with professional output formatting.
Run: python main.py path/to/contract.pdf
"""

from analyzer.extractor import extract_text
from analyzer.preprocessor import preprocess_contract
from analyzer.llm_model import ContractAnalyzer, LLMConfig
import sys
import json
import os
from datetime import datetime

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise EnvironmentError("ERROR: Missing API key — set OPENAI_API_KEY in environment variables.")


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_status(message: str, status: str = "INFO"):
    """Print status message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{status}] {message}")


def run_analysis(file_path: str):
    """
    Execute complete contract analysis pipeline.
    
    Parameters
    ----------
    file_path : str
        Path to contract document (PDF, DOCX, or TXT)
        
    Returns
    -------
    dict
        Complete analysis report in JSON format
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print_header("CONTRACT ANALYSIS PIPELINE")
    print_status(f"Processing file: {file_path}")
    
    # Step 1: Text Extraction
    print_status("Extracting contract text from document...")
    with open(file_path, "rb") as f:
        text = extract_text(f, None)
    
    if not text or len(text) < 100:
        raise ValueError("Insufficient text extracted from document. Please verify file integrity.")
    
    print_status(f"Successfully extracted {len(text):,} characters")
    
    # Step 2: Preprocessing
    print_status("Cleaning, anonymizing and segmenting contract clauses...")
    anonymised_text, original_clauses, anonymised_clauses, anon = preprocess_contract(text)
    print_status(f"Identified {len(original_clauses)} distinct clauses")
    
    if anon.entity_map:
        print_status(f"Anonymized {len(anon.entity_map)} entities to reduce bias")
    
    # Step 3: AI Analysis
    print_status("Performing comprehensive AI-powered legal analysis...")
    print_status("This may take several minutes depending on contract complexity...")
    
    analyzer = ContractAnalyzer(api_key=API_KEY, config=LLMConfig(model_name="gpt-4o"))
    
    report = analyzer.analyse_full_contract(
        original_text=text,
        anonymised_text=anonymised_text,
        clauses=original_clauses,
        anonymised_clause_texts=anonymised_clauses,
        anonymisation_map=anon.entity_map,
        output_language="English",
    )
    
    print_status("Analysis completed successfully", "SUCCESS")
    
    # Display summary
    print_header("ANALYSIS SUMMARY")
    summary = report.summary
    print(f"  Overall Risk Level: {summary.overall_risk_final}")
    print(f"  Contract Completeness: {summary.contract_completeness_score}/100")
    print(f"  Document Length: {summary.document_length_words:,} words")
    print(f"  Clauses Analyzed: {len(report.clauses)}")
    
    if summary.top_risks:
        print("\n  Top Risks Identified:")
        for i, risk in enumerate(summary.top_risks[:3], 1):
            print(f"    {i}. {risk[:80]}...")
    
    return report.to_json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUSAGE:")
        print("  python main.py tract_file_path>")
        print("\nEXAMPLE:")
        print("  python main.py contracts/sample_agreement.pdf")
        print("\nSUPPORTED FORMATS:")
        print("  - PDF (.pdf)")
        print("  - Word Document (.docx)")
        print("  - Plain Text (.txt)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        result = run_analysis(file_path)
        
        # Save results
        output_file = "analysis_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print_header("OUTPUT")
        print_status(f"Analysis report saved to: {output_file}", "SUCCESS")
        print_status(f"File size: {os.path.getsize(output_file):,} bytes")
        print("\nAnalysis complete. Review the JSON file for detailed results.")
        
    except FileNotFoundError as e:
        print_status(f"File error: {str(e)}", "ERROR")
        sys.exit(1)
    except ValueError as e:
        print_status(f"Validation error: {str(e)}", "ERROR")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
