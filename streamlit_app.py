"""Standalone Streamlit app with integrated backend logic."""
import streamlit as st
import sys
from pathlib import Path
import json
import tempfile
import shutil
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.parsers import DocumentParser
from backend.vectorstore import VectorStoreManager
from backend.rag import RAGEngine
from backend.selenium_gen import SeleniumScriptGenerator
from backend.py_selectors import SelectorExtractor
from backend.models import TestCase
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Autonomous QA Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        padding: 1rem;
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'selected_test_case' not in st.session_state:
    st.session_state.selected_test_case = None
if 'selector_map' not in st.session_state:
    st.session_state.selector_map = {}
if 'kb_built' not in st.session_state:
    st.session_state.kb_built = False
if 'vectorstore_manager' not in st.session_state:
    st.session_state.vectorstore_manager = VectorStoreManager()
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = RAGEngine()
if 'selenium_generator' not in st.session_state:
    st.session_state.selenium_generator = SeleniumScriptGenerator()
if 'selector_extractor' not in st.session_state:
    st.session_state.selector_extractor = SelectorExtractor()

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 Autonomous QA Agent")
    st.markdown("---")
    
    # Status
    st.success("✅ Backend Integrated")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["📚 Knowledge Base", "🧪 Test Case Generator", "🔧 Selenium Generator"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("AI-powered test case and Selenium script generator using RAG.")

# ============================================================================
# PAGE 1: KNOWLEDGE BASE BUILDER
# ============================================================================
if page == "📚 Knowledge Base":
    st.markdown('<div class="main-header">📚 Knowledge Base Builder</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload your support documents and checkout HTML file to build the knowledge base.
    The system will parse documents, create embeddings, and extract selectors.
    """)
    
    # File uploaders
    st.markdown('<div class="sub-header">Upload Support Documents</div>', unsafe_allow_html=True)
    support_files = st.file_uploader(
        "Upload documentation files (MD, TXT, JSON, PDF)",
        type=['md', 'txt', 'json', 'pdf'],
        accept_multiple_files=True,
        key="support_docs"
    )
    
    st.markdown('<div class="sub-header">Upload Checkout HTML</div>', unsafe_allow_html=True)
    html_file = st.file_uploader(
        "Upload checkout.html for selector extraction",
        type=['html'],
        key="checkout_html"
    )
    
    # Build button
    if st.button("🔨 Build Knowledge Base", type="primary", use_container_width=True):
        if not support_files:
            st.error("Please upload at least one support document")
        elif not html_file:
            st.error("Please upload checkout.html file")
        else:
            with st.spinner("Building knowledge base..."):
                try:
                    # Save uploaded files to temp directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        
                        # Save support documents
                        doc_files = []
                        for file in support_files:
                            file_path = temp_path / file.name
                            with open(file_path, 'wb') as f:
                                f.write(file.getbuffer())
                            doc_files.append(file_path)
                        
                        # Save HTML file
                        html_path = temp_path / html_file.name
                        with open(html_path, 'wb') as f:
                            f.write(html_file.getbuffer())
                        
                        # Extract selectors
                        st.session_state.selector_map = st.session_state.selector_extractor.extract_selectors_from_html(html_path)
                        
                        # Parse documents
                        documents = DocumentParser.files_to_documents(doc_files)
                        
                        # Create vector store
                        result = st.session_state.vectorstore_manager.create_vectorstore(documents)
                        
                        if result['status'] == 'ok':
                            st.session_state.kb_built = True
                            
                            st.success(f"""
                            ✅ Knowledge Base Built Successfully!
                            - **Chunks Created:** {result['chunks']}
                            - **Sources:** {len(result['sources'])} files
                            - **Selectors Extracted:** {len(st.session_state.selector_map)}
                            """)
                            
                            # Show selector map
                            with st.expander("📋 View Extracted Selectors"):
                                st.json(st.session_state.selector_map)
                        else:
                            st.error(f"Error: {result.get('message', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error building knowledge base: {str(e)}")

# ============================================================================
# PAGE 2: TEST CASE GENERATOR
# ============================================================================
elif page == "🧪 Test Case Generator":
    st.markdown('<div class="main-header">🧪 Test Case Generator</div>', unsafe_allow_html=True)
    
    if not st.session_state.kb_built:
        st.warning("⚠️ Please build the knowledge base first!")
        if st.button("Go to Knowledge Base"):
            st.rerun()
    else:
        st.markdown("Generate test cases using RAG-powered AI based on your documentation.")
        
        # Query input
        query = st.text_area(
            "Enter your test case generation query",
            placeholder="Example: Generate all positive and negative test cases for discount code feature",
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            top_k = st.slider("Number of document chunks to retrieve (top_k)", 1, 10, 5)
        
        # Generate button
        if st.button("🎯 Generate Test Cases", type="primary", use_container_width=True):
            if not query:
                st.error("Please enter a query")
            else:
                with st.spinner("Generating test cases..."):
                    try:
                        result = st.session_state.rag_engine.generate_test_cases(query, top_k)
                        
                        if result['status'] == 'ok':
                            st.session_state.test_cases = result['test_cases']
                            
                            st.success(f"✅ Generated {len(result['test_cases'])} test cases!")
                            
                            # Display test cases in table
                            if result['test_cases']:
                                st.markdown('<div class="sub-header">Generated Test Cases</div>', unsafe_allow_html=True)
                                
                                df_data = []
                                for tc in result['test_cases']:
                                    df_data.append({
                                        'Test ID': tc.Test_ID,
                                        'Feature': tc.Feature,
                                        'Scenario': tc.Test_Scenario,
                                        'Type': tc.Test_Type
                                    })
                                
                                df = pd.DataFrame(df_data)
                                st.dataframe(df, use_container_width=True)
                                
                                # Select test case for details
                                st.markdown('<div class="sub-header">Test Case Details</div>', unsafe_allow_html=True)
                                selected_id = st.selectbox(
                                    "Select a test case to view details",
                                    [tc.Test_ID for tc in result['test_cases']]
                                )
                                
                                selected_tc = next(tc for tc in result['test_cases'] if tc.Test_ID == selected_id)
                                st.session_state.selected_test_case = selected_tc
                                
                                # Display details
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Preconditions:**")
                                    for i, pre in enumerate(selected_tc.Preconditions, 1):
                                        st.write(f"{i}. {pre}")
                                    
                                    st.write("**Steps:**")
                                    for i, step in enumerate(selected_tc.Steps, 1):
                                        st.write(f"{i}. {step}")
                                
                                with col2:
                                    st.write("**Expected Result:**")
                                    st.write(selected_tc.Expected_Result)
                                    
                                    st.write("**Grounded In:**")
                                    for source in selected_tc.Grounded_In:
                                        st.write(f"- {source}")
                                    
                                    st.write("**Selectors Needed:**")
                                    for selector in selected_tc.SelectorsNeeded:
                                        st.write(f"- {selector}")
                                
                                # Download button
                                st.download_button(
                                    "📥 Download Test Case as JSON",
                                    data=json.dumps(selected_tc.model_dump(), indent=2),
                                    file_name=f"test_case_{selected_tc.Test_ID}.json",
                                    mime="application/json"
                                )
                        else:
                            st.error(f"Error: {result.get('message', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"Error generating test cases: {str(e)}")

# ============================================================================
# PAGE 3: SELENIUM GENERATOR
# ============================================================================
elif page == "🔧 Selenium Generator":
    st.markdown('<div class="main-header">🔧 Selenium Script Generator</div>', unsafe_allow_html=True)
    
    if not st.session_state.test_cases:
        st.warning("⚠️ Please generate test cases first!")
        if st.button("Go to Test Case Generator"):
            st.rerun()
    else:
        st.markdown("Generate Selenium automation scripts from your test cases.")
        
        # Select test case
        selected_id = st.selectbox(
            "Select a test case",
            [tc.Test_ID for tc in st.session_state.test_cases],
            format_func=lambda x: f"{x}: {next(tc.Test_Scenario for tc in st.session_state.test_cases if tc.Test_ID == x)}"
        )
        
        selected_tc = next(tc for tc in st.session_state.test_cases if tc.Test_ID == selected_id)
        
        # Show selector map
        st.markdown('<div class="sub-header">Selector Map</div>', unsafe_allow_html=True)
        st.json(st.session_state.selector_map)
        
        # Generate button
        if st.button("🤖 Generate Selenium Script", type="primary", use_container_width=True):
            with st.spinner("Generating Selenium script..."):
                try:
                    result = st.session_state.selenium_generator.generate_script(
                        selected_tc,
                        st.session_state.selector_map
                    )
                    
                    if result['status'] == 'ok':
                        st.success("✅ Selenium script generated!")
                        
                        # Display script
                        st.markdown('<div class="sub-header">Generated Script</div>', unsafe_allow_html=True)
                        st.code(result['script'], language='python')
                        
                        # Download button
                        st.download_button(
                            "📥 Download Selenium Script",
                            data=result['script'],
                            file_name=f"selenium_test_{selected_tc.Test_ID}.py",
                            mime="text/x-python"
                        )
                        
                        if result['missing_selectors']:
                            st.warning(f"⚠️ Missing selectors: {', '.join(result['missing_selectors'])}")
                    else:
                        st.error(f"Error: {result.get('message', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error generating Selenium script: {str(e)}")
