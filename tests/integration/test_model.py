import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCAL_CACHE = Path("D:/huggingface_cache/hub/models--google--medgemma-1.5-4b-it")
snapshot_dirs = list(LOCAL_CACHE.glob("snapshots/*"))
model_path = snapshot_dirs[0]

logger.info(f"Loading from: {model_path}")

logger.info("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
logger.info("Tokenizer loaded")

offload_dir = Path("D:/MedGemma/model_offload")
offload_dir.mkdir(exist_ok=True)
logger.info(f"Offload directory: {offload_dir}")

logger.info("Loading model with disk offload (will take 3-5 minutes)...")

model = AutoModelForCausalLM.from_pretrained(
    str(model_path),
    local_files_only=True,
    dtype=torch.float16,
    low_cpu_mem_usage=True,
    offload_folder=str(offload_dir)
)

logger.info("Moving model to CPU...")
model = model.to("cpu")

logger.info("SUCCESS! Model loaded")

logger.info("Testing inference...")
test_input = tokenizer("Extract hemoglobin: 9.2 g/dL", return_tensors="pt")

with torch.no_grad():
    output = model.generate(
        **test_input, 
        max_new_tokens=20,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        temperature=None,
        top_p=None
    )
    
result = tokenizer.decode(output[0], skip_special_tokens=True)
logger.info(f"Test result: {result}")
logger.info("Model is ready for use!")

