"""Tamper-evident Granular Certificate (GC) Ledger for RECxchange.
Implements EnergyTag-compliant hourly certificates with SHA-256 block hash chaining.
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd
from src.config import STATUS_VERIFIED

class GranularCertificate:
    def __init__(self, cert_id: str, prosumer_id: str, prosumer_name: str,
                 timestamp: datetime, energy_kwh: float, prev_hash: str):
        self.cert_id = cert_id
        self.prosumer_id = prosumer_id
        self.prosumer_name = prosumer_name
        self.timestamp = timestamp.isoformat()
        self.hour = timestamp.hour
        self.energy_kwh = round(energy_kwh, 3)
        self.fuel_type = "SOLAR_ROOFTOP"
        self.grid_zone = "VIETNAM_SOUTH"
        self.standard = "ENERGYTAG_HOURLY_v1"
        self.status = "ISSUED"  # ISSUED, RETIRED, or CANCELLED
        self.beneficiary = None
        self.prev_hash = prev_hash
        self.hash = self.compute_hash()

    def to_dict(self) -> dict:
        return {
            "cert_id": self.cert_id,
            "prosumer_id": self.prosumer_id,
            "prosumer_name": self.prosumer_name,
            "timestamp": self.timestamp,
            "hour": self.hour,
            "energy_kwh": self.energy_kwh,
            "fuel_type": self.fuel_type,
            "grid_zone": self.grid_zone,
            "standard": self.standard,
            "status": self.status,
            "beneficiary": self.beneficiary,
            "prev_hash": self.prev_hash,
            "hash": self.hash
        }

    def compute_hash(self) -> str:
        payload = f"{self.cert_id}|{self.prosumer_id}|{self.timestamp}|{self.energy_kwh}|{self.prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class CertificateLedger:
    def __init__(self):
        self.certificates: List[GranularCertificate] = []
        self.genesis_hash = "0" * 64

    def mint_from_verified_data(self, verified_df: pd.DataFrame) -> List[GranularCertificate]:
        """Chỉ phát hành chứng chỉ cho dữ liệu đã VERIFIED và sản lượng > 0."""
        valid_rows = verified_df[
            (verified_df["verification_status"] == STATUS_VERIFIED) & 
            (verified_df["energy_kwh"] > 0)
        ].sort_values(by=["timestamp", "prosumer_id"])

        minted = []
        last_hash = self.certificates[-1].hash if self.certificates else self.genesis_hash

        for _, row in valid_rows.iterrows():
            ts = row["timestamp"]
            date_str = ts.strftime("%Y%m%d")
            hour_str = f"{row['hour']:02d}00"
            cert_id = f"GC-VN-{date_str}-{hour_str}-{row['prosumer_id']}"

            cert = GranularCertificate(
                cert_id=cert_id,
                prosumer_id=row["prosumer_id"],
                prosumer_name=row["prosumer_name"],
                timestamp=ts,
                energy_kwh=row["energy_kwh"],
                prev_hash=last_hash
            )
            self.certificates.append(cert)
            minted.append(cert)
            last_hash = cert.hash

        return minted

    def to_dataframe(self) -> pd.DataFrame:
        if not self.certificates:
            return pd.DataFrame()
        return pd.DataFrame([c.to_dict() for c in self.certificates])

    def verify_ledger_integrity(self) -> bool:
        """Kiểm tra tính toàn vẹn của chuỗi băm sổ cái."""
        if not self.certificates:
            return True
        
        expected_prev = self.genesis_hash
        for cert in self.certificates:
            if cert.prev_hash != expected_prev:
                return False
            if cert.hash != cert.compute_hash():
                return False
            expected_prev = cert.hash
        return True
