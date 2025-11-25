"""Streamlit UI for Autonomous QA Agent."""
import streamlit as st
import requests
import json
from pathlib import Path
import pandas as pd
from typing import List, Dict

# API Configuration
API_BASE_URL = "http://localhost:8000"

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


def check_api_health():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Sidebar
with st.sidebar:
    st.markdown("### 🤖 Autonomous QA Agent")
    st.markdown("---")
    
    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Not Available")
        st.info("Please start the FastAPI backend:\n```\npython backend/app.py\n```")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["📚 Knowledge Base", "🧪 Test Case Generator", "🔧 Selenium Generator"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool uses:
    - **Google Gemini** for LLM
    - **FAISS** for vector storage
    - **LangChain** for RAG
    - **BeautifulSoup** for HTML parsing
    """)


# Page 1: Knowledge Base
if page == "📚 Knowledge Base":
    st.markdown('<p class="main-header">📚 Knowledge Base Builder</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload support documents and checkout HTML to build the knowledge base for test case generation.
    """)
    
    # File upload section
    st.markdown('<p class="sub-header">Upload Documents</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Support Documents**")
        support_docs = st.file_uploader(
            "Upload support docs (MD, TXT, JSON, PDF)",
            type=['md', 'txt', 'json', 'pdf'],
            accept_multiple_files=True,
            key="support_docs"
        )
        
        if support_docs:
            st.info(f"📄 {len(support_docs)} document(s) uploaded")
            for doc in support_docs:
                st.text(f"  • {doc.name}")
    
    with col2:
        st.markdown("**Checkout HTML**")
        checkout_html = st.file_uploader(
            "Upload checkout.html",
            type=['html', 'htm'],
            key="checkout_html"
        )
        
        if checkout_html:
            st.info(f"🌐 {checkout_html.name}")
    
    # Build button
    st.markdown("---")
    
    if st.button("🔨 Build Knowledge Base", type="primary", disabled=not api_healthy):
        if not support_docs and not checkout_html:
            st.error("Please upload at least one document")
        else:
            with st.spinner("Building knowledge base... This may take a moment."):
                try:
                    # Prepare files for upload
                    files = []
                    
                    if support_docs:
                        for doc in support_docs:
                            files.append(('files', (doc.name, doc.getvalue(), doc.type)))
                    
                    if checkout_html:
                        files.append(('files', (checkout_html.name, checkout_html.getvalue(), checkout_html.type)))
                    
                    # Send to API
                    response = requests.post(
                        f"{API_BASE_URL}/build_kb",
                        files=files
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.kb_built = True
                        
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.success("✅ Knowledge Base Built Successfully!")
                        st.markdown(f"""
                        **Statistics:**
                        - **Chunks Created:** {result['chunks']}
                        - **Sources Processed:** {len(result['sources'])}
                        - **Index Path:** `{result['index_path']}`
                        
                        **Sources:**
                        """)
                        for source in result['sources']:
                            st.text(f"  • {source}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Fetch selector map if checkout.html was uploaded
                        if checkout_html:
                            try:
                                sel_response = requests.get(f"{API_BASE_URL}/selectors")
                                if sel_response.status_code == 200:
                                    sel_data = sel_response.json()
                                    st.session_state.selector_map = sel_data.get('selectors', {})
                                    st.info(f"🎯 Extracted {sel_data['selector_count']} selectors from checkout.html")
                            except Exception as e:
                                st.warning(f"Could not fetch selectors: {e}")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Error building knowledge base: {str(e)}")
    
    # Status display
    if st.session_state.kb_built:
        st.markdown("---")
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.info("✅ Knowledge base is ready. You can now generate test cases!")
        st.markdown('</div>', unsafe_allow_html=True)


# Page 2: Test Case Generator
elif page == "🧪 Test Case Generator":
    st.markdown('<p class="main-header">🧪 Test Case Generator</p>', unsafe_allow_html=True)
    
    if not st.session_state.kb_built:
        st.warning("⚠️ Please build the knowledge base first in the 'Knowledge Base' page")
    else:
        st.markdown("Generate test cases using RAG-powered AI based on your uploaded documentation.")
        
        # Query input
        st.markdown('<p class="sub-header">Query Input</p>', unsafe_allow_html=True)
        
        query = st.text_area(
            "Enter your test case generation query",
            placeholder="Example: Generate all positive and negative test cases for the discount code feature",
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            top_k = st.slider("Number of chunks to retrieve", min_value=3, max_value=10, value=5)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_btn = st.button("🚀 Generate Test Cases", type="primary", disabled=not api_healthy)
        
        # Generate test cases
        if generate_btn:
            if not query.strip():
                st.error("Please enter a query")
            else:
                with st.spinner("Generating test cases... This may take a moment."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/generate_testcases",
                            json={"query": query, "top_k": top_k}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.test_cases = result['test_cases']
                            
                            st.success(f"✅ Generated {len(result['test_cases'])} test cases")
                            
                            # Show used chunks
                            with st.expander("📚 Retrieved Source Chunks"):
                                for i, chunk in enumerate(result['used_chunks']):
                                    st.markdown(f"**Chunk {i+1}:** {chunk['source']}")
                                    st.text(chunk['preview'])
                                    st.markdown("---")
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error generating test cases: {str(e)}")
        
        # Display test cases
        if st.session_state.test_cases:
            st.markdown("---")
            st.markdown('<p class="sub-header">Generated Test Cases</p>', unsafe_allow_html=True)
            
            # Create DataFrame for display
            df_data = []
            for tc in st.session_state.test_cases:
                df_data.append({
                    "Test ID": tc['Test_ID'],
                    "Feature": tc['Feature'],
                    "Test Scenario": tc['Test_Scenario'][:80] + "...",
                    "Type": tc['Test_Type'],
                    "Steps": len(tc['Steps'])
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Test case selector
            st.markdown("---")
            test_id_list = [tc['Test_ID'] for tc in st.session_state.test_cases]
            selected_id = st.selectbox("Select a test case to view details", test_id_list)
            
            if selected_id:
                selected_tc = next(tc for tc in st.session_state.test_cases if tc['Test_ID'] == selected_id)
                st.session_state.selected_test_case = selected_tc
                
                # Display full test case
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Test ID:** {selected_tc['Test_ID']}")
                    st.markdown(f"**Feature:** {selected_tc['Feature']}")
                    st.markdown(f"**Test Type:** {selected_tc['Test_Type']}")
                    st.markdown(f"**Scenario:** {selected_tc['Test_Scenario']}")
                
                with col2:
                    st.markdown("**Preconditions:**")
                    for p in selected_tc['Preconditions']:
                        st.text(f"  • {p}")
                    
                    st.markdown("**Selectors Needed:**")
                    for s in selected_tc['SelectorsNeeded']:
                        st.text(f"  • {s}")
                
                st.markdown("**Test Steps:**")
                for i, step in enumerate(selected_tc['Steps'], 1):
                    st.text(f"{i}. {step}")
                
                st.markdown(f"**Expected Result:** {selected_tc['Expected_Result']}")
                
                st.markdown("**Grounded In:**")
                for g in selected_tc['Grounded_In']:
                    st.text(f"  • {g}")
                
                # Download JSON
                json_str = json.dumps(selected_tc, indent=2)
                st.download_button(
                    "📥 Download Test Case (JSON)",
                    data=json_str,
                    file_name=f"{selected_tc['Test_ID']}.json",
                    mime="application/json"
                )


# Page 3: Selenium Generator
elif page == "🔧 Selenium Generator":
    st.markdown('<p class="main-header">🔧 Selenium Script Generator</p>', unsafe_allow_html=True)
    
    if not st.session_state.selected_test_case:
        st.warning("⚠️ Please select a test case from the 'Test Case Generator' page first")
    else:
        tc = st.session_state.selected_test_case
        
        st.markdown(f"### Selected Test Case: {tc['Test_ID']}")
        st.markdown(f"**Feature:** {tc['Feature']}")
        st.markdown(f"**Scenario:** {tc['Test_Scenario']}")
        
        # Display test case JSON
        with st.expander("📋 View Full Test Case"):
            st.json(tc)
        
        # Selector map editor
        st.markdown("---")
        st.markdown('<p class="sub-header">Selector Map</p>', unsafe_allow_html=True)
        
        if st.session_state.selector_map:
            st.info(f"🎯 {len(st.session_state.selector_map)} selectors available")
            
            with st.expander("View/Edit Selector Map"):
                # Convert to editable format
                selector_json = json.dumps(st.session_state.selector_map, indent=2)
                edited_selectors = st.text_area(
                    "Selector Map (JSON)",
                    value=selector_json,
                    height=300
                )
                
                if st.button("Update Selector Map"):
                    try:
                        st.session_state.selector_map = json.loads(edited_selectors)
                        st.success("✅ Selector map updated")
                    except Exception as e:
                        st.error(f"Invalid JSON: {e}")
        else:
            st.warning("No selector map available. Please upload checkout.html in the Knowledge Base page.")
        
        # Generate button
        st.markdown("---")
        if st.button("🚀 Generate Selenium Script", type="primary", disabled=not api_healthy):
            with st.spinner("Generating Selenium script..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/generate_selenium",
                        json={"test_case": tc}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('missing_selectors'):
                            st.warning(f"⚠️ Missing selectors: {', '.join(result['missing_selectors'])}")
                        
                        st.success("✅ Selenium script generated successfully!")
                        
                        # Display script
                        st.markdown('<p class="sub-header">Generated Script</p>', unsafe_allow_html=True)
                        st.code(result['script'], language='python')
                        
                        # Download button
                        st.download_button(
                            "📥 Download Selenium Script",
                            data=result['script'],
                            file_name=f"test_{tc['Test_ID'].lower().replace('-', '_')}.py",
                            mime="text/x-python"
                        )
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error generating script: {str(e)}")


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Autonomous QA Agent v1.0 | Powered by Google Gemini, LangChain & FAISS</p>
</div>
""", unsafe_allow_html=True)
