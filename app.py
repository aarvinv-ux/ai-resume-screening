import io
from pathlib import Path
import pandas as pd
import streamlit as st
from match import score_resumes
from parser import extract_contact, extract_name, read_job_description, read_resume, read_resume_from_url
from skills import extract_skills

st.set_page_config(page_title='HireLens', page_icon='H', layout='wide')
DEFAULT_JD = ''


def chips(values, style):
    return ' '.join(f'<span class="chip {style}">{v}</span>' for v in values) or '<span class="empty">None</span>'


def rank(job_text, uploads, urls=None, use_ai=False):
    job_skills = extract_skills(job_text)
    candidates = []
    for file in uploads or []:
        text = read_resume(file)
        if not text:
            st.warning(f'{file.name}: this resume looks like a scanned image or is empty.')
            continue
        contact = extract_contact(text)
        fallback_name = Path(file.name).stem.replace('_', ' ').replace('-', ' ').title()
        candidates.append({'Candidate': extract_name(text, fallback_name), 'Email': contact['email'], 'File': file.name, '_skills': extract_skills(text), '_text': text[:12000]})
    for url in urls or []:
        try:
            text = read_resume_from_url(url)
            if not text:
                st.warning(f'{url}: no readable resume text found.')
                continue
            contact = extract_contact(text)
            fallback_name = url.rstrip('/').split('/')[-1] or 'Resume link'
            candidates.append({'Candidate': extract_name(text, fallback_name), 'Email': contact['email'], 'File': url, '_skills': extract_skills(text), '_text': text[:12000]})
        except Exception as error:
            st.warning(f'{url}: {error}')
    safe_for_ai = use_ai and len(candidates) <= 75
    scores = score_resumes(job_text, [(item['_text'], item['_skills']) for item in candidates], job_skills, allow_ai=safe_for_ai)
    results = []
    for candidate, score in zip(candidates, scores):
        candidate.pop('_skills', None)
        candidate.pop('_text', None)
        candidate.update(score)
        results.append(candidate)
    return sorted(results, key=lambda x: x['score'], reverse=True), job_skills


def export_xlsx(results):
    frame = pd.DataFrame([{k: v for k, v in item.items() if k != 'Resume text'} for item in results])
    for col in ('matched_skills', 'missing_skills'):
        frame[col] = frame[col].apply(lambda values: ', '.join(values))
    frame = frame.rename(columns={'score': 'Score', 'skill_score': 'Skill score', 'text_score': 'AI similarity', 'similarity_method': 'Similarity method', 'matched_skills': 'Matched skills', 'missing_skills': 'Missing skills'})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        frame.to_excel(writer, index=False, sheet_name='Ranked candidates')
    output.seek(0)
    return output.getvalue()

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] { background: #ecebe8; }
.stApp { background: #ecebe8; color: #1c2824; }
.block-container { max-width: 1300px; padding-top: 0; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #153b36; width: 310px !important; min-width: 310px !important; }
[data-testid="stSidebar"] > div:first-child { background: #153b36; padding: 1.1rem 1.2rem 0.8rem; }
.stSidebar .block-container { padding-top: 0; }
.stSidebar .stCaptionContainer { color: #dfe9e2; font-size: 0.95rem; opacity: 0.95; margin-bottom: 1rem; }
.stSidebar .stTextArea textarea, .stSidebar .stTextInput input, .stSidebar .stFileUploader { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; color: #edf8f2; }
.stSidebar .stFileUploader { background: rgba(255,255,255,0.06); }
.stSidebar label { color: #edf8f2; font-size: 0.875rem; }
.stSidebar .stButton > button { width: 100%; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #edf8f2; }
.main .block-container { padding-left: 1.1rem; padding-right: 1.1rem; }
.eyebrow { color: #67756f; font-size: 0.8rem; letter-spacing: 0.18em; text-transform: uppercase; margin: 0 0 0.7rem; font-weight: 600; }
.hero { padding: 0.8rem 0 0.8rem; }
.hero h1 { font-family: 'Space Grotesk'; font-size: clamp(3rem, 4vw, 4.2rem); letter-spacing: -0.08em; line-height: 0.95; margin: 0; color: #1d251f; }
.hero p { color: #5f6f68; font-size: 1.03rem; margin: 1rem 0 0; }
.step-card { background: rgba(255,255,255,0.28); border-radius: 15px; border: 1px solid rgba(39, 64, 58, 0.08); padding: 1rem 1.15rem; }
.step-label { font-size: 0.75rem; font-weight: 700; color: #64756d; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.35rem; }
.step-title { font-family: 'Space Grotesk'; font-weight: 600; font-size: 1.05rem; color: #1f2725; margin-bottom: 0.4rem; }
[data-testid="stFileUploader"] { background: #0d1f1b; border: 1px solid rgba(61,75,71,0.7); border-radius: 14px; min-height: 88px; }
[data-testid="stFileUploaderDropzoneInstructions"] { color: #ebf4ee; }
.stButton > button[kind="primary"] { background: #1d5d4d; border: none; border-radius: 10px; color: #f5faf7; font-weight: 600; }
.stButton > button[kind="primary"]:hover { background: #174c3f; }
.skill-wrap { display: flex; flex-wrap: wrap; gap: 0.45rem; min-height: 40px; }
.chip { display: inline-block; padding: 0.38rem 0.72rem; border-radius: 0.45rem; font-size: 0.72rem; font-weight: 500; border: 1px solid rgba(39,61,55,0.08); }
.matched { background: #edf4ee; color: #235a4c; }
.missing { background: #f8ecea; color: #8d4d48; }
.metric { background: white; border: 1px solid #dae1dc; border-radius: 10px; padding: 1rem; }
.metric b { display: block; font: 700 1.75rem 'Space Grotesk'; color: #1e5c4d; }
.metric span { font-size: .78rem; color: #697b74; }
.candidate { background: white; border: 1px solid #dfe3dd; border-radius: 12px; padding: 1rem 1.1rem; margin: 0.8rem 0; }
.candidate h3 { margin: 0 0 0.2rem; font-size: 1.1rem; }
.candidate small { color: #67776f; }
.score { font: 700 2.05rem 'Space Grotesk'; color: #1d5d4d; }
.score-badge { font-size: 0.8rem; color: #64746d; }
.disclaimer { color: #74827b; font-size: .75rem; text-align: center; margin-top: 1.25rem; }
.empty { color: #71807a; font-style: italic; }
.status-card { background: #dfeaf0; border: 1px solid #c9d7df; border-radius: 10px; color: #2c5368; padding: 1rem 1.2rem; margin: 0.75rem 0 1rem; }
.footer-note { color: #dfece5; font-size: 0.88rem; line-height: 1.5; }
</style>''',unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'job' not in st.session_state: st.session_state.job = DEFAULT_JD
with st.sidebar:
    st.markdown('<div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.6rem"><div style="width:32px;height:32px;border-radius:9px;background:rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;font-family:Space Grotesk">H</div><div style="font-size:2.15rem;font-weight:700;font-family:Space Grotesk;color:#edf8f2;">HireLens</div></div>', unsafe_allow_html=True)
    st.caption('Explainable resume screening')
    job_text = st.text_area('Job description', st.session_state.job, height=220)
    job_file = st.file_uploader('Or upload a JD', type=['pdf', 'docx'])
    if job_file:
        try:
            job_text = read_job_description(job_file)
            st.success('Job description loaded')
        except Exception as error:
            st.error(str(error))
    st.session_state.job = job_text
    minimum = st.slider('Minimum score', 0, 100, 0)
    use_ai = st.checkbox('Use AI semantic matching', value=False, help='Uses embeddings only when enabled by the deployment. Otherwise it falls back immediately to fast local matching.')
    if st.button('Delete all screening data', use_container_width=True):
        st.session_state.results = []
        st.success('Session data deleted.')
    st.markdown('<div class="footer-note">Privacy-first screening<br>Session data stays in your browser</div>', unsafe_allow_html=True)

st.markdown('<div class="hero"><p class="eyebrow">CANDIDATE INTELLIGENCE</p><h1>Screen with clarity.</h1><p>Rank resumes against a job description with transparent, job-relevant evidence.</p></div>', unsafe_allow_html=True)

st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem"><div style="font-size:0.76rem;letter-spacing:0.15em;text-transform:uppercase;color:#687670;font-weight:700;">Screening workspace</div></div>', unsafe_allow_html=True)

left, right = st.columns([1.6, 1])
with left:
    st.markdown('<div class="step-card"><div class="step-label">Step 01</div><div class="step-title">Upload resumes</div></div>', unsafe_allow_html=True)
    uploads = st.file_uploader('Upload multiple PDF or DOCX resumes', type=['pdf', 'docx'], accept_multiple_files=True)
    if uploads:
        st.caption(f'{len(uploads)} resume file(s) selected')
    resume_links = st.text_area('Or add resume website links (one per line)', value='', height=88, placeholder='Paste public resume or portfolio links here', help='Optional alternative to file upload: add public PDF, DOCX, portfolio, or resume webpage links.')
with right:
    st.markdown('<div class="step-card"><div class="step-label">Step 02</div><div class="step-title">Job skills detected</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="skill-wrap">{chips(extract_skills(job_text), "matched")}</div>', unsafe_allow_html=True)
    st.caption('Skills are extracted from your job description and used to calculate the match score.')

if st.button('Rank candidates', type='primary', use_container_width=True):
    if not job_text.strip():
        st.error('Add a job description first.')
    else:
        link_list = [line.strip() for line in resume_links.splitlines() if line.strip()]
        total_sources = len(uploads or []) + len(link_list)
        mode = 'AI' if use_ai else 'fast'
        with st.spinner(f'Analyzing {total_sources} resume(s) in {mode} mode...'):
            st.session_state.results, _ = rank(job_text, uploads, link_list, use_ai)
        if use_ai and total_sources <= 75 and all(item['similarity_method'] != 'AI semantic similarity' for item in st.session_state.results):
            st.info('AI embeddings are not enabled on this deployment, so fast local matching was used.')

results = [item for item in st.session_state.results if item['score'] >= minimum]
if results:
    avg = sum(x['score'] for x in results) / len(results)
    cols = st.columns(4)
    for col, label, value in zip(cols, ['Candidates', 'Average score', 'Top score', 'JD skills'], [len(results), f'{avg:.1f}', f'{results[0]["score"]:.1f}', len(extract_skills(job_text))]):
        col.markdown(f'<div class="metric"><span>{label}</span><b>{value}</b></div>', unsafe_allow_html=True)
    st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-top:1.3rem;margin-bottom:0.5rem"><div style="font-size:0.76rem;letter-spacing:0.15em;text-transform:uppercase;color:#687670;font-weight:700;">Screening results</div><div>', unsafe_allow_html=True)
    st.download_button('Download Excel', export_xlsx(results), 'hirelens_ranked_candidates.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.markdown('</div></div>', unsafe_allow_html=True)

    visible_results = results[:50]
    if len(results) > len(visible_results):
        st.caption(f'Showing the top {len(visible_results)} candidates. All {len(results)} candidates are included in the Excel download.')
    for number, item in enumerate(visible_results, 1):
        st.markdown(f'''<div class="candidate"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem"><div style="display:flex;align-items:flex-start;gap:0.9rem"><div style="font-size:0.9rem;color:#8a9490;font-weight:700;width:1.8rem;">{number:02d}</div><div><h3>{item['Candidate']}</h3><small>{item['File']} · {item['Email']}</small></div></div><div style="text-align:right"><div class="score">{item['score']:.1f}</div><div class="score-badge">match score</div></div></div></div>''', unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            st.markdown('**Matched skills**')
            st.markdown(chips(item['matched_skills'], 'matched'), unsafe_allow_html=True)
        with b:
            st.markdown('**Missing skills**')
            st.markdown(chips(item['missing_skills'], 'missing'), unsafe_allow_html=True)
        with st.expander('Show score breakdown'):
            x, y, z = st.columns(3)
            x.metric('Skill score', f'{item["skill_score"]:.1f}%')
            y.metric('AI similarity', f'{item["text_score"]:.1f}%')
            z.metric('Final score', f'{item["score"]:.1f}')
            st.caption(f'Method: {item["similarity_method"]}')
else:
    st.markdown('<div class="status-card">Add a job description and upload resumes to rank them.</div>', unsafe_allow_html=True)

st.markdown('<p class="disclaimer">AI-assisted recommendation only. Do not use as the sole basis for hiring decisions. Scores are not scientifically validated.</p>', unsafe_allow_html=True)
