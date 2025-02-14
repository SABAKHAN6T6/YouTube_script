import streamlit as st
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
import os

# ========== CONFIGURATION ==========
MODEL_NAME = "gpt-4o"               # Switch between gpt-4o/gpt-4-turbo
MAX_TOKENS = 4096                   # Max response length
BASE_URL = "https://api.openai.com/v1"  # For Azure: "https://YOUR_RESOURCE.openai.azure.com"

# ========== INITIALIZATION ==========
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(
        api_key=st.secrets.OPENAI_API_KEY,
        base_url=BASE_URL,
        # For Azure add:
        # api_version="2024-02-15-preview"
    )
else:
    st.error("Set OPENAI_API_KEY in Streamlit secrets")
    st.stop()

# ========== SESSION STATE ==========
session_defaults = {
    "step": "input",
    "topic": "",
    "tone": "Informative",
    "outline": "",
    "section_index": 0,
    "sections": ["Hook", "Introduction", "Main Content", "Engagement", "Conclusion", "CTA"],
    "section_content": {},
    "retry_count": 0,
    "model_params": {
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": MAX_TOKENS
    }
}

for key, value in session_defaults.items():
    st.session_state.setdefault(key, value)

# ========== CORE FUNCTIONS ==========
def generate_content(prompt, context=None):
    """Advanced generator with error handling"""
    messages = [{"role": "user", "content": prompt}]
    if context:
        messages.insert(0, {"role": "system", "content": context})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=st.session_state.model_params["temperature"],
            max_tokens=st.session_state.model_params["max_tokens"],
            top_p=st.session_state.model_params["top_p"]
        )
        content = response.choices[0].message.content.strip()
        
        if not content or len(content) < 100:
            raise ValueError("Incomplete response")
        return content
    
    except (RateLimitError, APIConnectionError, APIError) as e:
        if st.session_state.retry_count < 3:
            st.session_state.retry_count += 1
            st.rerun()
        st.error(f"API Error: {str(e)}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return ""

def generate_outline():
    prompt = f"""Create YouTube script outline for '{st.session_state.topic}' ({st.session_state.tone} tone):
    - Hook (0-10s): Attention grabber
    - Intro (10-30s): Thesis statement
    - Main Content (3 key points with examples)
    - Engagement: 3 viewer interaction prompts
    - Conclusion: Summary + CTA
    - B-roll suggestions for each section
    Format: Markdown with timings"""
    return generate_content(prompt, "Professional YouTube Producer")

def generate_section(section):
    prompt = f"""Write {section} section for video about '{st.session_state.topic}':
    - Tone: {st.session_state.tone}
    - Length: 300-500 words
    - Include: Visual directions, transitions, 2 engagement elements
    - Format: Markdown
    Current Outline: {st.session_state.outline}"""
    return generate_content(prompt, "Video Production Expert")

# ========== UI COMPONENTS ==========
def show_progress():
    progress = (st.session_state.section_index + 1) / len(st.session_state.sections)
    st.progress(progress, text=f"""
    Progress: {st.session_state.section_index + 1}/{len(st.session_state.sections)}
    Retries: {st.session_state.retry_count}""")

def parameter_sidebar():
    with st.sidebar:
        st.header("⚙️ Model Settings")
        st.session_state.model_params["temperature"] = st.slider(
            "Creativity", 0.0, 2.0, 0.7, help="0=Strict, 2=Creative")
        st.session_state.model_params["max_tokens"] = st.slider(
            "Response Length", 512, 4096, 4096)
        st.markdown(f"""
        ## Model Info 🧠
        **Using:** {MODEL_NAME}
        **Context:** 128k tokens
        **Multimodal:** Text/Image support
        **Languages:** 27+ supported
        """)

# ========== APP FLOW ==========
parameter_sidebar()

if st.session_state.step == "input":
    st.title("🎬 YouTube Script Master")
    
    with st.form("main_input"):
        st.session_state.topic = st.text_input("Video Topic", 
            help="Ex: '10 Python Tips for Beginners'")
        st.session_state.tone = st.selectbox("Tone Style", 
            ["Informative", "Casual", "Humorous", "Motivational"])
        
        if st.form_submit_button("🚀 Generate Outline"):
            if len(st.session_state.topic) < 10:
                st.error("Enter detailed topic (10+ chars)")
            else:
                st.session_state.outline = generate_outline()
                st.session_state.step = "outline"
                st.rerun()

elif st.session_state.step == "outline":
    st.title("📝 Script Outline")
    st.markdown(st.session_state.outline)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate Outline"):
            st.session_state.outline = generate_outline()
            st.rerun()
    with col2:
        if st.button("✅ Start Full Script"):
            st.session_state.step = "sections"
            st.rerun()

elif st.session_state.step == "sections":
    current_section = st.session_state.sections[st.session_state.section_index]
    
    st.title(f"📜 {current_section}")
    show_progress()
    
    if current_section not in st.session_state.section_content:
        st.session_state.section_content[current_section] = generate_section(current_section)
    
    st.markdown(st.session_state.section_content[current_section])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate Section"):
            st.session_state.section_content[current_section] = generate_section(current_section)
            st.rerun()
    with col2:
        if st.session_state.section_index < len(st.session_state.sections) - 1:
            if st.button("⏭️ Next Section"):
                st.session_state.section_index += 1
                st.rerun()
        else:
            if st.button("🎉 Complete Script"):
                st.session_state.step = "final"
                st.rerun()

elif st.session_state.step == "final":
    st.title("✨ Final Script")
    show_progress()
    
    final_script = f"# {st.session_state.topic}\n\n**Tone:** {st.session_state.tone}\n\n"
    for section in st.session_state.sections:
        final_script += f"## {section}\n{st.session_state.section_content.get(section, '')}\n\n"
    
    st.markdown(final_script)
    
    st.download_button(
        "📥 Download Script",
        final_script,
        file_name=f"{st.session_state.topic.replace(' ', '_')}_script.md"
    )
    
    if st.button("🔄 New Script"):
        st.session_state.clear()
        st.rerun()

# ========== DEPLOYMENT NOTES ==========
"""
requirements.txt:
streamlit>=1.32.0
openai>=1.12.0

For Azure deployment:
1. Set BASE_URL to Azure endpoint
2. Add api_version parameter
3. Use Azure-specific API key
"""
