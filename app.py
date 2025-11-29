
import os
import sys


os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


import streamlit as st
import json
import io
import time
import locale
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    encoding='utf-8' if sys.version_info >= (3, 9) else None
)

logger = logging.getLogger(__name__)

from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from deep_translator import GoogleTranslator

try:
    from analyzer.extractor import extract_text
    from analyzer.preprocessor import preprocess_contract
    from analyzer.llm_model import ContractAnalyzer, LLMConfig
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from extractor import extract_text
    from preprocessor import preprocess_contract
    from llm_model import ContractAnalyzer, LLMConfig

# API Key Setup
API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("Missing API key. Set OPENAI_API_KEY in environment variables or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=API_KEY)



def sanitize_text(text: str) -> str:
    """Sanitize text to ensure UTF-8 compatibility"""
    try:
        if not isinstance(text, str):
            text = str(text)
        text = text.encode('utf-8', errors='replace').decode('utf-8')
        text = text.replace('\x00', '')
        return text
    except Exception as e:
        logger.error(f"Failed to sanitize text: {e}")
        return str(text)

def translate_to_hindi(text: str) -> str:
    """Translate English text to Hindi using deep-translator (100% FREE)"""
    if not text or not text.strip() or len(text.strip()) < 10:
        return text
    
    try:
        text = sanitize_text(text)
        
    
        max_length = 4500
        
        if len(text) > max_length:
            
            chunks = []
            current_pos = 0
            
            while current_pos < len(text):
                end_pos = min(current_pos + max_length, len(text))
                
                if end_pos < len(text):
                   
                    last_period = text.rfind('.', current_pos, end_pos)
                    if last_period > current_pos:
                        end_pos = last_period + 1
                
                chunk = text[current_pos:end_pos].strip()
                if chunk:
                    chunks.append(chunk)
                current_pos = end_pos
            
           
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"Translating chunk {i+1}/{len(chunks)}")
                    translated = GoogleTranslator(source='en', target='hi').translate(chunk)
                    translated_chunks.append(translated)
                    time.sleep(0.1)
                except Exception as chunk_error:
                    logger.error(f"Failed to translate chunk {i+1}: {chunk_error}")
                    translated_chunks.append(chunk)
            
            translated_text = " ".join(translated_chunks)
        else:
            translated_text = GoogleTranslator(source='en', target='hi').translate(text)
        
        if translated_text and any(0x0900 <= ord(c) <= 0x097F for c in translated_text):
            logger.info("✓ Successfully translated to Hindi")
            return translated_text
        else:
            logger.warning("Translation did not contain Devanagari characters")
            return text
        
    except Exception as e:
        logger.error(f"Translation failed: {type(e).__name__}: {e}")
        return text


# PDF GENERATION FUNCTIONS

def generate_professional_pdf(summary: dict, clauses: list, language: str = "english") -> io.BytesIO:
    """Generate PDF report in specified language (english/hindi)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    story = []
    
    # Title
    if language == "hindi":
        story.append(Paragraph("अनुबंध विश्लेषण रिपोर्ट", title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("कानूनी जोखिम मूल्यांकन और व्यापार विश्लेषण", styles['Heading2']))
    else:
        story.append(Paragraph("Contract Analysis Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Legal Risk Assessment & Business Analysis", styles['Heading2']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Metadata
    from datetime import datetime
    report_date = datetime.now().strftime("%B %d, %Y")
    
    if language == "hindi":
        story.append(Paragraph(f"<b>रिपोर्ट तिथि:</b> {report_date}", body_style))
        story.append(Paragraph(f"<b>दस्तावेज़ लंबाई:</b> {summary.get('document_length_words', 0)} शब्द", body_style))
    else:
        story.append(Paragraph(f"<b>Report Date:</b> {report_date}", body_style))
        story.append(Paragraph(f"<b>Document Length:</b> {summary.get('document_length_words', 0)} words", body_style))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    if language == "hindi":
        story.append(Paragraph("कार्यकारी सारांश", heading1_style))
    else:
        story.append(Paragraph("Executive Summary", heading1_style))
    
    summary_text = sanitize_text(summary.get("business_summary", "No summary available"))
    
    if language == "hindi":
        cache_key = "pdf_summary_hindi"
        if cache_key in st.session_state.translation_cache:
            summary_text = st.session_state.translation_cache[cache_key]
        else:
            summary_text = translate_to_hindi(summary_text)
            st.session_state.translation_cache[cache_key] = summary_text
    
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Risk Assessment
    if language == "hindi":
        story.append(Paragraph("जोखिम मूल्यांकन", heading1_style))
    else:
        story.append(Paragraph("Risk Assessment", heading1_style))
    
    overall_risk = summary.get("overall_risk_final", "Medium")
    risk_colors_map = {"Low": colors.green, "Medium": colors.orange, "High": colors.red}
    risk_color = risk_colors_map.get(overall_risk, colors.orange)
    
    if language == "hindi":
        story.append(Paragraph(f"<b>समग्र जोखिम स्तर:</b> <font color='{risk_color.hexval()}'>{overall_risk}</font>", body_style))
        story.append(Paragraph(f"<b>LLM मूल्यांकन:</b> {summary.get('overall_risk_llm', 'N/A')}", body_style))
        story.append(Paragraph(f"<b>नियम-आधारित:</b> {summary.get('overall_risk_rules', 'N/A')}", body_style))
    else:
        story.append(Paragraph(f"<b>Overall Risk Level:</b> <font color='{risk_color.hexval()}'>{overall_risk}</font>", body_style))
        story.append(Paragraph(f"<b>LLM Assessment:</b> {summary.get('overall_risk_llm', 'N/A')}", body_style))
        story.append(Paragraph(f"<b>Rule-Based:</b> {summary.get('overall_risk_rules', 'N/A')}", body_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Top Risks
    top_risks = summary.get("top_risks", [])
    if top_risks:
        if language == "hindi":
            story.append(Paragraph("महत्वपूर्ण व्यावसायिक जोखिम", heading1_style))
        else:
            story.append(Paragraph("Critical Business Risks", heading1_style))
        
        for i, risk in enumerate(top_risks, 1):
            risk_text = sanitize_text(risk)
            if language == "hindi":
                cache_key = f"pdf_risk_{i}_hindi"
                if cache_key in st.session_state.translation_cache:
                    risk_text = st.session_state.translation_cache[cache_key]
                else:
                    risk_text = translate_to_hindi(risk_text)
                    st.session_state.translation_cache[cache_key] = risk_text
            
            story.append(Paragraph(f"<b>{i}.</b> {risk_text}", body_style))
        story.append(Spacer(1, 0.3*inch))
    
    # Page break
    story.append(PageBreak())
    
    # Clause table
    if language == "hindi":
        story.append(Paragraph("विस्तृत खंड विश्लेषण", heading1_style))
        table_data = [["खंड #", "जोखिम", "स्कोर", "पक्ष"]]
    else:
        story.append(Paragraph("Detailed Clause Analysis", heading1_style))
        table_data = [["Clause #", "Risk", "Score", "Party"]]
    
    for c in clauses:
        table_data.append([
            str(c.get("clause_index", "")),
            c.get("risk_level_final", "Medium"),
            f"{c.get('final_risk_score', 0):.1f}",
            c.get("affected_party", "Unclear")
        ])
    
    t = Table(table_data, colWidths=[0.75*inch, 1.25*inch, 1*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_bilingual_pdf(summary: dict, clauses: list) -> io.BytesIO:
    """Generate bilingual PDF with English and Hindi side-by-side"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=8,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Contract Analysis Report<br/>अनुबंध विश्लेषण रिपोर्ट", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    summary_text_en = sanitize_text(summary.get("business_summary", "No summary available"))
    
    cache_key = "pdf_summary_hindi"
    if cache_key in st.session_state.translation_cache:
        summary_text_hi = st.session_state.translation_cache[cache_key]
    else:
        summary_text_hi = translate_to_hindi(summary_text_en)
        st.session_state.translation_cache[cache_key] = summary_text_hi
    
    summary_table = Table([
        ["English", "हिंदी (Hindi)"],
        [summary_text_en, summary_text_hi]
    ], colWidths=[3*inch, 3*inch])
    
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Risk info
    overall_risk = summary.get("overall_risk_final", "Medium")
    risk_table = Table([
        ["Overall Risk / समग्र जोखिम", overall_risk],
    ], colWidths=[3*inch, 3*inch])
    
    risk_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(risk_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# User Interface(UI)
st.set_page_config(
    page_title="Legal Contract Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .risk-high { color: #dc2626; font-weight: 600; }
    .risk-medium { color: #f59e0b; font-weight: 600; }
    .risk-low { color: #10b981; font-weight: 600; }
    .clause-header-high { color: #dc2626 !important; font-weight: 700 !important; }
    .clause-header-medium { color: #f59e0b !important; font-weight: 700 !important; }
    .clause-header-low { color: #10b981 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Legal Contract Analysis Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Risk Assessment & Business Intelligence for Commercial Agreements</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    model_name = st.selectbox(
        "Analysis Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0
    )
    
    st.divider()
    st.markdown("**About**")
    st.info("AI-powered contract analysis with FREE Hindi translation.")
    st.divider()
    
    logo_path = "/Users/sahirchoudhury/Downloads/Contract bot/assets/guviHclLogoText.webp"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown("""
    <div style="text-align:center; font-size:18px; font-weight:700; margin-top:10px;">
        Gen AI Hackathon 2025
    </div>
    <div style="text-align:center; font-size:14px; color:#6b7280; margin-top:5px;">
        Binary Force
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'translation_cache' not in st.session_state:
    st.session_state.translation_cache = {}
if 'display_language' not in st.session_state:
    st.session_state.display_language = 'english'

# File Upload
uploaded_file = st.file_uploader(
    "Upload Contract Document",
    type=["pdf", "docx", "txt"],
    help="Supported: PDF, DOCX, TXT | Max: 10MB"
)

if uploaded_file:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("File Name", uploaded_file.name)
    with col2:
        st.metric("File Size", f"{file_size_mb:.2f} MB")
    with col3:
        st.metric("Format", uploaded_file.type.split("/")[-1].upper())
    
    # Analysis Button
    if st.button("Begin Analysis", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Extract
            status_text.text("Step 1/3: Extracting text...")
            progress_bar.progress(10)
            text = extract_text(uploaded_file, uploaded_file.name)
            if not text or len(text.strip()) < 100:
                st.error("Failed to extract text.")
                st.stop()
            
            word_count = len(text.split())
            status_text.text(f"Step 1/3: Extracted {word_count:,} words")
            progress_bar.progress(30)
            time.sleep(0.5)
            
            # Preprocess
            status_text.text("Step 2/3: Preprocessing...")
            progress_bar.progress(40)
            anonymised_text, original_clauses, anonymised_clauses, anon = preprocess_contract(text)
            status_text.text(f"Step 2/3: Found {len(original_clauses)} clauses")
            progress_bar.progress(60)
            time.sleep(0.5)
            
            # Analyze (always English)
            status_text.text("Step 3/3: AI analysis (English)...")
            progress_bar.progress(70)
            
            config = LLMConfig(model_name=model_name, temperature=0.1, max_tokens=3000)
            analyzer = ContractAnalyzer(api_key=API_KEY, config=config)
            
            report = analyzer.analyze_contract(
                original_clauses=original_clauses,
                anonymised_clauses=anonymised_clauses,
                full_text=text,
                language="English"
            )
            
            result = report.to_json()
            st.session_state.analysis_result = result
            st.session_state.translation_cache = {}
            st.session_state.display_language = 'english'
            
            status_text.text("Analysis Complete ✓")
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            st.success("✓ Analysis completed!")
            st.info("📝 Use buttons below to view in Hindi")
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            logger.exception("Analysis error")

# Display Results
if st.session_state.analysis_result:
    st.divider()
    st.header("Analysis Results")
    
    result = st.session_state.analysis_result
    summary = result["summary"]
    
    # Language Buttons
    st.subheader("Report Language")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🇬🇧 English", use_container_width=True, 
                    type="primary" if st.session_state.display_language == 'english' else "secondary"):
            st.session_state.display_language = 'english'
            st.rerun()
    
    with col2:
        if st.button("🇮🇳 हिंदी", use_container_width=True,
                    type="primary" if st.session_state.display_language == 'hindi' else "secondary"):
            st.session_state.display_language = 'hindi'
            st.rerun()
    
    with col3:
        if st.button("🌐 Bilingual", use_container_width=True,
                    type="primary" if st.session_state.display_language == 'bilingual' else "secondary"):
            st.session_state.display_language = 'bilingual'
            st.rerun()
    
    display_mode = st.session_state.display_language
    
    st.divider()
    
    # Executive Summary
    st.subheader("Executive Summary")
    summary_text = summary.get("business_summary", "")
    
    if not summary_text:
        summary_text = "Contract requires legal review."
    
    if display_mode == "english":
        st.write(summary_text)
    
    elif display_mode == "hindi":
        cache_key = "summary_hindi"
        if cache_key not in st.session_state.translation_cache:
            with st.spinner("🔄 Translating..."):
                translated = translate_to_hindi(summary_text)
                st.session_state.translation_cache[cache_key] = translated
        st.write(st.session_state.translation_cache[cache_key])
    
    else:  # bilingual
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**English**")
            st.write(summary_text)
        with col2:
            st.markdown("**हिंदी**")
            cache_key = "summary_hindi"
            if cache_key not in st.session_state.translation_cache:
                with st.spinner("🔄 Translating..."):
                    translated = translate_to_hindi(summary_text)
                    st.session_state.translation_cache[cache_key] = translated
            st.write(st.session_state.translation_cache[cache_key])
    
    st.divider()
    
    # Risk Assessment
    st.subheader("Risk Assessment")
    overall_risk = summary.get("overall_risk_final", "Medium")
    risk_class = f"risk-{overall_risk.lower()}"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h3 class="{risk_class}">Overall Risk</h3><h2>{overall_risk}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>LLM</h3><h2>{summary.get("overall_risk_llm", "N/A")}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>Rule-Based</h3><h2>{summary.get("overall_risk_rules", "N/A")}</h2></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Top Risks
    top_risks = summary.get("top_risks", [])
    if top_risks:
        st.subheader("Critical Business Risks")
        
        for i, risk in enumerate(top_risks, 1):
            if display_mode == "english":
                st.markdown(f"{i}. {risk}")
            elif display_mode == "hindi":
                cache_key = f"risk_{i}_hindi"
                if cache_key not in st.session_state.translation_cache:
                    st.session_state.translation_cache[cache_key] = translate_to_hindi(risk)
                st.markdown(f"{i}. {st.session_state.translation_cache[cache_key]}")
            else:  # bilingual
                col1, col2 = st.columns(2)
                with col1:
                    if i == 1:
                        st.markdown("**English**")
                    st.markdown(f"{i}. {risk}")
                with col2:
                    if i == 1:
                        st.markdown("**हिंदी**")
                    cache_key = f"risk_{i}_hindi"
                    if cache_key not in st.session_state.translation_cache:
                        st.session_state.translation_cache[cache_key] = translate_to_hindi(risk)
                    st.markdown(f"{i}. {st.session_state.translation_cache[cache_key]}")
        
        st.divider()
    
    # Clause Analysis
    st.subheader("Clause-by-Clause Analysis")
    
    risk_filter = st.multiselect(
        "Filter by Risk Level",
        ["Low", "Medium", "High"],
        default=["Medium", "High"]
    )
    
    filtered_clauses = [c for c in result["clauses"] if c.get("risk_level_final", "Medium") in risk_filter]
    st.write(f"Showing {len(filtered_clauses)} of {len(result['clauses'])} clauses")
    
    for clause in filtered_clauses:
        risk_level = clause.get("risk_level_final", "Medium")
        clause_header_class = f"clause-header-{risk_level.lower()}"
        clause_title = f"Clause {clause['clause_index']} | Risk: {risk_level} | Score: {clause.get('final_risk_score', 0):.1f}/100"
        
        with st.expander(clause_title):
            st.markdown(f'<p class="{clause_header_class}">{clause_title}</p>', unsafe_allow_html=True)
            
            st.markdown("**Original Text**")
            st.text(clause.get("original_text", "")[:600])
            
            st.markdown("**Analysis**")
            explanation = clause.get("plain_english_explanation", "")
            
            if display_mode == "english":
                st.write(explanation)
            elif display_mode == "hindi":
                cache_key = f"clause_{clause['clause_index']}_hindi"
                if cache_key not in st.session_state.translation_cache:
                    with st.spinner("🔄 Translating..."):
                        st.session_state.translation_cache[cache_key] = translate_to_hindi(explanation)
                st.write(st.session_state.translation_cache[cache_key])
            else:  # bilingual
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**English**")
                    st.write(explanation)
                with col2:
                    st.markdown("**हिंदी**")
                    cache_key = f"clause_{clause['clause_index']}_hindi"
                    if cache_key not in st.session_state.translation_cache:
                        with st.spinner("🔄 Translating..."):
                            st.session_state.translation_cache[cache_key] = translate_to_hindi(explanation)
                    st.write(st.session_state.translation_cache[cache_key])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**LLM Risk:** {clause.get('risk_level_llm', 'N/A')}")
            with col2:
                st.markdown(f"**Affected Party:** {clause.get('affected_party', 'Unclear')}")
    
    st.divider()
    
    # Export Reports
    st.subheader("Export Report")
    
    current_language = st.session_state.display_language
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="**Download JSON**",
            data=json_str,
            file_name=f"analysis_{uploaded_file.name}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # PDF in current language
        if current_language == "english":
            pdf_label = "**Download PDF (English)**"
            pdf_file = f"analysis_en_{uploaded_file.name}.pdf"
            with st.spinner("Generating PDF..."):
                pdf_buffer = generate_professional_pdf(summary, result["clauses"], "english")
        
        elif current_language == "hindi":
            pdf_label = "**Download PDF (हिंदी)**"
            pdf_file = f"analysis_hi_{uploaded_file.name}.pdf"
            with st.spinner("Generating Hindi PDF..."):
                pdf_buffer = generate_professional_pdf(summary, result["clauses"], "hindi")
        
        else:  # bilingual
            pdf_label = "**Download PDF (Bilingual)**"
            pdf_file = f"analysis_bilingual_{uploaded_file.name}.pdf"
            with st.spinner("Generating Bilingual PDF..."):
                pdf_buffer = generate_bilingual_pdf(summary, result["clauses"])
        
        st.download_button(
            label=pdf_label,
            data=pdf_buffer,
            file_name=pdf_file,
            mime="application/pdf",
            use_container_width=True
        )

else:
    st.info("**Upload a contract document to start analysis**")
    
    with st.expander("Platform Capabilities"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Analysis Features:**
            - Multi-format support
            - AI-powered analysis
            - Rule-based risk assessment
            - FREE Hindi translation
            - PDF export in 3 languages
            """)
        
        with col2:
            st.markdown("""
            **Risk Intelligence:**
            - Risk scoring
            - Party impact analysis
            - Alternative suggestions
            - Negotiation strategies
            - Quality metrics
            """)
