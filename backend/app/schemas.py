from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime

class PredictionRequest(BaseModel):
    """
    Pydantic schema representing the 15 exact features expected by the ML model.
    Uses Field aliases to map valid Python variable names to the exact
    raw feature column names from CICIDS2017.
    """

    destination_port: float  = Field(..., alias="Destination Port")
    flow_duration: float = Field(..., alias="Flow Duration")
    total_fwd_packets: float = Field(..., alias="Total Fwd Packets")
    total_backward_packets: float = Field(..., alias="Total Backward Packets")
    total_length_of_fwd_packets: float = Field(..., alias="Total Length of Fwd Packets")
    total_length_of_bwd_packets: float = Field(..., alias="Total Length of Bwd Packets")
    fwd_packet_length_mean: float = Field(..., alias="Fwd Packet Length Mean")
    bwd_packet_length_mean: float = Field(..., alias="Bwd Packet Length Mean")
    flow_bytes_s: float = Field(..., alias="Flow Bytes/s")
    flow_packets_s: float = Field(..., alias="Flow Packets/s")
    packet_length_mean: float = Field(..., alias="Packet Length Mean")
    packet_length_std: float = Field(..., alias="Packet Length Std")
    average_packet_size: float = Field(..., alias="Average Packet Size")
    active_mean: float = Field(..., alias="Active Mean")
    idle_mean: float = Field(..., alias="Idle Mean")

    attack_type: Optional[str] = Field(default=None, alias="attack_type")

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "Destination Port": 80,
                "Flow Duration": 1000,
                "Total Fwd Packets": 10,
                "Total Backward Packets": 8,
                "Total Length of Fwd Packets": 500,
                "Total Length of Bwd Packets": 1200,
                "Fwd Packet Length Mean": 50.0,
                "Bwd Packet Length Mean": 150.0,
                "Flow Bytes/s": 1700.0,
                "Flow Packets/s": 18.0,
                "Packet Length Mean": 94.4,
                "Packet Length Std": 12.5,
                "Average Packet Size": 100.0,
                "Active Mean": 0.0,
                "Idle Mean": 0.0,
            }
        }
    )

class PredictionResponse(BaseModel):
    """
    Pydantic schema matching the exact output dictionary structure returned
    by ModelHandler.predict().
    """

    prediction: str
    prediction_id: int
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None

class PredictionLogOut(BaseModel):
    """
    Pydantic schema for serializing PredictionLog rows returned by GET /logs.
    from_attributes=True lets this read directly off the SQLAlchemy ORM object.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    predicted_label: str
    ground_truth_label: Optional[str] = None
    prediction_id: int
    input_features: Dict[str, Any]
    confidence: float
    probabilities: Optional[Dict[str, float]] = None

class LabelCount(BaseModel):
    label: str
    count: int

class VolumeBucket(BaseModel):
    time: str
    count: int
    threats: int

class StatsSummaryResponse(BaseModel):
    total_inspected: int
    benign_count: int
    threat_count: int
    avg_confidence: float
    label_distribution: List[LabelCount]
    volume_over_time: List[VolumeBucket]