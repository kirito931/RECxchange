"""Configuration constants and parameters for RECxchange platform."""

# Hệ số phát thải lưới điện Việt Nam (Grid Emission Factor)
# Nguồn tham khảo: Cục Biến đổi khí hậu / EVN (tCO2/MWh hoặc kgCO2/kWh)
VIETNAM_GRID_EMISSION_FACTOR = 0.7212  # kg CO2 / kWh

# Giá tham chiếu
CBAM_BENCHMARK_PRICE_EUR_PER_TON = 80.0  # ~80 EUR / tấn CO2 theo thị trường EU ETS
EUR_TO_VND = 27000  # Tỷ giá ước lượng
REC_PRICE_PER_MWH_VND = 50000  # ~2 USD / MWh (~50 VND / kWh)

# Chuẩn kỹ thuật năng lượng mặt trời (Solar physics bounds)
SUNRISE_HOUR = 6
SUNSET_HOUR = 18
PEAK_SOLAR_START = 11
PEAK_SOLAR_END = 13

# Ngưỡng an toàn vật lý
INVERTER_OVERLOAD_TOLERANCE = 1.15  # Tối đa 115% công suất danh định do nhiệt độ/bức xạ đặc biệt
MIN_IRRADIANCE_FOR_GENERATION = 20.0  # W/m2 - dưới mức này inverter không thể phát điện

# Trạng thái xác minh dữ liệu
STATUS_VERIFIED = "VERIFIED"
STATUS_FLAGGED = "FLAGGED_ANOMALY"

# Mã lỗi xác minh
ERR_NIGHT_GENERATION = "ERR_NIGHT_GEN"       # Phát điện khi không có bức xạ (ban đêm)
ERR_OVER_CAPACITY = "ERR_OVER_CAPACITY"     # Vượt quá công suất định mức inverter
ERR_FROZEN_DATA = "ERR_FROZEN_DATA"         # Số liệu đóng băng (treo cảm biến/replay attack)
ERR_PHYSICAL_MISMATCH = "ERR_PHYS_MISMATCH" # Công suất không khớp với bức xạ đo lường
