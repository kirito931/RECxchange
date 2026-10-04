"""Data Verification & Anomaly Detection Engine for RECxchange.
Validates IoT telemetry against physics bounds, solar radiation models, and statistical criteria.
Prevents greenwashing and fraudulent REC generation.
"""

import pandas as pd
import numpy as np
from src.config import (
    STATUS_VERIFIED,
    STATUS_FLAGGED,
    ERR_NIGHT_GENERATION,
    ERR_OVER_CAPACITY,
    ERR_FROZEN_DATA,
    ERR_PHYSICAL_MISMATCH,
    INVERTER_OVERLOAD_TOLERANCE,
    MIN_IRRADIANCE_FOR_GENERATION
)

def verify_readings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Xác minh từng bản ghi sản lượng điện mặt trời theo tiêu chuẩn kỹ thuật & vật lý.
    Gắn nhãn VERIFIED hoặc FLAGGED_ANOMALY kèm lý do chi tiết.
    """
    df = df.copy()
    df["verification_status"] = STATUS_VERIFIED
    df["anomaly_reasons"] = ""

    # Sắp xếp theo prosumer và thời gian
    df = df.sort_values(by=["prosumer_id", "timestamp"]).reset_index(drop=True)

    for i, row in df.iterrows():
        reasons = []

        # 1. Kiểm tra phát điện ban đêm (Physics Check 1)
        # Nếu bức xạ < 20 W/m2 mà công suất phát > 0.05 kW -> Gian lận hoặc đấu nối nhầm nguồn
        if row["irradiance_wm2"] < MIN_IRRADIANCE_FOR_GENERATION and row["active_power_kw"] > 0.05:
            reasons.append(ERR_NIGHT_GENERATION)

        # 2. Kiểm tra quá công suất định mức (Physics Check 2)
        # Công suất tức thời không thể vượt quá 115% công suất danh định của inverter
        max_allowed_kw = row["capacity_kwp"] * INVERTER_OVERLOAD_TOLERANCE
        if row["active_power_kw"] > max_allowed_kw:
            reasons.append(f"{ERR_OVER_CAPACITY} ({row['active_power_kw']:.1f}kW > {max_allowed_kw:.1f}kW)")

        # 3. Kiểm tra sai lệch bức xạ - công suất (Physical Mismatch Check)
        # Bức xạ yếu (< 150 W/m2) nhưng công suất lại đạt > 50% công suất danh định
        if row["irradiance_wm2"] < 150.0 and row["active_power_kw"] > (row["capacity_kwp"] * 0.5):
            reasons.append(ERR_PHYSICAL_MISMATCH)

        if reasons:
            df.at[i, "verification_status"] = STATUS_FLAGGED
            df.at[i, "anomaly_reasons"] = "; ".join(reasons)

    # 4. Kiểm tra dữ liệu đóng băng / Replay Attack (Statistical Check)
    # Nếu công suất > 0 và giữ nguyên giá trị suốt 3 giờ liên tiếp giữa ban ngày -> cảm biến treo
    for p_id, group in df.groupby("prosumer_id"):
        diffs = group["active_power_kw"].diff()
        # Tìm chuỗi 3 giờ liên tiếp diff == 0 trong khung giờ nắng
        for idx in group.index[2:]:
            h = df.at[idx, "hour"]
            val = df.at[idx, "active_power_kw"]
            val_prev1 = df.at[idx - 1, "active_power_kw"]
            val_prev2 = df.at[idx - 2, "active_power_kw"]
            if 9 <= h <= 16 and val > 0.5:
                if np.isclose(val, val_prev1, atol=1e-3) and np.isclose(val, val_prev2, atol=1e-3):
                    current_reasons = df.at[idx, "anomaly_reasons"]
                    reason_str = ERR_FROZEN_DATA if not current_reasons else current_reasons + f"; {ERR_FROZEN_DATA}"
                    df.at[idx, "verification_status"] = STATUS_FLAGGED
                    df.at[idx, "anomaly_reasons"] = reason_str

    return df

def get_verification_summary(df: pd.DataFrame) -> dict:
    """Tóm tắt kết quả kiểm định dữ liệu mạng lưới."""
    total_records = len(df)
    verified_records = len(df[df["verification_status"] == STATUS_VERIFIED])
    flagged_records = len(df[df["verification_status"] == STATUS_FLAGGED])
    
    total_kwh_claimed = df["energy_kwh"].sum()
    verified_kwh = df[df["verification_status"] == STATUS_VERIFIED]["energy_kwh"].sum()
    fraud_kwh = df[df["verification_status"] == STATUS_FLAGGED]["energy_kwh"].sum()

    return {
        "total_records": total_records,
        "verified_records": verified_records,
        "flagged_records": flagged_records,
        "verification_rate_pct": round((verified_records / total_records) * 100, 1) if total_records else 0,
        "total_kwh_claimed": round(total_kwh_claimed, 2),
        "verified_kwh": round(verified_kwh, 2),
        "fraud_kwh": round(fraud_kwh, 2),
        "fraud_energy_pct": round((fraud_kwh / total_kwh_claimed) * 100, 1) if total_kwh_claimed else 0
    }
