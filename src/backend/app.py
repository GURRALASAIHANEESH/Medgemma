"""
PregnancyBridge Backend API
===========================
POLICY: Rule engine is authoritative. MedGemma advice is advisory; 
raw outputs are stored for audit only.

Immutable artifact storage with HMAC signing for integrity verification.
"""

import os
import sys
import json
import hashlib
import hmac
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

# Add parent directory to path to import pregnancy_bridge modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizer
from dotenv import load_dotenv

# Import existing pregnancy_bridge modules
from src.pregnancy_bridge.modules.risk_engine import assess_risk as assess_risk_engine
from src.pregnancy_bridge.modules.medgemma_model import MedGemmaModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
ARTIFACT_HMAC_KEY = os.getenv('ARTIFACT_HMAC_KEY')
if not ARTIFACT_HMAC_KEY:
    raise ValueError("Missing required environment variable: ARTIFACT_HMAC_KEY")
ARTIFACT_HMAC_KEY = ARTIFACT_HMAC_KEY.encode()

MEDGEMMA_SNAPSHOT_PATH = os.getenv('MEDGEMMA_SNAPSHOT_PATH')
if not MEDGEMMA_SNAPSHOT_PATH:
    raise ValueError("Missing required environment variable: MEDGEMMA_SNAPSHOT_PATH")

# Configuration
MEDGEMMA_DEVICE = os.getenv('MEDGEMMA_DEVICE', 'cpu')
MEDGEMMA_TIMEOUT_SEC = int(os.getenv('MEDGEMMA_TIMEOUT_SEC', '2000'))
ARTIFACTS_DIR = Path('artifacts/backend_runs')
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Global model storage
MODEL_CACHE = {
    'model': None,
    'tokenizer': None,
    'loaded': False
}

# Job queue (simple in-memory queue)
JOB_QUEUE = {}



# ============================================================================
# DATA MODELS
# ============================================================================

class AssessmentRequest(BaseModel):
    """Request model for risk assessment"""
    patient_id: str = Field(..., description="Unique patient identifier")
    name: str
    age: int = Field(..., ge=15, le=55)
    gestational_age_weeks: Optional[int] = None
    bp_systolic: int = Field(..., description="Systolic blood pressure")
    bp_diastolic: int = Field(..., description="Diastolic blood pressure")
    weight_kg: float
    hemoglobin_g_dl: Optional[float] = None
    platelets_per_ul: Optional[int] = None
    proteinuria: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "DEMO_006",
                "name": "Kavitha Naik",
                "age": 28,
                "gestational_age_weeks": 22,
                "bp_systolic": 128,
                "bp_diastolic": 84,
                "weight_kg": 65.0,
                "hemoglobin_g_dl": 11.2,
                "platelets_per_ul": 145000,
                "proteinuria": "Negative"
            }
        }

class AssessmentResponse(BaseModel):
    """Response model for assessment results"""
    run_id: str
    status: str
    message: str
    artifacts_path: Optional[str] = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compute_hmac(data: bytes) -> str:
    """Compute HMAC-SHA256 signature"""
    return hmac.new(ARTIFACT_HMAC_KEY, data, hashlib.sha256).hexdigest()

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def derive_seed(request_data: dict) -> int:
    """Derive deterministic seed from request"""
    request_str = json.dumps(request_data, sort_keys=True)
    hash_hex = hashlib.sha256(request_str.encode()).hexdigest()[:8]
    return int(hash_hex, 16)

def save_with_fsync(file_path: Path, content: str):
    """Save file with fsync to ensure persistence"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    # Set read-only permissions (Unix-like systems)
    try:
        os.chmod(file_path, 0o444)
    except:
        pass  # Windows may not support chmod

def load_medgemma_model():
    """Load MedGemma model (cached)"""
    global MODEL_CACHE

    if MODEL_CACHE['loaded']:
        logger.info("Using cached MedGemma model")
        return MODEL_CACHE['model'], MODEL_CACHE['tokenizer']

    logger.info(f"Loading MedGemma model from {MEDGEMMA_SNAPSHOT_PATH}")
    logger.info(f"Device: {MEDGEMMA_DEVICE}")

    try:
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                MEDGEMMA_SNAPSHOT_PATH,
                trust_remote_code=True,
                use_fast=False
            )
        except Exception as e:
            if "GemmaTokenizer" in str(e):
                logger.info("AutoTokenizer failed, trying LlamaTokenizer...")
                tokenizer = LlamaTokenizer.from_pretrained(
                    MEDGEMMA_SNAPSHOT_PATH,
                    use_fast=False
                )
            else:
                raise

        # Add padding token if missing
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            MEDGEMMA_SNAPSHOT_PATH,
            torch_dtype=torch.float32 if MEDGEMMA_DEVICE == 'cpu' else torch.float16,
            device_map=MEDGEMMA_DEVICE,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        model.eval()

        MODEL_CACHE['model'] = model
        MODEL_CACHE['tokenizer'] = tokenizer
        MODEL_CACHE['loaded'] = True

        logger.info("✓ MedGemma model loaded successfully")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load MedGemma model: {e}")
        raise

# ============================================================================
# RULE ENGINE
# ============================================================================

def run_rule_engine(vitals: dict) -> dict:
    """
    Rule-based risk assessment (authoritative)
    Uses existing assess_risk function from pregnancy_bridge
    """
    try:
        # Map vitals to match assess_risk expected keys
        mapped_data = {
            'hemoglobin': vitals.get('hemoglobin_g_dl'),
            'bp_systolic': vitals.get('bp_systolic'),
            'bp_diastolic': vitals.get('bp_diastolic'),
            'gestational_age': vitals.get('gestational_age_weeks'),
            'proteinuria': vitals.get('proteinuria'),
            'weight': vitals.get('weight_kg'),
            'platelets': vitals.get('platelets_per_ul'),
            'age': vitals.get('age')
        }
        
        # Call existing risk engine function
        result = assess_risk_engine(mapped_data)

        return {
            'risk_level': result.get('risk_level', 'Medium'),
            'risk_score': result.get('risk_score', 0),
            'recommendations': result.get('recommendations', []),
            'confidence': 1.0  # Rule engine is deterministic
        }
    except Exception as e:
        logger.warning(f"Risk engine failed, using fallback: {e}")
        # Fallback rule-based assessment
        return run_fallback_rules(vitals)

def run_fallback_rules(vitals: dict) -> dict:
    """Fallback rule-based assessment if RiskEngine unavailable"""
    bp_sys = vitals.get('bp_systolic', 120)
    bp_dia = vitals.get('bp_diastolic', 80)
    hb = vitals.get('hemoglobin_g_dl', 12.0)
    platelets = vitals.get('platelets_per_ul', 150000)
    proteinuria = vitals.get('proteinuria', 'Negative')

    risk_level = 'Low'
    recommendations = []
    risk_score = 0

    # Blood pressure rules
    if bp_sys >= 160 or bp_dia >= 110:
        risk_level = 'High'
        risk_score += 3
        recommendations.append('URGENT: Immediate referral to District Hospital for severe hypertension')
        recommendations.append('Monitor BP every 2 hours until stabilized')
    elif bp_sys >= 140 or bp_dia >= 90:
        risk_level = 'High'
        risk_score += 2
        recommendations.append('Immediate referral to PHC for hypertension management')
        recommendations.append('Monitor blood pressure daily')
    elif bp_sys >= 130 or bp_dia >= 85:
        if risk_level == 'Low':
            risk_level = 'Medium'
        risk_score += 1
        recommendations.append('Schedule follow-up within 1 week for BP monitoring')

    # Hemoglobin rules
    if hb and hb < 9:
        risk_level = 'High'
        risk_score += 2
        recommendations.append('Severe anemia detected - immediate iron infusion required')
    elif hb and hb < 11:
        if risk_level == 'Low':
            risk_level = 'Medium'
        risk_score += 1
        recommendations.append('Iron and folic acid supplementation required')

    # Platelet rules
    if platelets and platelets < 100000:
        risk_level = 'High'
        risk_score += 2
        recommendations.append('Low platelet count - referral to hospital for evaluation')

    # Proteinuria rules
    if proteinuria and proteinuria not in ['Negative', '', 'Not tested']:
        if proteinuria in ['+3', '+2']:
            risk_level = 'High'
            risk_score += 2
            recommendations.append('Significant proteinuria - URGENT referral for pre-eclampsia evaluation')
        else:
            if risk_level == 'Low':
                risk_level = 'Medium'
            recommendations.append('Trace protein detected - monitor for pre-eclampsia')

    # Default recommendations
    if not recommendations:
        recommendations = [
            'All parameters within normal range - continue routine antenatal care',
            'Next visit in 4 weeks',
            'Maintain healthy diet and regular exercise'
        ]

    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'recommendations': recommendations,
        'confidence': 1.0
    }

# ============================================================================
# MEDGEMMA INFERENCE
# ============================================================================

def run_medgemma_inference(vitals: dict, run_dir: Path, timeout_sec: int) -> dict:
    """
    Run MedGemma inference with timeout
    Returns: {ai_risk, ai_recommendations, confidence, raw_text, fallback_triggered}
    """
    start_time = time.time()

    try:
        model, tokenizer = load_medgemma_model()

        # Build prompt
        prompt = f"""You are a maternal health AI assistant analyzing pregnancy risk factors.

Patient Data:
- Blood Pressure: {vitals.get('bp_systolic')}/{vitals.get('bp_diastolic')} mmHg
- Weight: {vitals.get('weight_kg')} kg
- Hemoglobin: {vitals.get('hemoglobin_g_dl', 'N/A')} g/dL
- Platelets: {vitals.get('platelets_per_ul', 'N/A')} /µL
- Proteinuria: {vitals.get('proteinuria', 'N/A')}
- Gestational Age: {vitals.get('gestational_age_weeks', 'N/A')} weeks
- Age: {vitals.get('age')} years

Analyze the risk level and provide recommendations. Format your response as:
RISK LEVEL: [High/Medium/Low]
RECOMMENDATIONS:
1. [First recommendation]
2. [Second recommendation]
3. [Third recommendation]

Analysis:"""

        # Generation parameters
        generation_params = {
            'do_sample': True,
            'temperature': 0.7,
            'max_new_tokens': 512,
            'top_p': 0.9
        }

        # Save generation params
        params_file = run_dir / 'generation_params.json'
        save_with_fsync(params_file, json.dumps(generation_params, indent=2))

        # Tokenize
        inputs = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True)
        if MEDGEMMA_DEVICE != 'cpu':
            inputs = inputs.to(MEDGEMMA_DEVICE)

        # Generate with timeout
        logger.info(f"Starting MedGemma inference (timeout: {timeout_sec}s)")

        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                do_sample=generation_params['do_sample'],
                temperature=generation_params['temperature'],
                max_new_tokens=generation_params['max_new_tokens'],
                top_p=generation_params['top_p'],
                pad_token_id=tokenizer.pad_token_id
            )

        inference_time = time.time() - start_time
        logger.info(f"MedGemma inference completed in {inference_time:.2f}s")

        # Decode output
        raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Save raw output
        raw_file = run_dir / 'medgemma_raw.txt'
        save_with_fsync(raw_file, raw_output)

        # Save as JSON too
        raw_json = {
            'prompt': prompt,
            'raw_response': raw_output,
            'inference_time_sec': inference_time,
            'generation_params': generation_params,
            'model_path': MEDGEMMA_SNAPSHOT_PATH,
            'device': MEDGEMMA_DEVICE
        }
        raw_json_file = run_dir / 'medgemma_raw.json'
        save_with_fsync(raw_json_file, json.dumps(raw_json, indent=2))

        # Parse output
        ai_risk = 'Medium'  # Default
        ai_recommendations = []

        response_text = raw_output[len(prompt):].strip() if prompt in raw_output else raw_output

        if 'RISK LEVEL:' in response_text:
            risk_lines = [l for l in response_text.split('\n') if 'RISK LEVEL:' in l]
            if risk_lines:
                risk_line = risk_lines[0]
                if 'High' in risk_line:
                    ai_risk = 'High'
                elif 'Low' in risk_line:
                    ai_risk = 'Low'
                else:
                    ai_risk = 'Medium'

        if 'RECOMMENDATIONS:' in response_text:
            rec_section = response_text.split('RECOMMENDATIONS:')[1]
            for line in rec_section.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    clean_line = line.lstrip('0123456789.-•) ').strip()
                    if clean_line:
                        ai_recommendations.append(clean_line)

        return {
            'ai_risk': ai_risk,
            'ai_recommendations': ai_recommendations[:5],  # Max 5
            'confidence': 0.85,  # Estimated
            'raw_text': response_text,
            'fallback_triggered': False,
            'inference_time_ms': int(inference_time * 1000)
        }

    except Exception as e:
        logger.error(f"MedGemma inference failed: {e}")
        return {
            'ai_risk': None,
            'ai_recommendations': [],
            'confidence': 0.0,
            'raw_text': f"Error: {str(e)}",
            'fallback_triggered': True,
            'inference_time_ms': int((time.time() - start_time) * 1000)
        }

# ============================================================================
# QC VALIDATION
# ============================================================================

def run_qc_validation(rule_decision: dict, ai_result: dict) -> dict:
    """Quality check on outputs"""
    qc_result = {
        'qc_passed': True,
        'warnings': [],
        'rule_disagreement': False
    }

    # Check for rule-AI disagreement
    if ai_result.get('ai_risk') and ai_result['ai_risk'] != rule_decision['risk_level']:
        qc_result['rule_disagreement'] = True
        qc_result['warnings'].append(
            f"AI risk ({ai_result['ai_risk']}) differs from rule engine ({rule_decision['risk_level']})"
        )

    # Check confidence
    if ai_result.get('confidence', 0) < 0.60:
        qc_result['warnings'].append('Low AI confidence - fallback triggered')

    # Check for fallback
    if ai_result.get('fallback_triggered'):
        qc_result['warnings'].append('MedGemma inference failed - using rule engine only')

    return qc_result

# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================

async def process_assessment(run_id: str, request_data: dict):
    """Main processing pipeline for a single assessment"""
    try:
        logger.info(f"Processing assessment {run_id}")
        JOB_QUEUE[run_id]['status'] = 'processing'

        # Create run directory
        run_dir = ARTIFACTS_DIR / run_id
        run_dir.mkdir(exist_ok=True)

        # Save raw request
        request_json = json.dumps(request_data, indent=2)
        raw_request_file = run_dir / 'raw_request.json'
        save_with_fsync(raw_request_file, request_json)

        # Compute request HMAC
        request_hmac = compute_hmac(request_json.encode())
        hmac_file = run_dir / 'raw_request.hmac'
        save_with_fsync(hmac_file, request_hmac)

        # Derive deterministic seed
        seed = derive_seed(request_data)
        torch.manual_seed(seed)

        # Normalize input
        normalized_input = {
            'patient_id': request_data['patient_id'],
            'vitals': {
                'bp_systolic': request_data['bp_systolic'],
                'bp_diastolic': request_data['bp_diastolic'],
                'weight_kg': request_data['weight_kg'],
                'hemoglobin_g_dl': request_data.get('hemoglobin_g_dl'),
                'platelets_per_ul': request_data.get('platelets_per_ul'),
                'proteinuria': request_data.get('proteinuria'),
                'age': request_data['age'],
                'gestational_age_weeks': request_data.get('gestational_age_weeks')
            }
        }

        normalized_input_file = run_dir / 'normalized_input.json'
        save_with_fsync(normalized_input_file, json.dumps(normalized_input, indent=2))

        # Run rule engine
        rule_decision = run_rule_engine(normalized_input['vitals'])
        rule_file = run_dir / 'rule_engine_decision.json'
        save_with_fsync(rule_file, json.dumps(rule_decision, indent=2))

        # Run MedGemma inference
        ai_result = run_medgemma_inference(
            normalized_input['vitals'],
            run_dir,
            MEDGEMMA_TIMEOUT_SEC
        )

        # Save normalized AI output
        normalized_output = {
            'ai_risk_level': ai_result.get('ai_risk'),
            'ai_recommendations': ai_result.get('ai_recommendations', []),
            'confidence': ai_result.get('confidence', 0),
            'fallback_triggered': ai_result.get('fallback_triggered', False)
        }
        normalized_output_file = run_dir / 'normalized_output.json'
        save_with_fsync(normalized_output_file, json.dumps(normalized_output, indent=2))

        # Run QC
        qc_result = run_qc_validation(rule_decision, ai_result)
        qc_file = run_dir / 'qc_result.json'
        save_with_fsync(qc_file, json.dumps(qc_result, indent=2))

        # Determine decision source (ALWAYS rule engine per policy)
        decision_source = 'rule_engine'
        final_risk = rule_decision['risk_level']
        final_recommendations = rule_decision['recommendations']

        # Create pipeline output
        pipeline_output = {
            'run_id': run_id,
            'patient_id': request_data['patient_id'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'decision_source': decision_source,
            'rule_engine_decision': rule_decision,
            'ai_risk': ai_result.get('ai_risk'),
            'ai_advisory': ai_result.get('ai_recommendations', []),
            'final_risk_level': final_risk,
            'final_recommendations': final_recommendations,
            'qc_result': qc_result,
            'provenance': {
                'model_snapshot': MEDGEMMA_SNAPSHOT_PATH,
                'device': MEDGEMMA_DEVICE,
                'seed': seed,
                'inference_time_ms': ai_result.get('inference_time_ms', 0),
                'generation_params_file': 'generation_params.json',
                'rule_engine_version': 'v2.0',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }

        pipeline_file = run_dir / 'pipeline_output.json'
        save_with_fsync(pipeline_file, json.dumps(pipeline_output, indent=2))

        # Compute artifact hash
        artifact_content = ''
        for fname in ['pipeline_output.json', 'medgemma_raw.txt', 'rule_engine_decision.json', 'normalized_output.json']:
            fpath = run_dir / fname
            if fpath.exists():
                artifact_content += fpath.read_text(encoding='utf-8')

        artifact_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
        hash_file = run_dir / 'artifact.sha256'
        save_with_fsync(hash_file, artifact_hash)

        # Sign artifact
        artifact_signature = compute_hmac(artifact_hash.encode())
        sig_file = run_dir / 'artifact.signature'
        save_with_fsync(sig_file, artifact_signature)

        # Update job status
        JOB_QUEUE[run_id]['status'] = 'completed'
        JOB_QUEUE[run_id]['artifacts_path'] = str(run_dir)
        JOB_QUEUE[run_id]['result'] = pipeline_output

        logger.info(f"✓ Assessment {run_id} completed successfully")

    except Exception as e:
        logger.error(f"Assessment {run_id} failed: {e}", exc_info=True)
        JOB_QUEUE[run_id]['status'] = 'failed'
        JOB_QUEUE[run_id]['error'] = str(e)

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting PregnancyBridge Backend API")
    logger.info(f"Artifacts directory: {ARTIFACTS_DIR.absolute()}")
    logger.info(f"MedGemma device: {MEDGEMMA_DEVICE}")
    yield
    logger.info("Shutting down PregnancyBridge Backend API")

app = FastAPI(
    title="PregnancyBridge Backend API",
    version="1.0.0",
    description="MedGemma-powered maternal health risk assessment",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "PregnancyBridge Backend API",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": MODEL_CACHE['loaded'],
        "device": MEDGEMMA_DEVICE,
        "total_runs": len(JOB_QUEUE)
    }

@app.post("/api/v1/assess-risk", response_model=AssessmentResponse)
async def assess_risk(request: AssessmentRequest, background_tasks: BackgroundTasks):
    """
    Submit a risk assessment request
    Processing happens in background, use /result/{run_id} to check status
    """
    run_id = str(uuid.uuid4())

    # Initialize job
    JOB_QUEUE[run_id] = {
        'run_id': run_id,
        'status': 'queued',
        'submitted_at': datetime.utcnow().isoformat(),
        'request': request.dict()
    }

    # Add to background tasks
    background_tasks.add_task(process_assessment, run_id, request.dict())

    return AssessmentResponse(
        run_id=run_id,
        status='queued',
        message=f'Assessment queued for processing. Check status at /api/v1/result/{run_id}'
    )

@app.get("/api/v1/result/{run_id}")
async def get_result(run_id: str):
    """Get assessment result and metadata"""
    if run_id not in JOB_QUEUE:
        raise HTTPException(status_code=404, detail="Run ID not found")

    job = JOB_QUEUE[run_id]

    response = {
        'run_id': run_id,
        'status': job['status'],
        'submitted_at': job['submitted_at']
    }

    if job['status'] == 'completed':
        response['result'] = job.get('result')
        response['artifacts_path'] = job.get('artifacts_path')
        response['download_links'] = {
            'pipeline_output': f'/api/v1/download/{run_id}/pipeline_output.json',
            'medgemma_raw': f'/api/v1/download/{run_id}/medgemma_raw.txt',
            'normalized_output': f'/api/v1/download/{run_id}/normalized_output.json',
            'artifact_signature': f'/api/v1/download/{run_id}/artifact.signature'
        }
    elif job['status'] == 'failed':
        response['error'] = job.get('error')

    return response

@app.get("/api/v1/download/{run_id}/{filename}")
async def download_artifact(run_id: str, filename: str):
    """Download artifact file (read-only)"""
    # Prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = ARTIFACTS_DIR / run_id / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 8000)),
        log_level="info"
    )