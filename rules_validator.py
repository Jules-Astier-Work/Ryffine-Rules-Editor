import pandas as pd
import streamlit as st

from validators import RyffineDITAValidator
import pyperclip

st.set_page_config(
    page_title="RyffineDITA Validator",
    page_icon="📝",
    layout="wide"
)

def copy_text_backend(text):
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(e)
        return False

def display_comment_box(key: str, label: str = "Comments"):
    """Display a comment text area"""
    return st.text_area(
        label,
        key=key,
        height=100,
        placeholder="Add your comments here..."
    )

st.markdown("Upload a document or paste text to validate and add comments")
    
# Initialize session state
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

# Input section
st.header("Input Document")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Upload File")
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['dita', 'ditamap', 'xml'],
        help="Upload a RyffineDITA document for validation"
    )

with col2:
    st.subheader("Or Paste Text")
    pasted_text = st.text_area(
        "Paste your text here",
        height=200,
        placeholder="Paste your document content here..."
    )

# Get content from either source
content = ""
if uploaded_file is not None:
    try:
        # Read the uploaded file
        if uploaded_file.type == "text/plain":
            content = str(uploaded_file.read(), "utf-8")
        else:
            # For other file types, treat as text
            content = str(uploaded_file.read(), "utf-8")
        st.success(f"File '{uploaded_file.name}' loaded successfully!")
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
elif pasted_text:
    content = pasted_text

# Validation button
if st.button("🔍 Validate Document", type="primary", disabled=not content):
    if content:
        with st.spinner("Validating document..."):
            validator  = RyffineDITAValidator()
            st.session_state["validation_results"] = validator.validate_content(content)
        st.success("Validation completed!")
    else:
        st.error("Please provide content to validate")

# Display results
if st.session_state["validation_results"]:
    results = st.session_state["validation_results"]
    
    st.header("📊 Validation Results")
    # Copy Report
    if st.button("📑 Copy Report"):
        if copy_text_backend(results["llm_report"]):
            st.success("Copied!")
        else:
            st.error("Failed to copy")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    error_count = sum([len(errors) for errors in results["report_data"]["line_errors"].values()])
    with col1:
        st.metric("Errors Found", error_count)
    with col2:
        st.metric("Definitions Found", len(results["report_data"]["definitions"]))
    with col3:
        st.metric("Status", "Complete" if error_count == 0 else "Issues Found")
    
    # Prettified content section
    st.subheader("✨ Prettified Document")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.code(
            results["report_data"]["content"],
            height=300,
            language="xmlDoc",
        )
    
    with col2:
        display_comment_box("prettified_comments", "Document Comments")
    
    # Errors section
    if len(results["report_data"]["line_errors"]) > 0:
        st.subheader("🚨 Errors Found")

        # Sort line numbers for consistent display
        for line_num, errors in results["report_data"]["line_errors"].items():
            
            with st.expander(f"Line {line_num} ({len(errors)} error{'s' if len(errors) > 1 else ''})", expanded=False):
                
                for i, error in enumerate(errors):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(error)
                    
                    with col2:
                        display_comment_box(f"error_comment_line_{line_num}_error_{i}", "Error Comments")
                    
                    if i < len(errors) - 1:  # Add separator between errors on same line
                        st.divider()

    
    # Definitions section
    if len(results["report_data"]["definitions"]) > 0:
        st.subheader("📚 Definitions Found")
        
        for i, (definition) in enumerate(results["report_data"]["definitions"]):
            with st.expander(f"Element Definition:", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.code(
                        definition,
                        language="xmlDoc",
                    )
                
                with col2:
                    display_comment_box(f"definition_comment_{i}", "Definition Comments")

    # Export comments section
    st.subheader("💾 Export Comments")
    if st.button("📥 Export All Comments"):
        report_data = []
        comments_data = []
        
        # Collect all comments
        if "prettified_comments" in st.session_state:
            if st.session_state["prettified_comments"]:
                report_data.append(results["report_data"]["content"])
                comments_data.append(st.session_state['prettified_comments'])
        
        for line_num, errors in results["report_data"]["line_errors"].items():
            for i, error in enumerate(errors):
                if f"error_comment_line_{line_num}_error_{i}" in st.session_state:
                    if st.session_state[f"error_comment_line_{line_num}_error_{i}"]:
                        report_data.append(error)
                        comments_data.append(st.session_state[f"error_comment_line_{line_num}_error_{i}"])
        
        for i, definition in enumerate(results["report_data"]["definitions"]):
            if f"definition_comment_{i}" in st.session_state:
                if st.session_state[f"definition_comment_{i}"]:
                    report_data.append(definition)
                    comments_data.append(st.session_state[f'definition_comment_{i}'])
        
        if comments_data and report_data:
            report_df = pd.DataFrame({
                "report_data": report_data,
                "comments": comments_data
            })
            csv = report_df.to_csv(index=False)

            st.download_button(
                label="📄 Download Comments",
                data=csv,
                file_name='report_comments.csv',
                mime='text/csv'
            )
        else:
            st.info("No comments to export")