import pandas as pd
import streamlit as st

from validators import RyffineDITAValidator
import pyperclip
import streamlit.components.v1 as components

st.set_page_config(
    page_title="RyffineDITA Validator",
    page_icon="📝",
    layout="wide"
)

def copy_to_clipboard(text, button_text="📑Copy to Clipboard", key=None):
    """
    Create a copy-to-clipboard button that matches Streamlit's default button styling
    
    Args:
        text (str): Text to copy to clipboard
        button_text (str): Text to display on the button
        key (str): Unique key for the component (useful if using multiple buttons)
    """
    # Escape text for JavaScript
    escaped_text = text.replace('`', '\\`').replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
    
    # Generate unique ID for this button
    button_id = f"copy_btn_{key}" if key else "copy_btn"
    
    copy_js = f"""
    <div>
        <style>
            .stCopyButton {{
                background-color: rgb(255, 255, 255);
                border: 1px solid rgb(204, 204, 204);
                border-radius: 0.5rem;
                box-sizing: border-box;
                color: rgb(38, 39, 48);
                cursor: pointer;
                display: inline-block;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 14px;
                font-weight: 400;
                height: 3rem;
                line-height: 1.6;
                margin: 0px;
                padding: 0.375rem 0.75rem;
                text-align: center;
                text-decoration: none;
                transition: all 200ms ease 0s;
                user-select: none;
                vertical-align: middle;
                white-space: nowrap;
                width: auto;
                min-width: auto;
            }}
            
            .stCopyButton:hover {{
                border-color: rgb(255, 75, 75);
                color: rgb(255, 75, 75);
            }}
            
            .stCopyButton:focus {{
                border-color: rgb(255, 75, 75);
                box-shadow: rgb(255, 75, 75) 0px 0px 0px 0.2rem;
                color: rgb(255, 75, 75);
                outline: none;
            }}
            
            .stCopyButton:active {{
                background-color: rgb(245, 245, 245);
                border-color: rgb(204, 204, 204);
                color: rgb(38, 39, 48);
            }}
            
            /* Dark mode support */
            @media (prefers-color-scheme: dark) {{
                .stCopyButton {{
                    background-color: rgb(38, 39, 48);
                    border-color: rgb(58, 58, 58);
                    color: rgb(250, 250, 250);
                }}
                
                .stCopyButton:active {{
                    background-color: rgb(58, 58, 58);
                    border-color: rgb(58, 58, 58);
                }}
            }}
            
            .success-message {{
                color: rgb(9, 171, 59);
                font-size: 14px;
                margin-top: 0.5rem;
                display: none;
            }}
            
            .error-message {{
                color: rgb(255, 43, 43);
                font-size: 14px;
                margin-top: 0.5rem;
                display: none;
            }}
        </style>
        
        <button class="stCopyButton" onclick="copyToClipboard_{button_id}()" id="{button_id}">
            {button_text}
        </button>
        
        <script>
            function copyToClipboard_{button_id}() {{
                const textToCopy = `{escaped_text}`;
                
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(textToCopy).then(function() {{
                        showMessage_{button_id}('success');
                        alert('Copied to clipboard!');
                    }}, function(err) {{
                        console.error('Could not copy text: ', err);
                        fallbackCopyTextToClipboard_{button_id}(textToCopy);
                    }});
                }} else {{
                    fallbackCopyTextToClipboard_{button_id}(textToCopy);
                }}
            }}
            
            function fallbackCopyTextToClipboard_{button_id}(text) {{
                const textArea = document.createElement("textarea");
                textArea.value = text;
                
                // Avoid scrolling to bottom
                textArea.style.top = "0";
                textArea.style.left = "0";
                textArea.style.position = "fixed";
                
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {{
                    const successful = document.execCommand('copy');
                    if (successful) {{
                        showMessage_{button_id}('success');
                    }} else {{
                        showMessage_{button_id}('error');
                    }}
                }} catch (err) {{
                    console.error('Fallback: Could not copy text: ', err);
                    showMessage_{button_id}('error');
                }}
                
                document.body.removeChild(textArea);
            }}
            
            function showMessage_{button_id}(type) {{
                // Hide all messages first
                document.getElementById('success_{button_id}').style.display = 'none';
                document.getElementById('error_{button_id}').style.display = 'none';
                
                // Show the appropriate message
                document.getElementById(type + '_{button_id}').style.display = 'block';
                
                // Hide message after 3 seconds
                setTimeout(function() {{
                    document.getElementById(type + '_{button_id}').style.display = 'none';
                }}, 3000);
            }}
        </script>
    </div>
    """
    
    components.html(copy_js, height=100)

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
    copy_to_clipboard(results["llm_report"])
    # if st.button("📑 Copy Report"):
    #     copied = copy_text_backend(results["llm_report"])
    #     if copied == True:
    #         st.success("Copied!")
    #     else:
    #         st.error(copied)
    
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