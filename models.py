from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

# --- Tool Output Enums ---

class LogCategory(str, Enum):
    INFRA = "INFRA"
    CODE = "CODE"
    CONFIG = "CONFIG"
    DEPENDENCY = "DEPENDENCY"
    FLAKY = "FLAKY"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ReadinessStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    NOT_SAFE = "NOT_SAFE"

class Recommendation(str, Enum):
    ALLOW_AUTOMATION = "ALLOW_AUTOMATION"
    BLOCK_AUTOMATION = "BLOCK_AUTOMATION"

# --- Tool Result Models ---

class LogAnalysisResult(BaseModel):
    category: LogCategory
    severity: Severity
    confidence: float = Field(..., ge=0, le=1)
    explanation: str # Renamed from root_cause_summary
    suggested_fix: str

class DriftResult(BaseModel):
    drift_detected: bool
    drift_keys: List[str]
    explanation: str
    version_mismatch: Optional[bool] = False
    suggested_fix: Optional[str] = None

class HealthCheckResult(BaseModel):
    service_name: str
    status: str # UP | DOWN
    latency_ms: int
    explanation: str
    suggested_fix: Optional[str] = None

class ScoreResult(BaseModel):
    readiness_score: int
    status: ReadinessStatus
    penalties: List[str]
    recommendation: Recommendation
    explanation: str
    suggested_fix: Optional[str] = None
    audit_report: Optional[Dict[str, Any]] = None

# --- API Interaction Models ---

class EvaluateRequest(BaseModel):
    build_id: str
    environment: str

class EvaluateResponse(BaseModel):
    success: bool
    data: Optional[ScoreResult] = None
    error: Optional[Dict[str, str]] = None

class ServerHealth(BaseModel):
    status: str
    tools_registered: int
    environment: str
    config_loaded: bool

class DiscoveryResult(BaseModel):
    success: bool
    message: str
    discovered_projects: List[str]

class ToolResponse(BaseModel):
    """Universal wrapper for all tool responses to ensure consistent IDE parsing."""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, str]] = None
