# backend/app/ai/orchestrator/engine.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Orchestration Engine
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Optional, List
from app.ai.orchestrator.schemas import OrchestratorInput, OrchestratorOutput
from app.ai.orchestrator.pipelines import (
    Pipeline,
    Urgency,
    ImageType,
    URGENT_SYMPTOMS,
    SOON_SYMPTOMS,
    DRUG_KEYWORDS,
    LIFESTYLE_KEYWORDS,
    DOCTOR_KEYWORDS,
    IMAGE_TYPE_KEYWORDS,
)


class OrchestratorEngine:
    """
    The MedCortex Orchestration Engine — intelligent router for clinical AI system.
    Analyzes user input and decides which specialized AI pipelines need activation.
    """

    def __init__(self):
        """Initialize the orchestrator engine."""
        pass

    def route(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """
        Analyze user input and determine which pipelines to activate.

        Args:
            input_data: The orchestrator input containing user message, image info,
                       conversation history, user profile, and audio flag.

        Returns:
            OrchestratorOutput: JSON-serializable routing decision with pipelines,
                               urgency, specialist hint, and reasoning.
        """
        user_message = input_data.user_message.lower()
        has_image = input_data.has_image
        image_description = input_data.image_description.lower() if input_data.image_description else None
        from_audio = input_data.from_audio

        # Initialize pipeline list
        pipelines = []
        image_type: Optional[str] = None

        # Determine image type if present
        if has_image and image_description:
            image_type = self._classify_image_type(image_description)

        # Check for wound/skin injury - wound_vision takes priority over general vision
        is_wound = self._is_wound_or_skin_injury(user_message, image_description)

        # Pipeline activation logic
        if has_image:
            if is_wound:
                pipelines.append(Pipeline.WOUND_VISION)
                # Wound images always get doctor referral
                pipelines.append(Pipeline.DOCTOR_FINDER)
                image_type = ImageType.WOUND
            else:
                pipelines.append(Pipeline.VISION)
                # Lab reports often need lifestyle guidance
                if image_type == ImageType.LAB_REPORT:
                    pipelines.append(Pipeline.LIFESTYLE)
        else:
            # No image - check for other pipeline needs
            if self._has_drug_query(user_message):
                pipelines.append(Pipeline.DRUG_RAG)
            elif self._has_lifestyle_query(user_message):
                pipelines.append(Pipeline.LIFESTYLE)
            elif self._has_doctor_request(user_message):
                pipelines.append(Pipeline.DOCTOR_FINDER)
            else:
                # Default to RAG for general medical questions
                pipelines.append(Pipeline.RAG)

        # Always include RAG when user describes physical symptoms
        if self._has_symptoms(user_message):
            if Pipeline.RAG not in pipelines:
                pipelines.append(Pipeline.RAG)

        # Check for doctor finder needs
        requires_doctor_finder = self._requires_doctor_referral(
            user_message, pipelines, has_image, is_wound
        )
        if requires_doctor_finder and Pipeline.DOCTOR_FINDER not in pipelines:
            pipelines.append(Pipeline.DOCTOR_FINDER)

        # Add STT passthrough flag if from audio
        if from_audio:
            pipelines.append(Pipeline.STT_PASSTHROUGH)

        # Determine primary pipeline
        primary_pipeline = self._determine_primary_pipeline(pipelines, has_image, is_wound)

        # Assess urgency
        urgency = self._assess_urgency(user_message, has_image, is_wound)

        # Determine specialist hint
        specialist_hint = self._determine_specialist(user_message, image_type, is_wound)

        # Generate routing reason
        routing_reason = self._generate_routing_reason(
            user_message, pipelines, has_image, image_type, is_wound
        )

        return OrchestratorOutput(
            pipelines=[p.value for p in pipelines],
            primary_pipeline=primary_pipeline.value,
            urgency=urgency.value,
            specialist_hint=specialist_hint,
            routing_reason=routing_reason,
            requires_doctor_finder=Pipeline.DOCTOR_FINDER in pipelines,
            image_type=image_type.value if image_type else None,
        )

    def _classify_image_type(self, description: str) -> Optional[ImageType]:
        """Classify image type based on description."""
        description_lower = description.lower()
        
        for image_type, keywords in IMAGE_TYPE_KEYWORDS.items():
            if any(keyword in description_lower for keyword in keywords):
                return image_type
        
        # Check for general medical image terms
        if any(term in description_lower for term in ["medical", "clinical", "report", "document"]):
            return ImageType.OTHER_MEDICAL
        
        return None

    def _is_wound_or_skin_injury(self, user_message: str, image_description: Optional[str]) -> bool:
        """Check if the input relates to a wound or skin injury."""
        wound_keywords = [
            "wound", "cut", "burn", "rash", "lesion", "bruise", "injury",
            "bleeding", "incision", "laceration", "abrasion", "blister",
            "skin condition", "skin problem", "dermat"
        ]
        
        combined_text = user_message
        if image_description:
            combined_text += " " + image_description
        
        combined_text = combined_text.lower()
        return any(keyword in combined_text for keyword in wound_keywords)

    def _has_drug_query(self, user_message: str) -> bool:
        """Check if the user is asking about drugs/medications."""
        # Check for drug names (common medications)
        drug_names = [
            "ibuprofen", "warfarin", "aspirin", "tylenol", "acetaminophen",
            "advil", "motrin", "aleve", "naproxen", "lisinopril", "metformin",
            "lipitor", "atorvastatin", "prozac", "zoloft", "xanax", "valium"
        ]
        if any(drug in user_message for drug in drug_names):
            return True
        return any(keyword in user_message for keyword in DRUG_KEYWORDS)

    def _has_lifestyle_query(self, user_message: str) -> bool:
        """Check if the user is asking about lifestyle recommendations."""
        return any(keyword in user_message for keyword in LIFESTYLE_KEYWORDS)

    def _has_doctor_request(self, user_message: str) -> bool:
        """Check if the user is explicitly requesting a doctor."""
        # Check for general doctor keywords
        if any(keyword in user_message for keyword in DOCTOR_KEYWORDS):
            return True
        
        # Check for specialist names (implies doctor finder need)
        specialist_names = [
            "cardiologist", "dermatologist", "orthopedist", "orthopedic",
            "gastroenterologist", "neurologist", "pulmonologist", "radiologist",
            "oncologist", "endocrinologist", "pediatrician", "obstetrician",
            "gynecologist", "psychiatrist", "surgeon"
        ]
        return any(specialist in user_message for specialist in specialist_names)

    def _has_symptoms(self, user_message: str) -> bool:
        """Check if the user describes physical symptoms."""
        symptom_indicators = [
            "pain", "ache", "hurt", "sore", "swelling", "fever", "nausea",
            "vomiting", "dizziness", "headache", "fatigue", "weakness",
            "cough", "shortness of breath", "difficulty breathing",
            "rash", "itch", "bleeding", "numb", "tingle", "burn"
        ]
        return any(indicator in user_message for indicator in symptom_indicators)

    def _requires_doctor_referral(
        self, user_message: str, pipelines: List[Pipeline], has_image: bool, is_wound: bool
    ) -> bool:
        """Determine if doctor finder should be activated."""
        # Urgent conditions always need doctor
        if self._is_urgent(user_message):
            return True
        
        # Wound images already handled separately
        if is_wound:
            return True
        
        # Explicit doctor request
        if any(keyword in user_message for keyword in DOCTOR_KEYWORDS):
            return True
        
        # Serious conditions need doctor
        if self._is_serious_condition(user_message):
            return True
        
        return False

    def _is_urgent(self, user_message: str) -> bool:
        """Check for urgent symptoms."""
        return any(symptom in user_message for symptom in URGENT_SYMPTOMS)

    def _is_serious_condition(self, user_message: str) -> bool:
        """Check for serious but not immediately urgent conditions."""
        serious_indicators = [
            "severe", "persistent", "chronic", "worsening", "sudden",
            "infection", "fracture", "broken", "dislocate"
        ]
        return any(indicator in user_message for indicator in serious_indicators)

    def _determine_primary_pipeline(
        self, pipelines: List[Pipeline], has_image: bool, is_wound: bool
    ) -> Pipeline:
        """Determine the primary pipeline for this input."""
        # Wound vision takes priority
        if is_wound and Pipeline.WOUND_VISION in pipelines:
            return Pipeline.WOUND_VISION
        
        # Vision is primary when image present (and not wound)
        if has_image and Pipeline.VISION in pipelines:
            return Pipeline.VISION
        
        # Drug RAG for drug questions
        if Pipeline.DRUG_RAG in pipelines:
            return Pipeline.DRUG_RAG
        
        # Doctor finder for urgent/serious cases
        if Pipeline.DOCTOR_FINDER in pipelines and self._is_urgent(""):
            return Pipeline.DOCTOR_FINDER
        
        # Default to RAG
        if Pipeline.RAG in pipelines:
            return Pipeline.RAG
        
        # Fallback to first available
        return pipelines[0] if pipelines else Pipeline.RAG

    def _assess_urgency(self, user_message: str, has_image: bool, is_wound: bool) -> Urgency:
        """Assess clinical urgency of the input."""
        # Urgent symptoms
        if self._is_urgent(user_message):
            return Urgency.URGENT
        
        # Wounds need soon attention
        if is_wound:
            return Urgency.SOON
        
        # Soon symptoms
        if any(symptom in user_message for symptom in SOON_SYMPTOMS):
            return Urgency.SOON
        
        # Default to routine
        return Urgency.ROUTINE

    def _determine_specialist(
        self, user_message: str, image_type: Optional[ImageType], is_wound: bool
    ) -> Optional[str]:
        """Determine the most appropriate medical specialist."""
        # Check for explicit specialist names in user message
        specialist_names = {
            "cardiologist": "cardiologist",
            "dermatologist": "dermatologist",
            "orthopedist": "orthopedist",
            "orthopedic": "orthopedist",
            "gastroenterologist": "gastroenterologist",
            "neurologist": "neurologist",
            "pulmonologist": "pulmonologist",
            "radiologist": "radiologist",
            "oncologist": "oncologist",
            "endocrinologist": "endocrinologist",
            "pediatrician": "pediatrician",
            "obstetrician": "obstetrician",
            "gynecologist": "gynecologist",
            "psychiatrist": "psychiatrist",
            "surgeon": "surgeon",
            "general practitioner": "general practitioner",
            "gp": "general practitioner",
            "primary care": "general practitioner",
        }
        
        for name, specialist in specialist_names.items():
            if name in user_message:
                return specialist
        
        # Cardiology
        if any(term in user_message for term in ["chest", "heart", "cardiac", "palpitation"]):
            return "cardiologist"
        
        # Dermatology (wounds/skin)
        if is_wound or image_type == ImageType.SKIN_LESION:
            return "dermatologist"
        
        # Orthopedics
        if any(term in user_message for term in ["bone", "joint", "fracture", "broken", "sprain"]):
            return "orthopedist"
        
        # Gastroenterology
        if any(term in user_message for term in ["stomach", "abdominal", "digestive", "liver"]):
            return "gastroenterologist"
        
        # Neurology
        if any(term in user_message for term in ["headache", "migraine", "seizure", "numb", "tingle"]):
            return "neurologist"
        
        # Pulmonology
        if any(term in user_message for term in ["lung", "breathing", "respiratory", "asthma"]):
            return "pulmonologist"
        
        # Radiology for imaging
        if image_type in [ImageType.XRAY, ImageType.CT_SCAN, ImageType.MRI, ImageType.ULTRASOUND]:
            return "radiologist"
        
        # Default to general practitioner
        return "general practitioner"

    def _generate_routing_reason(
        self,
        user_message: str,
        pipelines: List[Pipeline],
        has_image: bool,
        image_type: Optional[ImageType],
        is_wound: bool
    ) -> str:
        """Generate a one-sentence explanation of routing decision."""
        parts = []
        
        if is_wound:
            parts.append("User uploaded a wound image")
        elif has_image:
            if image_type:
                parts.append(f"User uploaded a {image_type.value.replace('_', ' ')}")
            else:
                parts.append("User uploaded a medical image")
        else:
            if self._has_drug_query(user_message):
                parts.append("User asks about drug interaction")
            elif self._has_lifestyle_query(user_message):
                parts.append("User asks about lifestyle recommendations")
            elif self._has_symptoms(user_message):
                parts.append("User describes symptoms")
            else:
                parts.append("User has a general medical question")
        
        # Add pipeline actions
        pipeline_actions = []
        if Pipeline.RAG in pipelines:
            pipeline_actions.append("medical knowledge retrieval")
        if Pipeline.VISION in pipelines:
            pipeline_actions.append("image analysis")
        if Pipeline.WOUND_VISION in pipelines:
            pipeline_actions.append("wound classification")
        if Pipeline.DRUG_RAG in pipelines:
            pipeline_actions.append("drug interaction check")
        if Pipeline.DOCTOR_FINDER in pipelines:
            pipeline_actions.append("doctor referral")
        if Pipeline.LIFESTYLE in pipelines:
            pipeline_actions.append("lifestyle guidance")
        
        if pipeline_actions:
            parts.append("needs " + " and ".join(pipeline_actions))
        
        return " — ".join(parts) + "."
