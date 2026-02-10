"""
MedGemma Clinical Reasoning Engine with GPU Acceleration
Preserves existing architecture, adds GPU auto-detection
"""

import torch
from pathlib import Path
from typing import Dict
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CACHE_PATH = Path("D:/medgemma_clean/models--google--medgemma-1.5-4b-it")
OFFLOAD_DIR = Path("D:/medgemma_clean/models--google--medgemma-1.5-4b-it/snapshots/b05b6fa90147b76639de6522a843ff1ebd8dd832")


class MedGemmaClinicalReasoner:
    """MedGemma for clinical reasoning with GPU acceleration"""
    
    def __init__(self, force_cpu=False):
        self.tokenizer = None
        self.model = None
        self.device = None
        self.force_cpu = force_cpu
        self.model_snapshot = None
        self.load_model()
    
    def _detect_device(self):
        """Auto-detect best available device"""
        if self.force_cpu:
            logger.info("Forcing CPU usage (force_cpu=True)")
            return "cpu"
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"✓ GPU detected: {gpu_name}")
            logger.info(f"CUDA version: {torch.version.cuda}")
            return "cuda"
        else:
            logger.info("No GPU available, using CPU")
            return "cpu"
    
    def load_model(self):
        """Load MedGemma with GPU acceleration if available"""
        try:
            logger.info("Loading MedGemma Clinical Reasoner...")
            
            # Detect device
            self.device = self._detect_device()
            
            # Find snapshot
            snapshot_dirs = list(CACHE_PATH.glob("snapshots/*"))
            if not snapshot_dirs:
                raise FileNotFoundError(f"No model found at {CACHE_PATH}")
            
            model_path = snapshot_dirs[0]
            self.model_snapshot = str(model_path)
            logger.info(f"Using snapshot: {model_path}")
            
            # Ensure offload directory exists (for CPU fallback)
            OFFLOAD_DIR.mkdir(parents=True, exist_ok=True)
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=True
            )
            
            # Configure tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model with device-specific configuration
            if self.device == "cuda":
                logger.info("Loading model on GPU with FP16...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                    trust_remote_code=True,
                    torch_dtype=torch.float16,  # FP16 for GPU efficiency
                    device_map="auto",  # Auto device mapping
                    low_cpu_mem_usage=True
                )
            else:
                logger.info("Loading model on CPU with bfloat16...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                    trust_remote_code=True,
                    torch_dtype=torch.bfloat16,  # bfloat16 for CPU
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                    offload_state_dict=True,
                    use_safetensors=False  # Bypass safetensors format error
                )
            
            self.model.eval()
            logger.info("✓ MedGemma Clinical Reasoner ready")
            logger.info(f"Model device: {self.device.upper()}")
            
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                reserved = torch.cuda.memory_reserved(0) / 1024**3
                logger.info(f"GPU memory: {allocated:.2f} GB allocated, {reserved:.2f} GB reserved")
                
        except Exception as e:
            logger.error(f"Failed to load MedGemma: {e}")
            raise
    
    def reason_about_case(self, structured_data: dict) -> dict:
        """
        Clinical reasoning with performance tracking
        Returns extended dict with hardware_used and inference_time_ms
        """
        start_time = time.time()
        
        try:
            # Check if custom prompt override provided
            if 'prompt_override' in structured_data:
                prompt = structured_data['prompt_override']
                logger.info("Using custom prompt override")
            else:
                prompt = self._build_clinical_prompt(structured_data)
                logger.info("Using default clinical prompt builder")
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            )
            
            # Move to model device
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            logger.info("Running clinical reasoning...")
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode only new tokens
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            inference_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Generated {len(response)} chars")
            logger.info(f"Response preview: {response[:100]}")
            logger.info(f"Inference time: {inference_time_ms:.0f} ms on {self.device.upper()}")
            
            # Parse reasoning output
            result = self._parse_reasoning_output(response, structured_data)
            
            # Add performance metadata
            result['hardware_used'] = self.device.upper()
            result['inference_time_ms'] = round(inference_time_ms, 1)
            result['model_snapshot'] = self.model_snapshot
            
            return result
            
        except Exception as e:
            inference_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Clinical reasoning failed: {e}")
            
            return {
                'risk_category': 'UNKNOWN',
                'reasoning': f'Model inference failed: {str(e)}',
                'confidence': 'low',
                'referral_urgent': False,
                'hardware_used': self.device.upper(),
                'inference_time_ms': round(inference_time_ms, 1),
                'error': str(e)
            }
    
    def _build_clinical_prompt(self, data: dict) -> str:
        """Build PLAIN TEXT prompt - NO ROLES, NO SPECIAL TOKENS"""
        prompt_parts = ["Clinical case analysis:\n"]
        
        if data.get('gestational_age'):
            prompt_parts.append(f"Gestational age: {data['gestational_age']} weeks")
        if data.get('hemoglobin'):
            prompt_parts.append(f"Hemoglobin: {data['hemoglobin']} g/dL")
        if data.get('bp_systolic') and data.get('bp_diastolic'):
            prompt_parts.append(f"Blood pressure: {data['bp_systolic']}/{data['bp_diastolic']} mmHg")
        if data.get('proteinuria'):
            prompt_parts.append(f"Proteinuria: {data['proteinuria']}")
        if data.get('hb_trend'):
            prompt_parts.append(f"Hemoglobin trend: {' → '.join(map(str, data['hb_trend']))} g/dL")
        
        prompt_parts.append("\nClinical assessment:")
        return "\n".join(prompt_parts)
    
    def _parse_reasoning_output(self, response: str, original_data: dict) -> dict:
        """Parse model response with clinical entity recognition and safety nets"""
        response_lower = response.lower()
        
        # Clinical condition-based risk assessment
        high_risk_conditions = [
            'preeclampsia', 'pre-eclampsia', 'eclampsia', 'severe anemia',
            'severe hypertension', 'hellp syndrome', 'hellp',
            'placental abruption', 'abruption', 'fetal distress',
            'meets diagnostic criteria for preeclampsia',
            'diagnostic criteria for preeclampsia'
        ]
        
        moderate_risk_conditions = [
            'gestational hypertension', 'mild anemia', 'moderate anemia',
            'iron deficiency anemia', 'iron deficiency', 'stage 1 hypertension',
            'folate deficiency', 'vitamin b12 deficiency'
        ]
        
        low_risk_indicators = [
            'normal', 'low risk', 'routine monitoring', 'no immediate concern',
            'within normal limits'
        ]
        
        # Phase 1: Check for high-risk clinical conditions
        if any(condition in response_lower for condition in high_risk_conditions):
            risk = 'HIGH'
        # Phase 2: Check for moderate-risk conditions
        elif any(condition in response_lower for condition in moderate_risk_conditions):
            risk = 'MODERATE'
        # Phase 3: Fallback to keyword-based detection
        elif 'high risk' in response_lower or 'severe' in response_lower:
            risk = 'HIGH'
        elif 'moderate risk' in response_lower or 'concerning' in response_lower:
            risk = 'MODERATE'
        elif any(indicator in response_lower for indicator in low_risk_indicators):
            risk = 'LOW'
        else:
            risk = 'UNKNOWN'
        
        # Enhanced referral logic
        urgent_keywords = [
            'immediate', 'urgent', 'emergency', 'preeclampsia', 'pre-eclampsia',
            'eclampsia', 'severe anemia', 'hellp', 'fetal distress',
            'severe hypertension', 'placental abruption', 'abruption',
            'immediate referral', 'urgent referral'
        ]
        
        referral_urgent = any(keyword in response_lower for keyword in urgent_keywords) or risk == 'HIGH'
        
        # SAFETY NET: Lab value-based risk escalation
        safety_net_triggered = False
        
        # Critical hemoglobin thresholds
        if original_data.get('hemoglobin'):
            hb = original_data['hemoglobin']
            if hb < 7.0:
                risk = 'HIGH'
                referral_urgent = True
                safety_net_triggered = True
                logger.warning(f"Safety net: Critical Hb={hb} g/dL → HIGH risk")
            elif hb < 9.0:
                if risk in ['LOW', 'UNKNOWN']:
                    risk = 'HIGH'
                    referral_urgent = True
                    safety_net_triggered = True
                    logger.warning(f"Safety net: Severe anemia Hb={hb} g/dL → HIGH risk")
        
        # Critical blood pressure thresholds
        if original_data.get('bp_systolic'):
            bp_sys = original_data['bp_systolic']
            if bp_sys >= 160:
                risk = 'HIGH'
                referral_urgent = True
                safety_net_triggered = True
                logger.warning(f"Safety net: Severe HTN BP={bp_sys} mmHg → HIGH risk")
            elif bp_sys >= 150:
                if risk in ['LOW', 'UNKNOWN']:
                    risk = 'HIGH'
                    referral_urgent = True
                    safety_net_triggered = True
                    logger.warning(f"Safety net: HTN BP={bp_sys} mmHg → HIGH risk")
        
        # Critical proteinuria with hypertension
        proteinuria_significant = original_data.get('proteinuria') in ['+2', '++', '2+', '+++', '3+', '+3']
        bp_elevated = original_data.get('bp_systolic', 0) >= 140
        
        if proteinuria_significant and bp_elevated:
            risk = 'HIGH'
            referral_urgent = True
            safety_net_triggered = True
            logger.warning("Safety net: HTN + proteinuria (pre-eclampsia criteria) → HIGH risk")
        
        return {
            'risk_category': risk,
            'reasoning': response.strip(),
            'confidence': 'high' if risk != 'UNKNOWN' else 'low',
            'referral_urgent': referral_urgent,
            'model_used': 'MedGemma-1.5-4b-it',
            'safety_net_triggered': safety_net_triggered
        }


# Singleton instances (one for GPU, one for CPU)
_reasoner_gpu = None
_reasoner_cpu = None


def get_clinical_reasoner(force_cpu=True) -> MedGemmaClinicalReasoner:
    """Get singleton MedGemma reasoner - FORCED CPU MODE"""
    global _reasoner_gpu, _reasoner_cpu
    
    # Always use CPU for stability
    if _reasoner_cpu is None:
        _reasoner_cpu = MedGemmaClinicalReasoner(force_cpu=True)
    return _reasoner_cpu


def clinical_reasoning(structured_data: dict, force_cpu=False) -> dict:
    """Main entry point for clinical reasoning"""
    reasoner = get_clinical_reasoner(force_cpu=force_cpu)
    return reasoner.reason_about_case(structured_data)
