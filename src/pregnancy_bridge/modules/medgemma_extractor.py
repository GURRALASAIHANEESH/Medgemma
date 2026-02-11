"""
MedGemma Clinical Reasoning Engine - STABLE CPU LOADER
Uses GemmaTokenizer + bfloat16 CPU inference, no chat templates.
"""

import logging
import time
from pathlib import Path
from typing import Dict

import torch
from transformers import AutoModelForCausalLM, GemmaTokenizer

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Point to the D: cache where you just downloaded MedGemma
CACHE_PATH = Path(r"D:\huggingface_cache\hub\models--google--medgemma-1.5-4b-it")
OFFLOAD_DIR = CACHE_PATH  # not critical, but kept for compatibility


class MedGemmaClinicalReasoner:
    """MedGemma for clinical reasoning - STABLE CONFIGURATION"""

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.model_snapshot = None
        self.load_model()

    def load_model(self):
        """Load MedGemma with stable CPU bfloat16 configuration."""
        try:
            logger.info("Loading MedGemma Clinical Reasoner...")

            # Find snapshot under CACHE_PATH/snapshots/*
            snapshot_dirs = list(CACHE_PATH.glob("snapshots/*"))
            if not snapshot_dirs:
                raise FileNotFoundError(f"No model found at {CACHE_PATH}")

            model_path = snapshot_dirs[0]
            self.model_snapshot = str(model_path)
            logger.info(f"Using snapshot: {model_path}")

            # Ensure offload directory exists (harmless)
            OFFLOAD_DIR.mkdir(parents=True, exist_ok=True)

            # Load tokenizer - use GemmaTokenizer (slow), no chat templates
            logger.info("Loading Gemma tokenizer from local cache...")
            self.tokenizer = GemmaTokenizer.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=True,
            )

            # Configure tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model - CPU ONLY, bfloat16, low memory
            logger.info("Loading model on CPU with bfloat16...")
            start_time = time.time()
            self.model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                device_map="cpu",
                low_cpu_mem_usage=True,
            )
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.1f}s ({load_time/60:.1f} min)")

            self.model.eval()
            logger.info("✓ MedGemma Clinical Reasoner ready")
            logger.info(f"Model device: {self.model.device}")

        except Exception as e:
            logger.error(f"Failed to load MedGemma: {e}")
            raise

    def reason_about_case(self, structured_data: dict) -> dict:
        """
        Clinical reasoning with performance tracking.
        Returns extended dict with hardware_used and inference_time_ms.
        """
        start_time = time.time()

        try:
            # Check if custom prompt override provided
            if "prompt_override" in structured_data:
                prompt = structured_data["prompt_override"]
                logger.info("Using custom prompt override")
            else:
                prompt = self._build_clinical_prompt(structured_data)
                logger.info("Using default clinical prompt builder")

            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024,
            )

            # Move to model device
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            logger.info("Running clinical reasoning...")

            # Generate (deterministic, capped length)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=120,
                    do_sample=False,
                    temperature=None,  # Greedy
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # Decode only new tokens
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
            )

            inference_time_ms = (time.time() - start_time) * 1000

            logger.info(f"Generated {len(response)} chars")
            logger.info(f"Response preview: {response[:100]}")
            logger.info(f"Inference time: {inference_time_ms:.0f} ms on CPU")

            # Parse reasoning output
            result = self._parse_reasoning_output(response, structured_data)

            # Add performance metadata
            result["hardware_used"] = "CPU"
            result["inference_time_ms"] = round(inference_time_ms, 1)
            result["model_snapshot"] = self.model_snapshot

            return result

        except Exception as e:
            inference_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Clinical reasoning failed: {e}")

            return {
                "risk_category": "UNKNOWN",
                "reasoning": f"Model inference failed: {str(e)}",
                "confidence": "low",
                "referral_urgent": False,
                "hardware_used": "CPU",
                "inference_time_ms": round(inference_time_ms, 1),
                "error": str(e),
            }

    def _build_clinical_prompt(self, data: dict) -> str:
        """Build PLAIN TEXT prompt - NO ROLES, NO SPECIAL TOKENS."""
        prompt_parts = ["Clinical case analysis:\n"]

        if data.get("gestational_age"):
            prompt_parts.append(f"Gestational age: {data['gestational_age']} weeks")
        if data.get("hemoglobin"):
            prompt_parts.append(f"Hemoglobin: {data['hemoglobin']} g/dL")
        if data.get("bp_systolic") and data.get("bp_diastolic"):
            prompt_parts.append(
                f"Blood pressure: {data['bp_systolic']}/{data['bp_diastolic']} mmHg"
            )
        if data.get("proteinuria"):
            prompt_parts.append(f"Proteinuria: {data['proteinuria']}")
        if data.get("hb_trend"):
            prompt_parts.append(
                f"Hemoglobin trend: {' → '.join(map(str, data['hb_trend']))} g/dL"
            )

        prompt_parts.append("\nClinical assessment:")
        return "\n".join(prompt_parts)

    def _parse_reasoning_output(self, response: str, original_data: dict) -> dict:
        """Parse model response into structured format with clinical safety nets."""
        response_lower = response.lower()

        # Clinical condition-based risk assessment
        high_risk_conditions = [
            "preeclampsia",
            "pre-eclampsia",
            "eclampsia",
            "severe anemia",
            "severe hypertension",
            "hellp syndrome",
            "hellp",
            "placental abruption",
            "abruption",
            "fetal distress",
            "meets diagnostic criteria for preeclampsia",
            "diagnostic criteria for preeclampsia",
        ]

        moderate_risk_conditions = [
            "gestational hypertension",
            "mild anemia",
            "moderate anemia",
            "iron deficiency anemia",
            "iron deficiency",
            "stage 1 hypertension",
            "folate deficiency",
            "vitamin b12 deficiency",
        ]

        low_risk_indicators = [
            "normal",
            "low risk",
            "routine monitoring",
            "no immediate concern",
            "within normal limits",
        ]

        # Phase 1: high-risk conditions
        if any(condition in response_lower for condition in high_risk_conditions):
            risk = "HIGH"
        # Phase 2: moderate-risk conditions
        elif any(condition in response_lower for condition in moderate_risk_conditions):
            risk = "MODERATE"
        # Phase 3: keyword-based detection
        elif "high risk" in response_lower or "severe" in response_lower:
            risk = "HIGH"
        elif "moderate risk" in response_lower or "concerning" in response_lower:
            risk = "MODERATE"
        elif any(indicator in response_lower for indicator in low_risk_indicators):
            risk = "LOW"
        else:
            risk = "UNKNOWN"

        # Enhanced referral logic
        urgent_keywords = [
            "immediate",
            "urgent",
            "emergency",
            "preeclampsia",
            "pre-eclampsia",
            "eclampsia",
            "severe anemia",
            "hellp",
            "fetal distress",
            "severe hypertension",
            "placental abruption",
            "abruption",
            "immediate referral",
            "urgent referral",
        ]

        referral_urgent = any(
            keyword in response_lower for keyword in urgent_keywords
        ) or risk == "HIGH"

        # SAFETY NET: lab value–based escalation
        safety_net_triggered = False

        # Critical hemoglobin thresholds
        if original_data.get("hemoglobin"):
            hb = original_data["hemoglobin"]
            if hb < 7.0:
                risk = "HIGH"
                referral_urgent = True
                safety_net_triggered = True
                logger.warning(f"Safety net: Critical Hb={hb} g/dL → HIGH risk")
            elif hb < 9.0:
                if risk in ["LOW", "UNKNOWN"]:
                    risk = "HIGH"
                    referral_urgent = True
                    safety_net_triggered = True
                    logger.warning(f"Safety net: Severe anemia Hb={hb} g/dL → HIGH risk")

        # Critical blood pressure thresholds
        if original_data.get("bp_systolic"):
            bp_sys = original_data["bp_systolic"]
            if bp_sys >= 160:
                risk = "HIGH"
                referral_urgent = True
                safety_net_triggered = True
                logger.warning(f"Safety net: Severe HTN BP={bp_sys} mmHg → HIGH risk")
            elif bp_sys >= 150:
                if risk in ["LOW", "UNKNOWN"]:
                    risk = "HIGH"
                    referral_urgent = True
                    safety_net_triggered = True
                    logger.warning(f"Safety net: HTN BP={bp_sys} mmHg → HIGH risk")

        # Critical proteinuria with hypertension (pre-eclampsia criteria)
        proteinuria_significant = original_data.get("proteinuria") in [
            "+2",
            "++",
            "2+",
            "+++",
            "3+",
            "+3",
        ]
        bp_elevated = original_data.get("bp_systolic", 0) >= 140

        if proteinuria_significant and bp_elevated:
            risk = "HIGH"
            referral_urgent = True
            safety_net_triggered = True
            logger.warning(
                "Safety net: HTN + proteinuria (pre-eclampsia criteria) → HIGH risk"
            )

        return {
            "risk_category": risk,
            "reasoning": response.strip(),
            "confidence": "high" if risk != "UNKNOWN" else "low",
            "referral_urgent": referral_urgent,
            "model_used": "MedGemma-1.5-4b-it",
            "safety_net_triggered": safety_net_triggered,
        }


# Singleton instances (CPU only)
_reasoner_instance = None


def get_clinical_reasoner(force_cpu: bool = True) -> MedGemmaClinicalReasoner:
    """Get singleton MedGemma reasoner (CPU-only)."""
    global _reasoner_instance
    if _reasoner_instance is None:
        _reasoner_instance = MedGemmaClinicalReasoner()
    return _reasoner_instance


def clinical_reasoning(structured_data: dict, force_cpu: bool = True) -> dict:
    """Main entry point for clinical reasoning."""
    reasoner = get_clinical_reasoner(force_cpu=force_cpu)
    return reasoner.reason_about_case(structured_data)
