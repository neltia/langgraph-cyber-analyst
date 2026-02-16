from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    is_malicious: bool = Field(description="악성 여부 판단")
    tid: str = Field(description="식별된 MITRE Technique ID (예: T1190)")
    technique_name: str = Field(description="기법 명칭")
    tactic: str = Field(description="주요 전술 카테고리 (예: Initial Access)")
    sub_tactic: Optional[str] = Field(description="서브 기법 ID (있을 경우, 예: T1190.001)")
    confidence: float = Field(ge=0, le=1, description="판단 신뢰도 점수")
    reasoning: str = Field(description="단순 패턴이 아닌 기술적 매커니즘에 기반한 분석 근거")


class AgentState(TypedDict):
    payload: str
    candidates: List[str]
    analysis: Optional[AnalysisResult]
    iteration: int
    feedback: str
    is_final: bool
