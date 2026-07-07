# backend/app/ai/multimodal/medical_image_analyzer.py
# ─────────────────────────────────────────────────────────────────────────────
# Medical Image Analyzer
# Ported from medical_rag_demo_v4_1 notebook for wound/skin condition analysis
# ─────────────────────────────────────────────────────────────────────────────

import base64
import os
import requests
from typing import Dict, Any
from groq import Groq

# Vision models priority (Groq)
VISION_MODELS_PRIORITY = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

# Updated image diagnosis prompt (v4.1) - gives primary diagnosis first, then ranked alternatives
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


class MedicalImageAnalyzer:
    """
    Analyzes medical images (wounds, skin conditions, etc.) using Groq Vision models
    with HuggingFace fallback for free analysis.
    """

    def __init__(self):
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None

    def encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    def _try_groq_vision(self, base64_image: str, mime_type: str = "image/jpeg") -> tuple[str, str]:
        """
        Try Groq Vision models in priority order.
        Returns (answer_text, model_name) or raises RuntimeError.
        """
        if not self.groq_client:
            raise RuntimeError("Groq client not initialized - GROQ_API_KEY missing")

        last_error = None
        for model_name in VISION_MODELS_PRIORITY:
            try:
                completion = self.groq_client.chat.completions.create(
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

    def _fallback_huggingface_caption(self, image_bytes: bytes) -> str:
        """
        Free 100% fallback: BLIP image captioning via Hugging Face Inference API.
        """
        api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        response = requests.post(api_url, data=image_bytes, timeout=30)
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

    def analyze_medical_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Main image analysis function. Returns dict:
          - answer: final text (primary diagnosis + ranked alternatives + next step)
          - source_type: "vision_groq" or "vision_fallback"
          - model_used: actual model name that answered
        """
        base64_image = self.encode_image_to_base64(image_bytes)
        try:
            answer_text, model_used = self._try_groq_vision(base64_image, mime_type)
            return {
                "answer": answer_text,
                "source_type": "vision_groq",
                "model_used": model_used,
            }
        except Exception:
            answer_text = self._fallback_huggingface_caption(image_bytes)
            return {
                "answer": answer_text,
                "source_type": "vision_fallback",
                "model_used": "Salesforce/blip-image-captioning-large (Hugging Face)",
            }


# Singleton instance
medical_image_analyzer = MedicalImageAnalyzer()
