import pytest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture(scope="session")
def medgemma_model():
    """Load MedGemma once per test session to avoid reload overhead."""
    try:
        from pregnancy_bridge.modules.medgemma_extractor import get_clinical_reasoner
        reasoner = get_clinical_reasoner()
        yield reasoner
    except Exception as e:
        pytest.skip(f"MedGemma model unavailable: {e}")
        yield None

@pytest.fixture(scope="session")
def asha_phrase_library():
    """Load ASHA phrase library once per session."""
    import json
    phrase_lib_path = project_root / "data" / "i18n" / "asha_phrase_library.json"
    if not phrase_lib_path.exists():
        pytest.skip("ASHA phrase library not found")
    with open(phrase_lib_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def test_cases_dir():
    """Return path to test cases directory."""
    return project_root / "data" / "test_cases"

@pytest.fixture
def output_dir():
    """Return and create output directory for test results."""
    output_path = project_root / "outputs" / "validation"
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

@pytest.fixture
def temporal_risk_engine():
    """Initialize temporal risk engine - skip if not available."""
    try:
        from pregnancy_bridge.modules.temporal_risk_engine import TemporalRiskEngine
        return TemporalRiskEngine()
    except ImportError:
        pytest.skip("TemporalRiskEngine not available")

@pytest.fixture
def evidence_linker():
    """Initialize evidence linking module - skip if not available."""
    try:
        from pregnancy_bridge.modules.evidence_linker import EvidenceLinker
        return EvidenceLinker()
    except ImportError:
        pytest.skip("EvidenceLinker not available")
