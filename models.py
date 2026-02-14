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
    root_cause_summary: str
    suggested_fix: str

class DriftResult(BaseModel):
    drift_detected: bool
    drift_keys: List[str]
    version_mismatch: Optional[bool] = False
    suggested_fix: Optional[str] = None

class HealthCheckResult(BaseModel):
    service_name: str
    status: str # UP | DOWN
    latency_ms: int
    suggested_fix: Optional[str] = None

class ScoreResult(BaseModel):
    readiness_score: int
    status: ReadinessStatus
    penalties: List[str]
    recommendation: Recommendation
    audit_report: Optional[Dict[str, Any]] = None

# --- API Interaction Models ---

class EvaluateRequest(BaseModel):
    build_id: str
    environment: str

class EvaluateResponse(BaseModel):
    success: bool
    data: Optional[ScoreResult] = None
    error: Optional[Dict[str, str]] = None

class ToolSuccessResponse(BaseModel):
    success: bool = True
    data: Any

class ToolErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, str]
