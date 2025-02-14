import streamlit as st
import openai
from openai.error import RateLimitError

# Secure API Key Handling
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets.OPENAI_API_KEY
else:
    st.error("Please set API key in Streamlit secrets")
    st.stop()

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = "input"
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "tone" not in st.session_state:
    st.session_state.tone = "Informative"
if "outline" not in st.session_state:
    st.session_state.outline = ""
if "section_index" not in st.session_state:
    st.session_state.section_index = 0
if "sections" not in st.session_state:
    st.session_state.sections = ["Hook", "Introduction", "Main Content", "Engagement", "Conclusion", "CTA"]
if "section_content" not in st.session_state:
    st.session_state.section_content = {}

def generate_outline(topic, tone):
    prompt = f"""
Create a YouTube video script outline for the topic '{topic}' in {tone} tone. Follow this structure:

1. Hook (0-10 seconds):
   - Compelling opening
   - Surprising fact or question

2. Introduction (10-30 seconds):
   - Engaging topic introduction
   - Explain importance

3. Main Content (30 seconds - X minutes):
   - 3 key points with examples and visual suggestions

4. Engagement (throughout video):
   - Audience interaction prompts

5. Conclusion (last 30 seconds):
   - Key points summary
   - Teaser for next video

6. Call to Action:
   - Subscribe/Like/Share instructions

Provide the outline in markdown format."""
    
    try:
        with st.spinner("Generating outline..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        st.error("Please wait and try again")
        return ""
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return ""

def generate_section(topic, section_name, tone):
    prompt = f"""
Write a {tone} tone script for the '{section_name}' section of a YouTube video about '{topic}'.

Focus on:
- {"Attention-grabbing opener" if section_name == "Hook" else ""}
- {"Clear topic presentation" if section_name == "Introduction" else ""}
- {"Examples and visual suggestions" if section_name == "Main Content" else ""}
- {"Audience interaction" if section_name == "Engagement" else ""}
- {"Memorable closing" if section_name == "Conclusion" else ""}
- {"Effective action instructions" if section_name == "CTA" else ""}

Provide 3-5 concise paragraphs in markdown format."""
    
    try:
        with st.spinner(f"Generating {section_name}..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        st.error("Please wait and try again")
        return ""
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return ""

# UI Flow
if st.session_state.step == "input":
    st.title("YouTube Script Wizard 🧙♂️")
    st.session_state.topic = st.text_input("Video Topic")
    st.session_state.tone = st.selectbox("Select Tone", ["Informative", "Casual", "Humorous", "Motivational"])
    
    if st.button("Generate Outline"):
        if not st.session_state.topic.strip():
            st.error("Please enter a topic")
        else:
            st.session_state.outline = generate_outline(st.session_state.topic, st.session_state.tone)
            st.session_state.step = "outline_confirm"
            st.experimental_rerun()

elif st.session_state.step == "outline_confirm":
    st.title("Outline Review")
    st.markdown(st.session_state.outline)
    
    if st.button("Generate New Outline"):
        st.session_state.outline = generate_outline(st.session_state.topic, st.session_state.tone)
        st.experimental_rerun()
    
    if st.button("Start Script Generation"):
        st.session_state.step = "section"
        st.session_state.section_index = 0
        st.experimental_rerun()

elif st.session_state.step == "section":
    current_index = st.session_state.section_index
    if current_index < len(st.session_state.sections):
        section = st.session_state.sections[current_index]
        st.title(f"Section: {section}")
        
        if section not in st.session_state.section_content:
            st.session_state.section_content[section] = generate_section(
                st.session_state.topic, section, st.session_state.tone
            )
        
        st.markdown(st.session_state.section_content[section])
        
        if st.button("Regenerate"):
            st.session_state.section_content[section] = generate_section(
                st.session_state.topic, section, st.session_state.tone
            )
            st.experimental_rerun()
        
        if st.button("Next Section"):
            st.session_state.section_index += 1
            st.experimental_rerun()
    else:
        st.title("🎉 Script Complete!")
        final_script = f"# {st.session_state.topic}\n\n"
        for section in st.session_state.sections:
            final_script += f"## {section}\n{st.session_state.section_content.get(section, '')}\n\n"
        
        st.markdown(final_script)
        st.download_button(
            "Download Script",
            final_script,
            file_name=f"{st.session_state.topic.replace(' ', '_')}_script.md"
        )
        
        if st.button("Create New Script"):
            st.session_state.clear()
            st.experimental_rerun()
