import io
from pathlib import Path
import pandas as pd
import streamlit as st
from match import score_resume
from parser import extract_contact, extract_name, read_job_description, read_resume
from skills import extract_skills

st.set_page_config(page_title='HireLens', page_icon='H', layout='wide')
DEFAULT_JD = '''Python Developer needed to build reliable APIs and data products.
Required skills: Python, FastAPI, SQL, Git, Docker.
Preferred skills: AWS, pandas, scikit-learn, testing.
Experience with backend development, analytics, and communication is useful.'''
DEMO = [
 ('Aarav Mehta','aarav@example.com','Python developer with Python, FastAPI, SQL, Docker, Git and AWS. Built a recruitment API.'),
 ('Maya Shah','maya@example.com','Frontend engineer with JavaScript, React, HTML, CSS, TypeScript and Git.'),
 ('Rohan Kapoor','rohan@example.com','Junior developer with Python, JavaScript, HTML and SQL. Built a college event portal.'),
 ('Ishita Rao','ishita@example.com','Data analyst with Python, pandas, numpy, scikit-learn, SQL, Excel and Power BI.'),
 ('Kabir Singh','kabir@example.com','Web developer with HTML, CSS, JavaScript and communication skills.')]

def chips(values, style):
    return ' '.join(f'<span class="chip {style}">{v}</span>' for v in values) or '<span class="empty">None</span>'

def rank(job_text, uploads):
    job_skills = extract_skills(job_text)
    results = []
    for name, email, text in DEMO:
        results.append({'Candidate':name,'Email':email,'File':'Demo candidate','Resume text':text, **score_resume(text,job_text,extract_skills(text),job_skills)})
    for file in uploads or []:
        text = read_resume(file)
        if not text:
            st.warning(f'{file.name}: this resume looks like a scanned image or is empty.')
            continue
        contact = extract_contact(text)
        fallback_name = Path(file.name).stem.replace('_', ' ').replace('-', ' ').title()
        results.append({'Candidate':extract_name(text, fallback_name),'Email':contact['email'],'File':file.name,'Resume text':text, **score_resume(text,job_text,extract_skills(text),job_skills)})
    return sorted(results,key=lambda x:x['score'],reverse=True), job_skills

def export_xlsx(results):
    frame = pd.DataFrame([{k:v for k,v in item.items() if k != 'Resume text'} for item in results])
    for col in ('matched_skills','missing_skills'):
        frame[col] = frame[col].apply(lambda values:', '.join(values))
    frame = frame.rename(columns={'score':'Score','skill_score':'Skill score','text_score':'Text similarity','matched_skills':'Matched skills','missing_skills':'Missing skills'})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        frame.to_excel(writer,index=False,sheet_name='Ranked candidates')
    output.seek(0)
    return output.getvalue()

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Space+Grotesk:wght@600;700&display=swap');
.stApp{background:#f4f6f1;color:#17251f}.block-container{max-width:1180px;padding-top:2.3rem}h1,h2,h3{font-family:'Space Grotesk';letter-spacing:-.6px}.hero{background:#f4f6f1;padding:.2rem 0 1.35rem;border-radius:0;margin-bottom:1rem}.hero h1{color:#17251f;font-size:2.8rem;margin-bottom:.2rem}.hero p{color:#718078;font-size:1rem}.stSidebar{background:#17342b}.stSidebar>div:first-child{background:#17342b}.stSidebar *{color:#dcece2}.stSidebar textarea{background:#234a3c;border-color:#557a6a;color:#fff}.stSidebar label{color:#dcece2}.stButton>button{border-radius:7px;border-color:#27735c}.stButton>button[kind="primary"]{background:#27735c;color:#fff;border-color:#27735c}.stFileUploader{background:#fff;border:1px solid #dce4dc;border-radius:10px;padding:.8rem}.metric{background:white;border:1px solid #dce4dc;border-radius:9px;padding:1rem}.metric b{display:block;font:700 1.8rem 'Space Grotesk';color:#27735c}.metric span{font-size:.75rem;color:#718078}.chip{display:inline-block;padding:.3rem .5rem;border-radius:4px;margin:.15rem;font-size:.75rem}.matched{color:#216348;background:#e6f0e9}.missing{color:#914641;background:#f8e8e5}.candidate{background:white;border:1px solid #dce4dc;border-radius:9px;padding:1.2rem;margin:1rem 0}.score{font:700 2rem 'Space Grotesk';color:#27735c}.disclaimer{color:#89968e;font-size:.72rem;text-align:center}
</style>''',unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results=[]
if 'job' not in st.session_state: st.session_state.job=DEFAULT_JD
with st.sidebar:
    st.markdown('## HireLens')
    st.caption('Explainable resume screening')
    job_text=st.text_area('Job description',st.session_state.job,height=220)
    job_file=st.file_uploader('Or upload a JD',type=['pdf','docx'])
    if job_file:
        try: job_text=read_job_description(job_file); st.success('Job description loaded')
        except Exception as error: st.error(str(error))
    st.session_state.job=job_text
    minimum=st.slider('Minimum score',0,100,0)
    if st.button('Delete all screening data',use_container_width=True): st.session_state.results=[]; st.success('Session data deleted.')

st.markdown('<div class="hero"><p class="eyebrow">CANDIDATE INTELLIGENCE</p><h1>Screen with clarity.</h1><p>Rank resumes against a job description with transparent, job-relevant evidence.</p></div>',unsafe_allow_html=True)
left,right=st.columns([1.4,1])
with left: uploads=st.file_uploader('Upload multiple PDF or DOCX resumes',type=['pdf','docx'],accept_multiple_files=True)
with right: st.markdown('### Job skills detected'); st.markdown(chips(extract_skills(job_text),'matched'),unsafe_allow_html=True)
if st.button('Rank candidates',type='primary',use_container_width=True):
    if not job_text.strip(): st.error('Add a job description first.')
    else: st.session_state.results,_=rank(job_text,uploads)

results=[item for item in st.session_state.results if item['score']>=minimum]
if results:
    avg=sum(x['score'] for x in results)/len(results); cols=st.columns(4)
    for col,label,value in zip(cols,['Candidates','Average score','Top score','JD skills'],[len(results),f'{avg:.1f}',f'{results[0]["score"]:.1f}',len(extract_skills(job_text))]): col.markdown(f'<div class="metric"><span>{label}</span><b>{value}</b></div>',unsafe_allow_html=True)
    st.subheader('Ranked candidates')
    st.download_button('Download ranked list as Excel',export_xlsx(results),'hirelens_ranked_candidates.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    for number,item in enumerate(results,1):
        st.markdown(f'<div class="candidate"><div style="display:flex;justify-content:space-between"><div><h3>#{number} {item["Candidate"]}</h3><small>{item["File"]} · {item["Email"]}</small></div><div class="score">{item["score"]:.1f}</div></div></div>',unsafe_allow_html=True)
        a,b=st.columns(2)
        with a: st.markdown('**Matched skills**'); st.markdown(chips(item['matched_skills'],'matched'),unsafe_allow_html=True)
        with b: st.markdown('**Missing skills**'); st.markdown(chips(item['missing_skills'],'missing'),unsafe_allow_html=True)
        with st.expander('Score breakdown'):
            x,y,z=st.columns(3); x.metric('Skill score (70%)',f'{item["skill_score"]:.1f}'); y.metric('Text similarity (30%)',f'{item["text_score"]:.1f}'); z.metric('Final score',f'{item["score"]:.1f}')
else: st.info('Add a job description and click Rank candidates. Five demo candidates are included automatically.')
st.markdown('<p class="disclaimer">AI-assisted recommendation only. Do not use as the sole basis for hiring decisions. Scores are not scientifically validated.</p>',unsafe_allow_html=True)
