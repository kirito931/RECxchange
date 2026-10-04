"""Hourly Matching Engine & Scope 2 GHG Compliance Calculator.
Implements 24/7 Carbon-Free Energy (CFE) matching between SME demand and verified prosumer supply.
Calculates Market-based vs Location-based Scope 2 emissions and CBAM financial savings.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from src.config import (
    VIETNAM_GRID_EMISSION_FACTOR,
    CBAM_BENCHMARK_PRICE_EUR_PER_TON,
    EUR_TO_VND,
    REC_PRICE_PER_MWH_VND,
    STATUS_VERIFIED
)

# Hồ sơ phụ tải mẫu của các doanh nghiệp vừa và nhỏ (SME) xuất khẩu
SME_PRESETS = {
    "Dệt May (Quy mô ~250 công nhân)": {
        "sector": "May Mặc Xuất Khẩu",
        "shift_start": 7,
        "shift_end": 19,
        "base_load_kw": 20.0,
        "peak_load_kw": 85.0
    },
    "Chế biến Gỗ (Sản xuất đồ nội thất EU)": {
        "sector": "Chế Biến Gỗ Xuất Khẩu",
        "shift_start": 8,
        "shift_end": 17,
        "base_load_kw": 30.0,
        "peak_load_kw": 110.0
    },
    "Sản xuất Da Giày (Gia công phụ trợ)": {
        "sector": "Da Giày Phụ Trợ",
        "shift_start": 6,
        "shift_end": 20,
        "base_load_kw": 25.0,
        "peak_load_kw": 95.0
    }
}

def generate_sme_demand_profile(preset_name: str = "Dệt May (Quy mô ~250 công nhân)", scale_factor: float = 1.0) -> pd.DataFrame:
    """Sinh chuỗi phụ tải tiêu thụ điện 24 giờ của doanh nghiệp xuất khẩu."""
    preset = SME_PRESETS.get(preset_name, list(SME_PRESETS.values())[0])
    shift_start = preset["shift_start"]
    shift_end = preset["shift_end"]
    base_load = preset["base_load_kw"] * scale_factor
    peak_load = preset["peak_load_kw"] * scale_factor

    hours = list(range(24))
    demands = []

    np.random.seed(101)
    for h in hours:
        if shift_start <= h <= shift_end:
            # Giờ làm việc ca ngày: phụ tải cao, đỉnh điểm lúc 9h-11h và 14h-16h
            mid_factor = 0.9 + 0.1 * np.sin((h - shift_start) / (shift_end - shift_start) * np.pi)
            noise = np.random.uniform(-3.0, 3.0)
            demand = peak_load * mid_factor + noise
        else:
            # Ngoài giờ làm việc: duy trì phụ tải nền (chiếu sáng bảo vệ, tủ lạnh, văn phòng trực)
            demand = base_load + np.random.uniform(-1.0, 1.0)
        demands.append(round(max(5.0, demand), 2))

    return pd.DataFrame({
        "hour": hours,
        "sme_demand_kwh": demands
    })

def run_hourly_matching(verified_df: pd.DataFrame, demand_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Khớp lệnh từng giờ giữa nguồn cung VERIFIED từ các hộ áp mái và nhu cầu nhà máy.
    Tính toán chỉ số 24/7 CFE Score, Scope 2 GHG và giá trị kinh tế CBAM.
    """
    # Lọc chỉ lấy sản lượng đã xác minh
    clean_supply = verified_df[verified_df["verification_status"] == STATUS_VERIFIED]
    hourly_supply = clean_supply.groupby("hour")["energy_kwh"].sum().reset_index()
    hourly_supply.rename(columns={"energy_kwh": "verified_supply_kwh"}, inplace=True)

    # Ghép với bảng nhu cầu
    matching_df = pd.merge(demand_df, hourly_supply, on="hour", how="left")
    matching_df["verified_supply_kwh"] = matching_df["verified_supply_kwh"].fillna(0.0)

    # Khớp lệnh theo giờ (Hourly Matching)
    matching_df["matched_kwh"] = np.minimum(matching_df["sme_demand_kwh"], matching_df["verified_supply_kwh"])
    matching_df["grid_grey_kwh"] = matching_df["sme_demand_kwh"] - matching_df["matched_kwh"]
    matching_df["curtailed_excess_kwh"] = matching_df["verified_supply_kwh"] - matching_df["matched_kwh"]
    matching_df["cfe_match_pct"] = np.where(
        matching_df["sme_demand_kwh"] > 0,
        (matching_df["matched_kwh"] / matching_df["sme_demand_kwh"]) * 100.0,
        0.0
    ).round(1)

    # Tổng kết toàn ngày
    total_demand = matching_df["sme_demand_kwh"].sum()
    total_matched = matching_df["matched_kwh"].sum()
    total_grey = matching_df["grid_grey_kwh"].sum()
    total_supply = matching_df["verified_supply_kwh"].sum()
    total_excess = matching_df["curtailed_excess_kwh"].sum()
    overall_cfe_score = round((total_matched / total_demand) * 100.0, 1) if total_demand > 0 else 0

    # Tính toán phát thải Scope 2 (GHG Protocol Guidance)
    # 1. Location-based (Toàn bộ điện lấy theo hệ số phát thải lưới)
    scope2_location_based_kg = total_demand * VIETNAM_GRID_EMISSION_FACTOR
    
    # 2. Market-based (Chỉ tính phát thải trên phần điện lưới xám chưa được bù trừ bằng REC)
    scope2_market_based_kg = total_grey * VIETNAM_GRID_EMISSION_FACTOR

    # Lượng phát thải giảm được (Avoided CO2)
    emissions_avoided_kg = total_matched * VIETNAM_GRID_EMISSION_FACTOR
    emissions_avoided_tons = emissions_avoided_kg / 1000.0

    # Tính toán tài chính CBAM
    # Thuế/chi phí carbon CBAM dự kiến tiết kiệm được
    cbam_savings_eur = emissions_avoided_tons * CBAM_BENCHMARK_PRICE_EUR_PER_TON
    cbam_savings_vnd = cbam_savings_eur * EUR_TO_VND

    # Chi phí mua chứng chỉ REC từ các hộ dân
    rec_cost_vnd = (total_matched / 1000.0) * REC_PRICE_PER_MWH_VND

    # Lợi ích kinh tế ròng (Net Benefit)
    net_savings_vnd = cbam_savings_vnd - rec_cost_vnd

    return {
        "matching_df": matching_df,
        "summary": {
            "total_demand_kwh": round(total_demand, 2),
            "total_verified_supply_kwh": round(total_supply, 2),
            "total_matched_kwh": round(total_matched, 2),
            "total_grey_grid_kwh": round(total_grey, 2),
            "total_excess_solar_kwh": round(total_excess, 2),
            "cfe_score_pct": overall_cfe_score,
            "scope2_location_based_tco2": round(scope2_location_based_kg / 1000.0, 3),
            "scope2_market_based_tco2": round(scope2_market_based_kg / 1000.0, 3),
            "avoided_tco2": round(emissions_avoided_tons, 3),
            "cbam_savings_vnd": round(cbam_savings_vnd, 0),
            "rec_cost_vnd": round(rec_cost_vnd, 0),
            "net_benefit_vnd": round(net_savings_vnd, 0)
        }
    }
