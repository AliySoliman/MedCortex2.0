# Generated from: medical_rag_demo_v4_1 (4).ipynb
# Converted at: 2026-07-07T04:17:14.240Z
# Next step (optional): refactor into modules & generate tests with RunCell
# Quick start: pip install runcell

# # 🏥 Medical RAG Assistant — v4.0 (Function Calling)
# ### قاعدة معرفة داخلية (Pinecone + كتب طبية) + بحث خارجي تلقائي عبر Function Calling + تحليل صور طبية
# 
# **الميزات في هذا الإصدار:**
# - 🤖 الموديل نفسه (عبر Function Calling) يقرر يستخدم أنهي tool: البحث الداخلي أولاً، وبعدين البحث الخارجي لو احتاج.
# - 📐 شكل إجابة ثابت ومنظم دايمًا: المرض، الأعراض، الأسباب، الحل، والمصدر المستخدم.
# - 🖼️ تحليل صور طبية (جروح/أمراض جلدية ظاهرة) باستخدام موديلات Vision مجانية، مع fallback مجاني بالكامل.
# - 🏷️ كل إجابة تُعرض مع توضيح واضح لمصدرها: **داخلي (Internal)** أو **خارجي (External)** أو **تحليل صورة (Vision)**.
# - 🔒 المفاتيح (API Keys) لا تُكتب داخل الكود — تُطلب وقت التشغيل فقط.
# 


# ## 1️⃣ تثبيت المكتبات


!pip install --upgrade "numpy<2.0.0"
!pip install -q markdown groq pillow requests
!pip install -qU langchain langchain-core langchain-community langchain-groq langchain-pinecone langchain-huggingface pinecone-client sentence-transformers


# ## 2️⃣ تحميل المفاتيح + الاتصال بقاعدة المعرفة + تجهيز الموديلات


import os
from getpass import getpass
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ============================================================
# 1. SETUP API KEYS
# ============================================================
if "PINECONE_API_KEY" not in os.environ:
    os.environ["PINECONE_API_KEY"] = getpass("🔑 Enter Pinecone API Key: ")

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass("🔑 Enter Groq API Key (free at console.groq.com): ")

# ============================================================
# 2. RECONNECT TO THE VECTOR DATABASE
# ============================================================
print("🔄 Reconnecting to Pinecone (medical_textbooks_base)...")
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cuda"}
)

vectorstore = PineconeVectorStore(
    index_name="medical-assistant",
    embedding=embeddings,
    namespace="medical_textbooks_base"
)

SCORE_THRESHOLD = 0.40

def retrieve_with_scores(question: str, k: int = 4):
    """Returns [(Document, score), ...] from Pinecone directly."""
    return vectorstore.similarity_search_with_score(question, k=k)

retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10})

# ============================================================
# 3. INITIALIZE THE TEXT LLM
# ============================================================
print("🧠 Booting up GPT-OSS 120B (Groq)...")
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    max_tokens=1024
)

# groq/compound → الاسم الصح هو compound-beta
# لو compound-beta كمان مش شغال عندك، الكود هيعمل fallback تلقائي
# لـ llama-3.3-70b-versatile مع web search tool مدمج
external_search_llm = ChatGroq(
    model="compound-beta",
    temperature=0.0,
    max_tokens=1024
)

# ============================================================
# 4. RAG PIPELINE
# ============================================================
MAX_CHARS_PER_DOC = 1500
MAX_TOTAL_CONTEXT_CHARS = 6000

def format_docs(docs):
    formatted_chunks = []
    total_chars = 0
    for doc in docs:
        book = doc.metadata.get("book_title", "Unknown Book")
        heading = doc.metadata.get("docling_headings", "Unknown Section")
        text = doc.page_content[:MAX_CHARS_PER_DOC]
        chunk = f"Source: {book} | Section: {heading}\nText: {text}"
        if total_chars + len(chunk) > MAX_TOTAL_CONTEXT_CHARS:
            break
        formatted_chunks.append(chunk)
        total_chars += len(chunk)
    return "\n\n---\n\n".join(formatted_chunks)

system_prompt = (
    "You are an elite, highly accurate Clinical AI Assistant. Your knowledge is strictly limited "
    "to the provided excerpts from medical textbooks.\n\n"
    "RULES:\n"
    "1. Answer the user's question based ONLY on the context below.\n"
    "2. If the answer cannot be found in the context, explicitly state: 'I cannot find the answer to this in the provided medical library.' Do NOT guess or hallucinate.\n"
    "3. Structure your answer professionally, using bullet points for readability if appropriate.\n"
    "4. At the end of your answer, cite the specific books and sections you used based on the metadata.\n\n"
    "MEDICAL CONTEXT:\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("✅ Medical Assistant is Online and Ready!\n")
print("=" * 60)


# ## 3️⃣ الوكيل الطبي (Function Calling Agent)


# ============================================================
# 🤖 Medical Agent (Function Calling) — v4.1
#
# Changes in v4.1:
#   - Language auto-detection: Arabic question → Arabic answer,
#     English question → English answer (never mixed).
#   - IMAGE_DIAGNOSIS_PROMPT updated: model gives ONE primary
#     diagnosis first (highest probability), then ranked
#     alternative possibilities — no more equal-weight lists.
# ============================================================

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# ---------- Tool 1: Internal Knowledge Base ----------
@tool
def search_internal_medical_knowledge(query: str) -> str:
    """Search the internal medical textbook knowledge base (vector database)
    for information about a disease, symptom, or medical condition.
    ALWAYS try this tool FIRST before searching the web.
    IMPORTANT: translate the query to English before calling this tool
    (textbooks are in English), but answer the user in their own language.
    Returns relevant excerpts, or NOT_FOUND if nothing relevant exists."""
    docs = retriever.invoke(query)
    if not docs:
        return "NOT_FOUND: No relevant documents found in the internal medical knowledge base."
    context = format_docs(docs)
    if not context.strip():
        return "NOT_FOUND: No relevant documents found in the internal medical knowledge base."
    return f"INTERNAL_SOURCE_FOUND:\n{context}"


# ---------- Tool 2: External Web Search ----------
@tool
def search_web(query: str) -> str:
    """Search the public web for up-to-date medical information.
    Use this ONLY if search_internal_medical_knowledge returned NOT_FOUND,
    or returned content that does not actually answer the user's question.
    Returns a synthesized answer based on live web search results.

    NOTE: not HIPAA-compliant — do not use with real patient-identifying data."""
    system_msg = (
        "You are a medical research assistant. Search the web and return factual, "
        "evidence-based findings about the query below. Be concise and mention general "
        "source types (health organization, clinical guideline, medical reference site)."
    )
    # حاول مع compound-beta أولاً (بيعمل web search مدمج تلقائياً)
    try:
        response = external_search_llm.invoke([
            ("system", system_msg),
            ("human", query),
        ])
        return f"EXTERNAL_SOURCE_FOUND:\n{response.content}"
    except Exception as e1:
        # Fallback: استخدم نفس الـ llm الأساسي (gpt-oss-120b) من معرفته
        # ووضّح للمستخدم إن البحث الخارجي فشل ولكن الموديل سيجاوب من معرفته العامة
        try:
            fallback_response = llm.invoke([
                ("system",
                 "You are a medical research assistant. Answer the following medical query "
                 "using your general medical knowledge (web search is unavailable). "
                 "Be factual, concise, and note that this comes from your training knowledge "
                 "rather than a live web search."),
                ("human", query),
            ])
            return (
                f"EXTERNAL_SOURCE_FOUND (fallback — web search unavailable, using model knowledge):\n"
                f"{fallback_response.content}"
            )
        except Exception as e2:
            return (
                f"EXTERNAL_SEARCH_FAILED: compound-beta error: {str(e1)[:150]} | "
                f"fallback error: {str(e2)[:150]}"
            )


tools = [search_internal_medical_knowledge, search_web]

# ============================================================
# AGENT SYSTEM PROMPT — v4.1
# Language detection + fixed answer structure
# ============================================================
AGENT_SYSTEM_PROMPT = """You are an expert Clinical AI Assistant helping users understand medical
conditions in clear, simple language.

TOOL USAGE RULES (must follow in order):
1. ALWAYS call `search_internal_medical_knowledge` first for ANY medical question.
2. If it returns "NOT_FOUND" or the content does not actually answer the question,
   THEN call `search_web` to find the answer from the internet.
3. Never answer from your own memory alone — always use one of the two tools first.

LANGUAGE RULE (critical):
- Detect the language the user wrote in.
- If the question is in Arabic → respond ENTIRELY in Arabic (translate section titles too).
- If the question is in English → respond ENTIRELY in English.
- NEVER mix languages in your response.
- When calling `search_internal_medical_knowledge`, always translate the query to English
  first (textbooks are in English), then write the final answer in the user's language.

QUESTION TYPE DETECTION (critical — read before choosing answer format):
Before answering, classify the user's question into one of these types:

TYPE A — Disease/Condition question:
  Examples: "What is diabetes?", "ما هو السكري؟", "أعراض الزائدة الدودية", "causes of hypertension"
  → Use the full structured format (5 sections below).

TYPE B — Specific / practical question:
  Examples: "What foods help with stomach pain?", "أكل بيخفف وجع المعدة؟",
            "can I take ibuprofen with antibiotics?", "هل الزنجبيل بينفع للسعال؟",
            "how long does a cold last?", "متى أروح للدكتور؟"
  → Answer DIRECTLY and conversationally. No rigid 5-section format.
     Give a focused, helpful answer to exactly what was asked.
     Still end with the ℹ️ Source line and ⚠️ disclaimer.

TYPE C — Follow-up or clarification:
  Examples: User already got a diagnosis answer and now asks "وإيه أحسن دواء؟" or "is surgery needed?"
  → Answer only the specific follow-up question. Do NOT repeat the full disease format.

---

FORMAT FOR TYPE A (Disease/Condition questions) — use this exact 5-section structure:

Arabic version:
## 🩺 المرض / الحالة
(اسم المرض أو الحالة)
## 📋 الأعراض
- (نقطة لكل عرض)
## 🔍 الأسباب
- (نقطة لكل سبب)
## 💊 العلاج / الحل المقترح
- (نقطة لكل خطوة)
## ℹ️ المصدر
(📚 تم الاعتماد على قاعدة المعرفة الداخلية، أو 🌐 تم البحث في الإنترنت لعدم توفر إجابة كافية)
⚠️ هذه معلومات تعليمية وليست تشخيصًا طبيًا، يرجى مراجعة طبيب مختص.

English version:
## 🩺 Condition
(clearly name the condition)
## 📋 Symptoms
- (one bullet per symptom)
## 🔍 Causes
- (one bullet per cause)
## 💊 Treatment / Next Steps
- (one bullet per step)
## ℹ️ Source
(📚 Based on the internal knowledge base (medical textbooks), or
 🌐 Based on a live web search — internal data was insufficient)
⚠️ This is educational information, not a medical diagnosis. Please consult a healthcare professional.

---

FORMAT FOR TYPE B & C (specific/practical/follow-up questions):
Answer directly in clear bullet points or short paragraphs — whatever fits best.
Do NOT use the 5-section disease format.
Example for "أكل بيخفف وجع المعدة؟":
  ✅ أكل خفيف بيساعد على تهدئة المعدة:
  - الأرز أو الشوفان المسلوق
  - الموز
  - ...
  ## ℹ️ المصدر
  ⚠️ هذه معلومات تعليمية ...

If the question is not medical at all, politely say (in the user's language) that you only handle medical questions.
"""

llm_with_tools = llm.bind_tools(tools)


def run_medical_agent(question: str, max_steps: int = 4):
    """
    Main agent loop:
    - Sends the question to the model with the tools.
    - If the model requests a tool, executes it and returns the result.
    - Repeats until the model returns a final answer (no new tool call).
    Returns dict: {answer, tools_used}
    """
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]
    tools_used = []

    for _ in range(max_steps):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        if not ai_msg.tool_calls:
            return {
                "answer": ai_msg.content,
                "tools_used": tools_used,
            }

        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tools_used.append(tool_name)

            matching_tool = next((t for t in tools if t.name == tool_name), None)
            if matching_tool is None:
                tool_result = f"ERROR: Unknown tool '{tool_name}'"
            else:
                try:
                    tool_result = matching_tool.invoke(tool_args)
                except Exception as e:
                    tool_result = f"TOOL_ERROR: {type(e).__name__} - {str(e)[:200]}"

            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))

    return {
        "answer": "⚠️ تعذر الوصول لإجابة نهائية بعد عدة محاولات. حاول إعادة صياغة السؤال.",
        "tools_used": tools_used,
    }


print("✅ Medical Agent v4.1 (Function Calling + Language Detection) is ready!")


# ## 4️⃣ تحليل الصور الطبية (Vision)


# ============================================================
# 🖼️ Medical Image Analysis (Vision) — v4.1
#
# Change in v4.1:
#   IMAGE_DIAGNOSIS_PROMPT updated to give:
#     1. ONE primary / most-likely diagnosis (decisive, not a list).
#     2. Ranked alternative possibilities (2-3 options, not equal weight).
#   This avoids the old behavior of listing many possibilities
#   without any priority, which was confusing for users.
# ============================================================

import base64
import requests
from groq import Groq

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

VISION_MODELS_PRIORITY = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

# ---- UPDATED IMAGE DIAGNOSIS PROMPT (v4.1) ----
# Key change: give ONE decisive primary diagnosis first,
# then ranked alternatives — NOT an equal-weight list.
IMAGE_DIAGNOSIS_PROMPT = """You are a clinical AI assistant analyzing a medical image
(e.g. a skin condition, visible wound, rash, or similar).

IMPORTANT INSTRUCTION ON HOW TO RESPOND:
- Do NOT list multiple diagnoses at equal weight.
- Give ONE primary diagnosis (the most likely/probable condition) first and be decisive about it.
- Then list 2-3 alternative possibilities in ranked order (most likely → least likely).
- For each option, briefly explain WHY you ranked it that way (visual clue that supports it).
- After the diagnosis section, provide HOME CARE / TREATMENT TIPS relevant to the primary diagnosis.

Structure your response EXACTLY as follows:

## 🔬 Primary Diagnosis (Most Likely)
**[Condition Name]** — Probability: High / Moderate
[Brief reasoning: the specific visual features that led to this conclusion]

## 🔄 Alternative Possibilities (ranked)
1. **[Second most likely condition]** — [brief visual reasoning]
2. **[Third possibility]** — [brief visual reasoning]

## 👁️ Visual Observations
- [Specific things you observe: color, texture, shape, size, distribution, etc.]

## 💊 General Care & Treatment Tips
Based on the primary diagnosis above, here are general care recommendations:
- **Immediate care:** [what to do right now — e.g. clean the wound, avoid scratching, keep dry]
- **Home remedies / OTC options:** [safe general suggestions — e.g. antiseptic cream, antihistamine for rash, cold compress]
- **What to avoid:** [things that could make it worse — e.g. don't pop blisters, avoid sun exposure]
- **Warning signs to watch for:** [symptoms that mean seek urgent care — e.g. fever, spreading redness, pus]

## 🏥 Recommended Next Step
[One clear, actionable recommendation — e.g. "See a dermatologist within 1-2 weeks"
or "Seek urgent care if fever develops"]

⚠️ This is an AI-generated visual impression, not a medical diagnosis. Please consult a healthcare professional.
"""


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _try_groq_vision(base64_image: str, mime_type: str = "image/jpeg"):
    """Try Groq Vision models in priority order.
    Returns (answer_text, model_name) or raises RuntimeError."""
    last_error = None
    for model_name in VISION_MODELS_PRIORITY:
        try:
            completion = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_DIAGNOSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                temperature=0.2,
                max_tokens=800,
            )
            return completion.choices[0].message.content, model_name
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All Groq vision models failed. Last error: {last_error}")


def _fallback_huggingface_caption(image_path: str) -> str:
    """Free 100% fallback: BLIP image captioning via Hugging Face Inference API."""
    api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    with open(image_path, "rb") as f:
        data = f.read()
    response = requests.post(api_url, data=data, timeout=30)
    if response.status_code != 200:
        return (
            "⚠️ تعذّر الوصول لأي موديل تحليل صور (Groq و Hugging Face). "
            "حاول تاني بعد قليل، أو تأكد من اتصالك بالإنترنت."
        )
    result = response.json()
    caption = result[0].get("generated_text", "No content recognized.") if isinstance(result, list) else str(result)
    return (
        f"**General image description (Hugging Face BLIP - fallback):** {caption}\n\n"
        "⚠️ This is a general image description only (free fallback model with no advanced medical "
        "diagnostic capability). Please consult a doctor for an accurate assessment."
    )


def analyze_medical_image(image_path: str, mime_type: str = "image/jpeg"):
    """
    Main image analysis function. Returns dict:
      - answer: final text (primary diagnosis + ranked alternatives + next step)
      - source_type: "vision_groq" or "vision_fallback"
      - model_used: actual model name that answered
    """
    base64_image = encode_image_to_base64(image_path)
    try:
        answer_text, model_used = _try_groq_vision(base64_image, mime_type)
        return {
            "answer": answer_text,
            "source_type": "vision_groq",
            "model_used": model_used,
        }
    except Exception:
        answer_text = _fallback_huggingface_caption(image_path)
        return {
            "answer": answer_text,
            "source_type": "vision_fallback",
            "model_used": "Salesforce/blip-image-captioning-large (Hugging Face)",
        }


print("✅ Medical Vision Module v4.1 (Primary Diagnosis + Ranked Alternatives) is ready!")


# ## 5️⃣ واجهة العرض (HTML Demo)


import markdown
import datetime
import time
from IPython.display import display, HTML, clear_output

# ============================================================
# 🎨 واجهة العرض (HTML Demo) — محدّثة لتوضيح مصدر الإجابة بوضوح:
#    - 📚 INTERNAL: من قاعدة المعرفة (الكتب الطبية المدرّبة عليها)
#    - 🌐 EXTERNAL: من بحث خارجي على الويب (لما الداتا الداخلية ناقصة)
#    - 🖼️ VISION: من تحليل صورة طبية مرفوعة
# ============================================================

SOURCE_BADGE_STYLE = {
    "internal": ("📚", "Internal Knowledge Base", "#00C9A7", "#003D32"),
    "external": ("🌐", "External Web Search", "#FFB74D", "#3A2A00"),
    "vision_groq": ("🖼️", "AI Vision Analysis (Groq)", "#4FC3F7", "#0D2A3A"),
    "vision_fallback": ("🖼️", "AI Vision Analysis (Fallback)", "#CE93D8", "#2A0A3A"),
}


def run_html_demo(question: str = None, image_path: str = None):
    """
    - لو question موجود بس: سؤال نصي عادي (داخلي أو خارجي تلقائيًا).
    - لو image_path موجود: تحليل صورة طبية.
    - ممكن الاتنين مع بعض (سؤال + صورة) لو احتجت مستقبلًا.
    """
    start_time = time.time()

    if image_path:
        print("🖼️ Analyzing medical image...")
        result = analyze_medical_image(image_path)
        question_display = question or "🖼️ [Image uploaded for analysis]"
        source_docs = []
    else:
        print("🧠 Agent is thinking (deciding which tool to use)...")
        agent_result = run_medical_agent(question)
        question_display = question

        tools_used = agent_result.get("tools_used", [])
        # نحدد نوع المصدر بناءً على آخر tool فعليًا استخدمه الموديل بنفسه
        if "search_web" in tools_used:
            source_type = "external"
        elif "search_internal_medical_knowledge" in tools_used:
            source_type = "internal"
        else:
            source_type = "internal"  # افتراضي احتياطي

        result = {
            "answer": agent_result["answer"],
            "source_type": source_type,
            "decision_reason": f"Tools used by the model: {', '.join(tools_used) if tools_used else 'none'}",
        }
        source_docs = []  # الـ agent الجديد بيرجع نص جاهز بدل مستندات خام

    answer_text = result["answer"]
    source_type = result["source_type"]
    elapsed_time = f"{round(time.time() - start_time, 2)}s"

    answer_html = markdown.markdown(answer_text, extensions=['extra', 'codehilite', 'tables'])

    # ── Source Badge (المصدر الرئيسي: داخلي / خارجي / صورة) ──
    badge_icon, badge_label, badge_accent, badge_bg = SOURCE_BADGE_STYLE.get(
        source_type, ("❓", "Unknown", "#888", "#222")
    )
    decision_reason = result.get("decision_reason", "")
    model_used = result.get("model_used", "")

    # ── Sources from internal knowledge base (لو فيه) ──
    sources_html = ""
    seen_sources = set()
    stats = {"Anatomy": 0, "Radiology": 0, "Diagnosis": 0, "Other": 0}

    CATEGORY_MAP = {
        "Anatomy":   ("🦴", "#00C9A7", "#003D32"),
        "Radiology": ("🩻", "#4FC3F7", "#0D2A3A"),
        "Diagnosis": ("🩺", "#FFB74D", "#3A2A00"),
        "Medical":   ("📘", "#CE93D8", "#2A0A3A"),
    }

    if source_docs:
        for doc in source_docs:
            book_title = doc.metadata.get('book_title', 'Unknown Book')
            if   "Anatomy"   in book_title: cat = "Anatomy"
            elif "Radiology" in book_title: cat = "Radiology"
            elif "Diagnosis" in book_title or "Laboratory" in book_title: cat = "Diagnosis"
            else: cat = "Medical"

            icon, accent, bg = CATEGORY_MAP[cat]
            stat_key = cat if cat in stats else "Other"
            stats[stat_key] += 1

            key = f"{cat}-{book_title}"
            if key not in seen_sources:
                seen_sources.add(key)
                short = book_title[:38] + ("…" if len(book_title) > 38 else "")
                sources_html += f"""
                <div class="source-badge" style="--accent:{accent};--bg:{bg};">
                    <span class="src-icon">{icon}</span>
                    <div class="src-text">
                        <span class="src-cat">{cat}</span>
                        <span class="src-title">{short}</span>
                    </div>
                </div>"""
    elif source_type == "internal":
        sources_html = "<p class='no-src internal-ok'>📚 الإجابة مبنية على نتائج تم استخراجها من قاعدة المعرفة الداخلية (الكتب الطبية).</p>"
    elif source_type == "external":
        sources_html = "<p class='no-src ext'>🌐 Answer generated via live web search (Groq Compound) — not from the trained medical library.</p>"
    else:
        sources_html = f"<p class='no-src vis'>🖼️ Visual analysis only — model used: {model_used}</p>"

    def stat_card(label, value, color, bg):
        return f"""
        <div class="stat-card" style="--c:{color};--b:{bg};">
            <span class="stat-val">{value}</span>
            <span class="stat-lbl">{label}</span>
        </div>"""

    stats_html = (
        stat_card("Sources",   len(seen_sources), "#A78BFA", "#1E1B4B") +
        stat_card("Anatomy",   stats["Anatomy"],  "#00C9A7", "#003D32") +
        stat_card("Radiology", stats["Radiology"],"#4FC3F7", "#0D2A3A") +
        stat_card("Diagnosis", stats["Diagnosis"],"#FFB74D", "#3A2A00")
    )

    now_str = datetime.datetime.now().strftime("%d %b %Y • %H:%M:%S")

    image_preview_html = ""
    if image_path:
        try:
            b64 = encode_image_to_base64(image_path)
            image_preview_html = f'<img src="data:image/jpeg;base64,{b64}" class="uploaded-img" />'
        except Exception:
            pass

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg-deep:    #050A14;
  --bg-panel:   #0C1525;
  --bg-card:    #111E35;
  --bg-input:   #0A1628;
  --border:     rgba(99,179,237,.12);
  --border-glow:rgba(99,179,237,.35);
  --teal:       #00C9A7;
  --cyan:       #4FC3F7;
  --violet:     #818CF8;
  --text-main:  #E2EBF6;
  --text-soft:  #7A94B8;
  --text-faint: #3A5070;
  --radius-xl:  24px;
  --radius-lg:  16px;
  --radius-md:  10px;
  --font-head:  'Syne', sans-serif;
  --font-body:  'DM Sans', sans-serif;
}}
body {{
  font-family: var(--font-body);
  background: var(--bg-deep);
  color: var(--text-main);
  min-height: 100vh;
  padding: 24px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,201,167,.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 110%, rgba(79,195,247,.06) 0%, transparent 55%);
}}
.shell {{
  width: 100%;
  max-width: 1120px;
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow:
    0 0 0 1px rgba(0,201,167,.04),
    0 40px 80px -20px rgba(0,0,0,.8),
    0 0 120px -40px rgba(0,201,167,.12);
  animation: fadeUp .5s ease both;
}}
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
.hdr {{
  background: linear-gradient(135deg, #070F1E 0%, #0C1A2E 100%);
  padding: 22px 32px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border); gap: 16px; flex-wrap: wrap;
}}
.hdr-brand {{ display:flex; align-items:center; gap:16px; }}
.hdr-logo {{
  width: 50px; height: 50px;
  background: linear-gradient(135deg, #00C9A7, #4FC3F7);
  border-radius: 14px;
  display: flex; align-items:center; justify-content:center;
  font-size: 1.5em;
  box-shadow: 0 0 24px rgba(0,201,167,.35), inset 0 1px 0 rgba(255,255,255,.15);
  flex-shrink: 0;
}}
.hdr-name {{
  font-family: var(--font-head); font-size: 1.35em; font-weight: 800; letter-spacing: -.02em;
  background: linear-gradient(120deg, #fff 30%, var(--teal));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hdr-sub {{ font-size: .78em; color: var(--text-soft); margin-top: 2px; letter-spacing: .02em; }}
.hdr-pills {{ display:flex; gap:10px; flex-wrap:wrap; }}
.pill {{
  padding: 6px 14px; border-radius: 40px; font-size: .72em; font-weight: 600;
  letter-spacing: .06em; text-transform: uppercase; border: 1px solid;
}}
.pill-teal  {{ color:var(--teal);  border-color:rgba(0,201,167,.3);  background:rgba(0,201,167,.08);  }}
.pill-cyan  {{ color:var(--cyan);  border-color:rgba(79,195,247,.3); background:rgba(79,195,247,.08); }}
.pill-live  {{ color: #4ADE80; border-color:rgba(74,222,128,.3); background:rgba(74,222,128,.08); display:flex; align-items:center; gap:6px; }}
.pulse-dot {{ width:7px; height:7px; border-radius:50%; background:#4ADE80; animation: pulse 1.8s infinite; }}
@keyframes pulse {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(74,222,128,.4); }} 50% {{ box-shadow: 0 0 0 5px rgba(74,222,128,0); }} }}
.body {{ background: var(--bg-panel); padding: 32px; display: flex; flex-direction: column; gap: 24px; }}
.stats-row {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }}
.stat-card {{
  background: var(--b, #111E35); border: 1px solid rgba(255,255,255,.06);
  border-left: 3px solid var(--c, #818CF8); border-radius: var(--radius-lg);
  padding: 16px 18px; display: flex; flex-direction:column; gap:4px;
  transition: transform .2s, box-shadow .2s;
}}
.stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px -8px rgba(0,0,0,.5); }}
.stat-val {{ font-family: var(--font-head); font-size: 2.1em; font-weight: 800; color: var(--c, #818CF8); line-height: 1; }}
.stat-lbl {{ font-size: .72em; text-transform: uppercase; letter-spacing: .1em; color: var(--text-soft); font-weight: 600; }}
.q-row {{ display:flex; justify-content:flex-end; gap:12px; align-items:flex-end; }}
.q-avatar {{
  width: 36px; height: 36px; flex-shrink:0; border-radius: 50%;
  background: linear-gradient(135deg, #4F46E5, #818CF8);
  display:flex; align-items:center; justify-content:center; font-size: 1em;
  box-shadow: 0 0 16px rgba(129,140,248,.3);
}}
.q-bubble {{
  background: linear-gradient(135deg, #2D3A8C, #3730A3); color: #E0E7FF;
  padding: 16px 22px; border-radius: 22px 22px 4px 22px; max-width: 75%;
  font-size: .95em; line-height: 1.65; font-weight: 400;
  border: 1px solid rgba(129,140,248,.2); box-shadow: 0 8px 24px -8px rgba(55,48,163,.5);
  word-wrap: break-word;
}}
.uploaded-img {{
  max-width: 220px; border-radius: 14px; margin-top: 10px; display:block;
  border: 1px solid rgba(129,140,248,.3);
}}
.a-row {{ display:flex; gap:12px; align-items:flex-start; }}
.a-avatar {{
  width: 36px; height: 36px; flex-shrink:0; margin-top:4px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), var(--cyan));
  display:flex; align-items:center; justify-content:center; font-size: 1em;
  box-shadow: 0 0 16px rgba(0,201,167,.35);
}}
.a-card {{
  flex: 1; background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 4px 22px 22px 22px; overflow: hidden;
  box-shadow: 0 20px 40px -16px rgba(0,0,0,.6); word-wrap: break-word;
}}
.a-card-top {{
  display:flex; align-items:center; gap:10px; padding: 12px 22px;
  background: rgba(0,201,167,.06); border-bottom: 1px solid rgba(0,201,167,.1); flex-wrap: wrap;
}}
.a-card-label {{ font-family: var(--font-head); font-size: .8em; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color: var(--teal); }}
.a-time {{ margin-left:auto; font-size:.72em; color:var(--text-faint); display:flex; align-items:center; gap:6px; }}

/* ── Source Origin Badge (الإضافة الأهم: داخلي/خارجي/صورة) ── */
.origin-badge {{
  display:inline-flex; align-items:center; gap:6px;
  padding: 4px 12px; border-radius: 20px; font-size:.72em; font-weight:700;
  text-transform:uppercase; letter-spacing:.05em;
  border: 1px solid var(--accent); color: var(--accent); background: var(--bg);
}}

.a-body {{ padding: 26px 28px; font-size: .93em; line-height: 1.85; color: var(--text-main); }}
.a-body h1,.a-body h2,.a-body h3 {{ font-family: var(--font-head); color: #fff; margin: 24px 0 12px; letter-spacing:-.02em; }}
.a-body h1 {{ font-size:1.5em; }}
.a-body h2 {{ font-size:1.2em; color:var(--teal); }}
.a-body h3 {{ font-size:1.05em; color:var(--cyan); }}
.a-body p  {{ margin-bottom:14px; }}
.a-body ul,.a-body ol {{ margin:0 0 14px 22px; }}
.a-body li {{ margin-bottom:6px; }}
.a-body strong {{ color:var(--cyan); font-weight:600; }}
.a-body em     {{ color: #A5B4FC; }}
.a-body code   {{ background: rgba(79,195,247,.12); color: var(--cyan); padding: 2px 7px; border-radius:5px; font-family: 'Fira Code', monospace; font-size:.88em; }}
.a-body pre {{ background: #070F1E; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 16px; overflow-x:auto; margin: 14px 0; }}
.a-body table {{ width:100%; border-collapse:collapse; margin: 16px 0; font-size:.88em; }}
.a-body th {{ background: rgba(0,201,167,.1); color:var(--teal); padding:10px 14px; text-align:left; border-bottom: 1px solid var(--border-glow); font-family:var(--font-head); font-weight:700; letter-spacing:.04em; }}
.a-body td {{ padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--text-main); }}
.a-body tr:hover td {{ background:rgba(255,255,255,.02); }}
.a-body blockquote {{ border-left: 3px solid var(--violet); padding: 12px 18px; background: rgba(129,140,248,.06); border-radius: 0 var(--radius-md) var(--radius-md) 0; margin: 14px 0; color: #A5B4FC; }}
.sources-section {{ padding: 20px 28px 24px; border-top: 1px solid var(--border); background: rgba(0,0,0,.15); }}
.src-heading {{ font-family: var(--font-head); font-size: .72em; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--text-faint); margin-bottom: 14px; display:flex; align-items:center; gap:8px; }}
.src-heading::after {{ content:''; flex:1; height:1px; background:var(--border); }}
.sources-grid {{ display:flex; flex-wrap:wrap; gap:10px; }}
.source-badge {{
  display: inline-flex; align-items:center; gap:10px; background: var(--bg, #111E35);
  border: 1px solid rgba(255,255,255,.07); border-left: 3px solid var(--accent, #00C9A7);
  padding: 9px 14px; border-radius: var(--radius-md); font-size:.8em;
  transition: transform .18s, box-shadow .18s; cursor:default;
}}
.source-badge:hover {{ transform:translateY(-2px); box-shadow: 0 6px 20px -6px rgba(0,0,0,.5); border-color: rgba(255,255,255,.12); }}
.src-icon {{ font-size:1.2em; }}
.src-text  {{ display:flex; flex-direction:column; gap:1px; }}
.src-cat   {{ font-weight:700; color:var(--accent); font-size:.75em; letter-spacing:.05em; text-transform:uppercase; }}
.src-title {{ color:var(--text-main); font-size:.88em; }}
.no-src    {{ color:#F87171; font-size:.85em; padding:12px; background:rgba(248,113,113,.08); border-radius:var(--radius-md); }}
.no-src.ext {{ color:#FFB74D; background:rgba(255,183,77,.08); }}
.no-src.vis {{ color:#4FC3F7; background:rgba(79,195,247,.08); }}
.no-src.internal-ok {{ color:#00C9A7; background:rgba(0,201,167,.08); }}
.decision-note {{ font-size:.72em; color:var(--text-faint); margin-top:8px; font-style:italic; }}
.ftr {{ background: #070F1E; border-top: 1px solid var(--border); padding: 14px 32px; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.ftr-left {{ font-size:.75em; color:var(--text-faint); display:flex; align-items:center; gap:8px; }}
.ftr-sep {{ width:1px; height:14px; background:var(--border); }}
.ftr-right {{ font-size:.73em; color:var(--text-faint); }}
@media(max-width:700px) {{
  .stats-row {{ grid-template-columns:repeat(2,1fr); }}
  .q-bubble,.a-card {{ max-width:100%; }}
  .hdr {{ padding:16px 18px; }}
  .body {{ padding:20px 16px; }}
}}
</style>
</head>
<body>
<div class="shell">
  <header class="hdr">
    <div class="hdr-brand">
      <div class="hdr-logo">⚕️</div>
      <div>
        <div class="hdr-name">Clinical Knowledge Core</div>
        <div class="hdr-sub">Medical RAG System &nbsp;·&nbsp; GPT-OSS 120B &nbsp;·&nbsp; Pinecone Vector Search &nbsp;·&nbsp; Vision-Enabled</div>
      </div>
    </div>
    <div class="hdr-pills">
      <span class="pill pill-teal">GPT-OSS 120B</span>
      <span class="pill pill-cyan">Pinecone</span>
      <span class="pill pill-live"><span class="pulse-dot"></span>Live</span>
    </div>
  </header>

  <main class="body">
    <div class="stats-row">{stats_html}</div>

    <div class="q-row">
      <div class="q-bubble">{question_display}{image_preview_html}</div>
      <div class="q-avatar">👤</div>
    </div>

    <div class="a-row">
      <div class="a-avatar">🤖</div>
      <div class="a-card">
        <div class="a-card-top">
          <span class="a-card-label">⚕ AI Clinical Response</span>
          <span class="origin-badge" style="--accent:{badge_accent};--bg:{badge_bg};">{badge_icon} {badge_label}</span>
          <span class="a-time">⏱ {elapsed_time} &nbsp;|&nbsp; {now_str}</span>
        </div>
        <div class="a-body">
          {answer_html}
          {f'<p class="decision-note">ℹ️ {decision_reason}</p>' if decision_reason else ''}
        </div>
        <div class="sources-section">
          <div class="src-heading">Verified Sources</div>
          <div class="sources-grid">{sources_html}</div>
        </div>
      </div>
    </div>
  </main>

  <footer class="ftr">
    <div class="ftr-left">
      <span>⚡ Medical RAG v3.0 (Internal + Web Fallback + Vision)</span>
      <div class="ftr-sep"></div>
      <span>For educational &amp; research use only</span>
    </div>
    <div class="ftr-right">Not a substitute for professional medical advice</div>
  </footer>
</div>
</body>
</html>"""

    clear_output(wait=True)
    display(HTML(html_content))


# ## 6️⃣ اختبارات (Tests)


# # 🧪 TEST 1 — سؤال متوقع وجوده في الداتا الداخلية (Internal Knowledge Base)
# 


question = "What are the common causes and treatments for hypernatremia?"
run_html_demo(question=question)


# # 🧪 TEST 2 — سؤال متوقع وجوده في الداتا الداخلية (للمقارنة)
# 


question = "What are the classic symptoms of acute appendicitis, and what tests are used to diagnose it?"
run_html_demo(question=question)


# # 🧪 TEST 3 — سؤال خارج نطاق الداتا الداخلية (لتجربة البحث الخارجي تلقائيًا)
# # مثال: سؤال عن حدث/موضوع طبي حديث جدًا أو نادر مش موجود في الكتب المدرّبة عليها
# 


question = "What are the latest 2026 FDA-approved treatments for resistant hypertension?"
run_html_demo(question=question)

# لاحظ: الموديل دلوقتي بيقرر بنفسه (Function Calling) لما يستخدم search_web.
# لو ظهر دايمًا Badge "📚 Internal" حتى لأسئلة حديثة جدًا، جرّب سؤال أوضح
# في كونه خارج نطاق الكتب الطبية، أو راجع الـ tools_used المطبوعة في decision_reason.


# # 🧪 TEST 4 — رفع صورة طبية (جرح/مرض جلدي ظاهر) وتحليلها بالـ AI Vision
# # في Colab: شغّل الخلية اللي تحتها وارفع صورة من جهازك مباشرة.
# 


from google.colab import files

print("📤 من فضلك ارفع صورة الحالة الطبية (جرح / طفح جلدي / إصابة ظاهرة)...")
uploaded = files.upload()

# نأخذ أول ملف مرفوع
uploaded_filename = list(uploaded.keys())[0]
image_path = f"/content/{uploaded_filename}"

run_html_demo(image_path=image_path)


# # 🧪 TEST 5 — سؤال عربي (اختبار اللغة التلقائية)
# # الموديل يكتشف تلقائيًا إن السؤال بالعربي ويرد بالعربي كامل بدون خلط لغات.


question = "ما هي أعراض وأسباب التهاب الزائدة الدودية، وكيف يتم علاجه؟"
run_html_demo(question=question)

# # 🧪 TEST 6 — اختبار البحث الخارجي (Web Search Fallback)
# # سؤال عن موضوع طبي حديث جدًا مش موجود في الكتب الداخلية.
# # المتوقع: الموديل يستخدم search_web تلقائيًا ويظهر Badge 🌐 External.


question = "What are the latest 2026 FDA-approved treatments for resistant hypertension?"
run_html_demo(question=question)
# Expected: Badge shows 🌐 External Web Search
# because this topic is too recent for the internal medical textbooks.

# ## 📝 ملاحظات مهمة قبل الاستخدام الفعلي
# 
# 1. **الأمان**: لا تشارك هذا النوتبوك مع مفاتيح API مكتوبة بداخله — المفاتيح هنا تُطلب وقت التشغيل فقط (`getpass`) ولا تُحفظ في الملف.
# 2. **كيف يقرر الموديل المصدر؟** الموديل (gpt-oss-120b) نفسه يقرر عبر Function Calling: يستخدم `search_internal_medical_knowledge` أولاً، وإذا لم تكن النتيجة كافية يستخدم `search_web` تلقائيًا. يمكنك مراقبة هذا القرار من خلال `decision_reason` المعروض أسفل كل إجابة (يوضح أي tools استُخدمت فعليًا).
# 3. **شكل الإجابة الثابت**: تم تثبيت تنسيق الإجابة (المرض، الأعراض، الأسباب، الحل، المصدر) داخل `AGENT_SYSTEM_PROMPT`. لو احتجت تغيّر الأقسام أو إضافة قسم جديد (مثل "متى تزور الطوارئ؟")، عدّل هذا الـ prompt مباشرة.
# 4. **HIPAA / خصوصية المرضى**: نظام `groq/compound` (البحث الخارجي) وكذلك موديلات الـ Vision **غير معتمدة كخدمات متوافقة مع HIPAA**. لا تُدخل أي بيانات حقيقية لمرضى (أسماء، صور وجوه، تفاصيل تعريفية) — هذا النوتبوك للأغراض التعليمية والتجريبية فقط.
# 5. **حدود تحليل الصور**: تحليل الصور الطبية بالذكاء الاصطناعي عرضة لأخطاء كبيرة (إضاءة، زاوية تصوير، جودة الكاميرا)، ولا يمكن الاعتماد عليه لاتخاذ قرارات علاجية. استخدمه فقط كأداة توعية أولية، ووجّه المستخدم دائمًا لمراجعة طبيب مختص.
# 6. **تتبع الموديلات**: موديلات Groq تتغير وتُستبدل بشكل متكرر (deprecation). إذا توقف أحد الموديلات المذكورة هنا عن العمل، راجع [صفحة الموديلات الرسمية](https://console.groq.com/docs/models) وحدّث أسماء الموديلات في خلية الإعداد.
# 
#