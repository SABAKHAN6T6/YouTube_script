import streamlit as st
from openai import OpenAI, APIConnectionError, APIError, RateLimitError

# Initialize OpenAI client
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)
else:
    st.error("Please set OPENAI_API_KEY in Streamlit secrets")
    st.stop()

# Session state initialization
required_states = {
    "step": "input",
    "topic": "",
    "tone": "Informative",
    "outline": "",
    "section_index": 0,
    "sections": ["Hook", "Introduction", "Main Content", "Engagement", "Conclusion", "CTA"],
    "section_content": {},
    "retry_count": 0
}

for key, value in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

def generate_content(prompt, context=None):
    """Enhanced content generator with retry logic"""
    try:
        messages = [{"role": "user", "content": prompt}]
        if context:
            messages.insert(0, {"role": "system", "content": context})
            
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    
    except (RateLimitError, APIConnectionError, APIError) as e:
        st.session_state.retry_count += 1
        if st.session_state.retry_count < 3:
            st.rerun()
        st.error(f"API Error: {str(e)}")
        return ""
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return ""

def generate_outline():
    prompt = f"""
    Create a detailed YouTube video script outline about '{st.session_state.topic}' in {st.session_state.tone} tone.
    Include these elements:
    - Attention-grabbing hook
    - Clear introduction with thesis statement
    - 3 main points with supporting examples
    - Viewer engagement prompts
    - Strong conclusion with call-to-action
    - B-roll suggestions for each section
    
    Format in markdown with timing indications."""
    
    return generate_content(prompt, "You're a professional YouTube scriptwriter")

def generate_section(section_name):
    prompt = f"""
    Write the {section_name} section for a YouTube video about '{st.session_state.topic}'.
    Tone: {st.session_state.tone}
    Requirements:
    - Minimum 500 words
    - Include visual directions
    - Add transition phrases
    - Use markdown formatting
    - Incorporate 2-3 engagement elements
    
    Current script outline: {st.session_state.outline}"""
    
    return generate_content(prompt, "You're a video production expert")

# UI Components
def show_progress():
    progress = (st.session_state.section_index + 1) / len(st.session_state.sections)
    st.progress(progress, text=f"""
    Progress: {st.session_state.section_index + 1}/{len(st.session_state.sections)} sections
    Retries: {st.session_state.retry_count}""")

# Main App Flow
if st.session_state.step == "input":
    st.title("YouTube Script Master 🎬")
    
    with st.form("input_form"):
        st.session_state.topic = st.text_input("Video Topic", help="Be specific! E.g., '10 Python Tips for Beginners'")
        st.session_state.tone = st.selectbox("Tone Style", ["Informative", "Casual", "Humorous", "Motivational", "Storytelling"])
        
        if st.form_submit_button("Start Script Creation"):
            if len(st.session_state.topic) < 10:
                st.error("Please enter a detailed topic (minimum 10 characters)")
            else:
                st.session_state.outline = generate_outline()
                st.session_state.step = "outline_confirm"
                st.rerun()

elif st.session_state.step == "outline_confirm":
    st.title("Outline Preview")
    st.markdown(st.session_state.outline)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate Outline"):
            st.session_state.outline = generate_outline()
            st.rerun()
    
    with col2:
        if st.button("✅ Start Full Script Generation"):
            st.session_state.step = "section"
            st.session_state.section_index = 0
            st.rerun()

elif st.session_state.step == "section":
    current_section = st.session_state.sections[st.session_state.section_index]
    
    st.title(f"Section: {current_section}")
    show_progress()
    
    if current_section not in st.session_state.section_content:
        st.session_state.section_content[current_section] = generate_section(current_section)
    
    st.markdown(st.session_state.section_content[current_section])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Regenerate Section"):
            st.session_state.section_content[current_section] = generate_section(current_section)
            st.rerun()
    
    with col2:
        if st.session_state.section_index < len(st.session_state.sections) - 1:
            if st.button("⏭️ Next Section"):
                st.session_state.section_index += 1
                st.rerun()
    
    with col3:
        if st.session_state.section_index == len(st.session_state.sections) - 1:
            if st.button("🎉 Complete Script"):
                st.session_state.step = "final"
                st.rerun()

elif st.session_state.step == "final":
    st.title("✨ Final Script")
    show_progress()
    
    final_script = f"""# {st.session_state.topic}\n\n**Tone:** {st.session_state.tone}\n\n"""
    
    for section in st.session_state.sections:
        final_script += f"## {section}\n{st.session_state.section_content.get(section, '')}\n\n"
    
    st.markdown(final_script)
    
    st.download_button(
        "📥 Download Full Script",
        final_script,
        file_name=f"{st.session_state.topic.replace(' ', '_')}_script.md",
        mime="text/markdown"
    )
    
    if st.button("🔄 Create New Script"):
        st.session_state.clear()
        st.rerun()

# Requirements.txt needed:
# streamlit>=1.32.0
# openai>=1.12.0
