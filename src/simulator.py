"""IoT Telemetry Simulator for Rooftop Solar Prosumers in Vietnam.
Simulates realistic 24-hour generation curves and injects fraud/anomaly scenarios.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.config import SUNRISE_HOUR, SUNSET_HOUR

# Danh sách hộ dân / cơ sở phát điện áp mái mẫu tại TP.HCM & lân cận
DEFAULT_PROSUMERS = [
    {"id": "REC-HCM-001", "name": "Hộ Gia Đình Q.7 (Phú Mỹ Hưng)", "capacity_kwp": 5.0, "anomaly_type": None},
    {"id": "REC-HCM-002", "name": "Xưởng Mộc Thủ Đức", "capacity_kwp": 25.0, "anomaly_type": "FROZEN"},
    {"id": "REC-HCM-003", "name": "Hộ Gia Đình Bình Chánh", "capacity_kwp": 8.0, "anomaly_type": "NIGHT_FRAUD"},
    {"id": "REC-HCM-004", "name": "Kho Logistics Tân Bình", "capacity_kwp": 45.0, "anomaly_type": None},
    {"id": "REC-HCM-005", "name": "Hộ Gia Đình Hóc Môn", "capacity_kwp": 10.0, "anomaly_type": "OVERCAPACITY"},
    {"id": "REC-BD-006",  "name": "Nhà Xưởng Phụ Trợ Bình Dương", "capacity_kwp": 60.0, "anomaly_type": None},
]

def generate_clear_sky_irradiance(hour: int, date_seed: int = 42) -> float:
    """Mô phỏng bức xạ mặt trời (W/m2) theo chu kỳ ngày đêm tại miền Nam VN."""
    np.random.seed(date_seed + hour)
    if hour < SUNRISE_HOUR or hour > SUNSET_HOUR:
        return 0.0
    
    # Đường cong hình sin chuẩn hóa từ 6h đến 18h
    day_fraction = (hour - SUNRISE_HOUR) / (SUNSET_HOUR - SUNRISE_HOUR)
    base_irradiance = np.sin(day_fraction * np.pi) * 950.0  # Đỉnh khoảng 950 W/m2
    
    # Thêm yếu tố mây ngẫu nhiên (Cloud fluctuation)
    cloud_factor = np.random.uniform(0.85, 1.0)
    return round(float(max(0.0, base_irradiance * cloud_factor)), 1)

def simulate_prosumers(date_str: str = None, seed: int = 42) -> pd.DataFrame:
    """
    Sinh chuỗi dữ liệu 24 giờ cho danh sách prosumers kèm các kịch bản gian lận mô phỏng.
    """
    np.random.seed(seed)
    if date_str is None:
        target_date = datetime.now().replace(minute=0, second=0, microsecond=0)
    else:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")

    records = []

    for prosumer in DEFAULT_PROSUMERS:
        p_id = prosumer["id"]
        name = prosumer["name"]
        cap = prosumer["capacity_kwp"]
        anomaly = prosumer["anomaly_type"]

        frozen_val = None

        for h in range(24):
            record_time = target_date.replace(hour=h)
            irradiance = generate_clear_sky_irradiance(h, date_seed=seed)
            
            # Nhiệt độ môi trường (mát vào ban đêm, nóng đỉnh điểm lúc 13h)
            temp_ambient = 25.0 + 9.0 * np.sin((h - 4) / 24 * 2 * np.pi) if 6 <= h <= 18 else 26.0
            temp_ambient += np.random.uniform(-0.5, 0.5)

            # Công suất phát lý thuyết: P = P_peak * (Irradiance / 1000) * hiệu suất nhiệt
            # Hiệu suất giảm 0.4% mỗi độ C khi nhiệt độ tấm pin > 25°C
            temp_cell = temp_ambient + (irradiance / 800.0) * 25.0
            derating = 1.0 - max(0.0, (temp_cell - 25.0) * 0.004)
            
            if irradiance > 0:
                raw_power = cap * (irradiance / 1000.0) * derating
                raw_power += np.random.normal(0, 0.02 * cap)
                raw_power = max(0.0, raw_power)
            else:
                raw_power = 0.0

            anomaly_note = "NORMAL"

            # Áp dụng kịch bản bất thường / gian lận để thử nghiệm thuật toán
            if anomaly == "NIGHT_FRAUD" and h in [22, 23, 1]:
                # Gian lận: Khai khống sản lượng ban đêm (ví dụ dùng máy phát hoặc hack công tơ)
                raw_power = cap * 0.65  # Khai khống 65% công suất
                anomaly_note = "INJECTED_NIGHT_FRAUD"

            elif anomaly == "OVERCAPACITY" and h in [11, 12, 13]:
                # Gian lận: Báo vượt 180% công suất biến tần cho phép
                raw_power = cap * 1.85
                anomaly_note = "INJECTED_OVERCAPACITY"

            elif anomaly == "FROZEN" and h in [14, 15, 16, 17]:
                # Lỗi: Treo dữ liệu/replay attack (giữ nguyên một giá trị cứng ngắc)
                if frozen_val is None:
                    frozen_val = cap * 0.52
                raw_power = frozen_val
                anomaly_note = "INJECTED_FROZEN"

            energy_kwh = round(float(raw_power), 3)  # Trong 1 giờ, kW ~ kWh
            active_power_kw = round(float(raw_power), 3)

            records.append({
                "timestamp": record_time,
                "hour": h,
                "prosumer_id": p_id,
                "prosumer_name": name,
                "capacity_kwp": cap,
                "irradiance_wm2": irradiance,
                "ambient_temp_c": round(float(temp_ambient), 1),
                "inverter_temp_c": round(float(temp_cell), 1),
                "active_power_kw": active_power_kw,
                "energy_kwh": energy_kwh,
                "injected_scenario": anomaly_note
            })

    return pd.DataFrame(records)
