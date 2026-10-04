"""RECxchange - Nền tảng Tổng hợp và Minh bạch hóa Chứng chỉ Năng lượng Tái tạo
Cuộc thi Sáng tạo trẻ 2026 - Đội thi: Green Farmer
Phụ trách Kỹ thuật & Data Science: Nguyễn Quang Tùng (ĐH Bách Khoa ĐHQG-HCM)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from src.simulator import simulate_prosumers, DEFAULT_PROSUMERS
from src.verification import verify_readings, get_verification_summary
from src.ledger import CertificateLedger
from src.matching import (
    SME_PRESETS,
    generate_sme_demand_profile,
    run_hourly_matching
)
from src.config import (
    VIETNAM_GRID_EMISSION_FACTOR,
    CBAM_BENCHMARK_PRICE_EUR_PER_TON,
    STATUS_VERIFIED,
    STATUS_FLAGGED
)

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="RECxchange - Nền tảng Năng lượng Tái tạo & Scope 2 SME",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại, chuyên nghiệp
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-verified {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
        padding: 4px 9px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    .badge-flagged {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        white-space: normal;
        word-break: break-word;
        box-shadow: 0 1px 2px rgba(220, 38, 38, 0.08);
    }
    .hero-banner {
        background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.2);
    }
    
    /* Radar table styling */
    .radar-table-container {
        border: 1px solid #fee2e2;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 8px -2px rgba(220, 38, 38, 0.06);
        margin-top: 14px;
        margin-bottom: 24px;
        background: #ffffff;
    }
    .radar-table-header {
        background: #fef2f2;
        padding: 12px 18px;
        border-bottom: 1px solid #fee2e2;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .radar-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-size: 13.5px;
    }
    .radar-table th {
        background: #f8fafc;
        padding: 12px 14px;
        font-weight: 600;
        color: #475569;
        border-bottom: 1px solid #e2e8f0;
        white-space: nowrap;
    }
    .radar-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #f1f5f9;
        color: #1e293b;
        vertical-align: middle;
    }
    .radar-table tr:hover {
        background: #fff8f8;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo dữ liệu trong session state
if "raw_telemetry" not in st.session_state:
    raw_df = simulate_prosumers()
    verified_df = verify_readings(raw_df)
    st.session_state["raw_telemetry"] = raw_df
    st.session_state["verified_telemetry"] = verified_df
    
    # Khởi tạo sổ cái
    ledger = CertificateLedger()
    ledger.mint_from_verified_data(verified_df)
    st.session_state["ledger"] = ledger

# SIDEBAR: Cấu hình và giả lập
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
        <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); width: 46px; height: 46px; min-width: 46px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="4"/>
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
            </svg>
        </div>
        <div>
            <div style="font-size: 21px; font-weight: 800; color: #0f172a; line-height: 1.15; letter-spacing: -0.5px;">RECxchange</div>
            <div style="font-size: 11px; font-weight: 600; color: #059669; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px;">EnergyTag · 24/7 CFE</div>
        </div>
    </div>
    <div style="font-size: 12.5px; color: #64748b; line-height: 1.4; margin-bottom: 14px;">
        Nền tảng tổng hợp & minh bạch hoá Chứng chỉ Năng lượng Tái tạo theo giờ
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("⚙️ Thiết lập Mô phỏng")
    sim_seed = st.number_input("Hạt giống mô phỏng (Random Seed)", min_value=1, max_value=999, value=42)
    
    if st.button("🔄 Tái tạo luồng dữ liệu IoT", use_container_width=True, type="primary"):
        new_raw = simulate_prosumers(seed=int(sim_seed))
        new_verified = verify_readings(new_raw)
        new_ledger = CertificateLedger()
        new_ledger.mint_from_verified_data(new_verified)
        
        st.session_state["raw_telemetry"] = new_raw
        st.session_state["verified_telemetry"] = new_verified
        st.session_state["ledger"] = new_ledger
        st.success("Đã cập nhật dữ liệu viễn thông từ các công tơ IoT!")

    st.markdown("---")
    st.markdown("""
    **Đội thi:** Green Farmer  
    **Cuộc thi:** Sáng tạo trẻ 2026  
    **Chuẩn kỹ thuật:**
    - EnergyTag Hourly Matching
    - GHG Protocol Scope 2 Guidance
    - EVN Grid Factor: `0.7212 tCO2/MWh`
    """)

# HEADER HERO
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: white;">RECxchange · Trung tâm Xác minh & Khớp lệnh REC</h1>
            <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 15px;">
                Nền tảng đo lường IoT tận gốc, minh bạch hóa theo giờ chuẩn EnergyTag cho nguồn phát nhỏ và doanh nghiệp SME xuất khẩu
            </p>
        </div>
        <div style="text-align: right; background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px;">
            <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Sẵn sàng tuân thủ CBAM</div>
            <div style="font-size: 18px; font-weight: 700;">2026 Ready 🇪🇺</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# TABS CHÍNH
tab_prosumers, tab_ledger, tab_sme_portal = st.tabs([
    "☀️ Mạng Lưới Nguồn Phát & Giám Sát IoT",
    "📜 Sổ Cái Chứng Chỉ Số (EnergyTag Ledger)",
    "🏭 Cổng Doanh Nghiệp SME & Tuân Thủ Scope 2"
])

verified_df = st.session_state["verified_telemetry"]
v_summary = get_verification_summary(verified_df)
ledger: CertificateLedger = st.session_state["ledger"]

# ==========================================
# TAB 1: MẠNG LƯỚI NGUỒN PHÁT & GIÁM SÁT IOT
# ==========================================
with tab_prosumers:
    st.subheader("📊 Giám sát Luồng Dữ liệu Công tơ Thông minh (IoT Telemetry)")
    
    # Hàng chỉ số KPI
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tổng nguồn phát tích hợp</div>
            <div class="metric-val">{len(DEFAULT_PROSUMERS)} <span style="font-size: 15px; font-weight: normal; color: #64748b;">trạm</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tổng sản lượng khai báo</div>
            <div class="metric-val">{v_summary['total_kwh_claimed']} <span style="font-size: 15px; font-weight: normal; color: #64748b;">kWh</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sản lượng Hợp lệ (Verified)</div>
            <div class="metric-val" style="color: #059669;">{v_summary['verified_kwh']} <span style="font-size: 15px; font-weight: normal; color: #64748b;">kWh ({v_summary['verification_rate_pct']}%)</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sản lượng Bất thường bị Chặn</div>
            <div class="metric-val" style="color: #dc2626;">{v_summary['fraud_kwh']} <span style="font-size: 15px; font-weight: normal; color: #64748b;">kWh ({v_summary['fraud_energy_pct']}%)</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Biểu đồ công suất theo thời gian
    st.markdown("#### 📈 Đường cong Công suất 24h & Phát hiện Bất thường")
    
    selected_p = st.selectbox(
        "Chọn nguồn phát để phân tích chi tiết:",
        options=["Tất cả nguồn phát"] + [f"{p['id']} - {p['name']} ({p['capacity_kwp']} kWp)" for p in DEFAULT_PROSUMERS]
    )

    if selected_p == "Tất cả nguồn phát":
        plot_df = verified_df
    else:
        p_id_selected = selected_p.split(" - ")[0]
        plot_df = verified_df[verified_df["prosumer_id"] == p_id_selected]

    fig_power = px.line(
        plot_df,
        x="hour",
        y="active_power_kw",
        color="prosumer_name",
        markers=True,
        labels={"hour": "Khung giờ trong ngày (0h - 23h)", "active_power_kw": "Công suất (kW)", "prosumer_name": "Nguồn phát"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_power.update_layout(
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            title_text=""
        ),
        xaxis=dict(
            title=dict(text="Khung giờ trong ngày (0h - 23h)", standoff=15, font=dict(size=12, color="#475569")),
            tickmode="linear",
            tick0=0,
            dtick=2,
            ticksuffix=":00",
            gridcolor="#f1f5f9",
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text="Công suất phát thực tế (kW)", font=dict(size=12, color="#475569")),
            gridcolor="#f1f5f9",
            zeroline=False
        ),
        margin=dict(l=50, r=20, t=65, b=65),
        height=450
    )
    st.plotly_chart(fig_power, use_container_width=True)

    # Bảng cảnh báo gian lận (Anti-Fraud Radar)
    flagged_df = verified_df[verified_df["verification_status"] == STATUS_FLAGGED]
    st.markdown("#### 🚨 Radar Chống Gian lận (Các bản ghi vi phạm quy tắc vật lý)")
    
    if len(flagged_df) > 0:
        rows_html = []
        for _, row in flagged_df.iterrows():
            reasons = [r.strip() for r in str(row["anomaly_reasons"]).split(";") if r.strip()]
            badges_html = "".join([
                f'<span class="badge-flagged" style="margin: 2px 4px 2px 0;">⚠️ {reason}</span>'
                for reason in reasons
            ])
            
            hour_str = f"{int(row['hour']):02d}:00"
            cap_str = f"{float(row['capacity_kwp']):.1f} kWp"
            irr_str = f"{float(row['irradiance_wm2']):.1f} W/m²"
            pwr_str = f"<b style='color: #dc2626;'>{float(row['active_power_kw']):.2f} kW</b>"
            
            rows_html.append(
                f"<tr>"
                f"<td style='font-weight: 600; color: #475569;'>{hour_str}</td>"
                f"<td><code style='background: #f1f5f9; color: #0f172a; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 12px;'>{row['prosumer_id']}</code></td>"
                f"<td style='font-weight: 500;'>{row['prosumer_name']}</td>"
                f"<td>{cap_str}</td>"
                f"<td>{irr_str}</td>"
                f"<td>{pwr_str}</td>"
                f"<td style='min-width: 320px; line-height: 1.6;'>{badges_html}</td>"
                f"</tr>"
            )
            
        all_rows = "".join(rows_html)
        radar_table_html = (
            f'<div class="radar-table-container">'
            f'<div class="radar-table-header">'
            f'<span style="font-weight: 700; color: #991b1b; font-size: 14px;">'
            f'🚨 DANH SÁCH BẢN GHI BẤT THƯỜNG / GIAN LẬN ({len(flagged_df)} bản ghi phát hiện)'
            f'</span>'
            f'<span style="font-size: 12px; color: #dc2626; font-weight: 600; background: #fff; padding: 3px 10px; border-radius: 20px; border: 1px solid #fecaca;">'
            f'Tự động cách ly khỏi Sổ cái'
            f'</span>'
            f'</div>'
            f'<div style="overflow-x: auto;">'
            f'<table class="radar-table">'
            f'<thead>'
            f'<tr>'
            f'<th>Khung giờ</th>'
            f'<th>Mã Trạm</th>'
            f'<th>Tên Hộ/Xưởng</th>'
            f'<th>Công suất Đỉnh</th>'
            f'<th>Bức xạ Đo lường</th>'
            f'<th>Công suất Báo về</th>'
            f'<th style="min-width: 320px;">Mã Lỗi Phát Hiện & Lý Do Vi Phạm</th>'
            f'</tr>'
            f'</thead>'
            f'<tbody>{all_rows}</tbody>'
            f'</table>'
            f'</div>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.html(radar_table_html)
        else:
            st.markdown(radar_table_html, unsafe_allow_html=True)
        
        # Chú thích ý nghĩa mã lỗi giúp người dùng hiểu nhanh
        st.caption("ℹ️ **Giải thích mã kiểm định:** `ERR_NIGHT_GEN`: Khai khống sản lượng ban đêm · `ERR_OVER_CAPACITY`: Vượt >115% công suất inverter · `ERR_PHYS_MISMATCH`: Sai lệch bức xạ & công suất · `ERR_FROZEN_DATA`: Treo cảm biến đo")
    else:
        st.success("Tất cả dữ liệu viễn thông đều trong giới hạn an toàn vật lý!")

# ==========================================
# TAB 2: SỔ CÁI CHỨNG CHỈ SỐ (ENERGYTAG)
# ==========================================
with tab_ledger:
    st.subheader("📜 Sổ Cái Lưu Ký Chứng Chỉ Năng Lượng Tái Tạo Theo Giờ (Granular Certificates)")
    
    is_valid_ledger = ledger.verify_ledger_integrity()
    if is_valid_ledger:
        st.success("🛡️ **Toàn vẹn Sổ cái (Ledger Integrity):** ĐẠT CHUẨN. Chuỗi băm SHA-256 không bị can thiệp hay sửa đổi.")
    else:
        st.error("⚠️ **Cảnh báo:** Phát hiện bất thường trong chuỗi mã băm của sổ cái!")

    ledger_df = ledger.to_dataframe()
    
    if not ledger_df.empty:
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            st.metric("Tổng số chứng chỉ theo giờ đã cấp", f"{len(ledger_df)} GC")
        with col_l2:
            st.metric("Tổng năng lượng được số hóa", f"{ledger_df['energy_kwh'].sum():.2f} kWh")
        with col_l3:
            st.metric("Tiêu chuẩn áp dụng", "EnergyTag / 1-Hour Granularity")

        st.markdown("#### Tra cứu Danh mục Chứng chỉ Số")
        
        # Lọc chứng chỉ
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_hour_filter = st.slider("Lọc theo khung giờ phát:", min_value=0, max_value=23, value=(6, 18))
        with filter_col2:
            selected_owner = st.selectbox("Lọc theo nguồn phát:", ["Tất cả"] + list(ledger_df["prosumer_name"].unique()))

        filtered_ledger = ledger_df[
            (ledger_df["hour"] >= selected_hour_filter[0]) & 
            (ledger_df["hour"] <= selected_hour_filter[1])
        ]
        if selected_owner != "Tất cả":
            filtered_ledger = filtered_ledger[filtered_ledger["prosumer_name"] == selected_owner]

        # Hiển thị bảng chứng chỉ
        show_table = filtered_ledger[[
            "cert_id", "hour", "prosumer_name", "energy_kwh", 
            "fuel_type", "status", "hash", "prev_hash"
        ]].copy()
        show_table["hash_short"] = show_table["hash"].apply(lambda h: h[:10] + "..." + h[-8:])
        show_table["prev_hash_short"] = show_table["prev_hash"].apply(lambda h: h[:10] + "..." + h[-8:])
        show_table.drop(columns=["hash", "prev_hash"], inplace=True)
        show_table.columns = ["Mã Chứng Chỉ (GC-ID)", "Giờ", "Nguồn Phát", "Sản Lượng (kWh)", "Loại Nguồn", "Trạng Thái", "Mã Băm Block (SHA-256)", "Mã Băm Khối Trước"]

        st.dataframe(
            show_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mã Chứng Chỉ (GC-ID)": st.column_config.TextColumn("Mã Chứng Chỉ (GC-ID)", width="medium"),
                "Giờ": st.column_config.NumberColumn("Khung giờ", format="%02d:00", width="small"),
                "Nguồn Phát": st.column_config.TextColumn("Nguồn Phát", width="medium"),
                "Sản Lượng (kWh)": st.column_config.NumberColumn("Sản Lượng", format="%.3f kWh", width="small"),
                "Loại Nguồn": st.column_config.TextColumn("Loại Nguồn", width="small"),
                "Trạng Thái": st.column_config.TextColumn("Trạng Thái", width="small"),
                "Mã Băm Block (SHA-256)": st.column_config.TextColumn("Mã Băm Block", width="medium"),
                "Mã Băm Khối Trước": st.column_config.TextColumn("Mã Băm Khối Trước", width="medium")
            }
        )
    else:
        st.info("Chưa có chứng chỉ nào được phát hành do không có dữ liệu hợp lệ.")

# ==========================================
# TAB 3: CỔNG DOANH NGHIỆP SME & SCOPE 2
# ==========================================
with tab_sme_portal:
    st.subheader("🏭 Cổng Doanh Nghiệp Mua (SME) - Báo Cáo Tuân Thủ Scope 2 & CBAM")
    st.caption("Khớp lệnh cung - cầu năng lượng sạch theo chuẩn 24/7 CFE của GHG Protocol & EnergyTag")

    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("#### 1. Chọn Hồ Sơ Nhà Máy Xuất Khẩu")
        sme_choice = st.selectbox("Ngành hàng / Doanh nghiệp:", list(SME_PRESETS.keys()))
        sme_scale = st.slider("Quy mô công suất tiêu thụ (%):", min_value=50, max_value=200, value=100, step=10) / 100.0
        
        demand_df = generate_sme_demand_profile(sme_choice, scale_factor=sme_scale)
        match_result = run_hourly_matching(verified_df, demand_df)
        match_df = match_result["matching_df"]
        summary = match_result["summary"]

        st.markdown("---")
        st.markdown("#### 2. Kết quả Đối Soát Năng Lượng Sạch")
        st.metric("Tỷ lệ Năng lượng Sạch Đáp ứng (24/7 CFE Score)", f"{summary['cfe_score_pct']}%")
        st.metric("Điện Xanh Khớp lệnh", f"{summary['total_matched_kwh']} kWh / ngày")
        st.metric("Điện Lưới Xám Còn Lại", f"{summary['total_grey_grid_kwh']} kWh / ngày")

    with col_s2:
        st.markdown("#### 📊 Biểu Đồ Khớp Năng Lượng Tái Tạo Theo Từng Giờ (Hourly Matching)")
        
        # Biểu đồ Area/Bar chart khớp lệnh
        fig_match = go.Figure()
        
        # Nhu cầu nhà máy
        fig_match.add_trace(go.Scatter(
            x=match_df["hour"],
            y=match_df["sme_demand_kwh"],
            mode="lines+markers",
            name="Nhu cầu Nhà máy (Demand)",
            line=dict(color="#2563eb", width=3, dash="dash")
        ))

        # Năng lượng sạch tự khớp
        fig_match.add_trace(go.Bar(
            x=match_df["hour"],
            y=match_df["matched_kwh"],
            name="REC Nguồn phát Nhỏ Khớp lệnh (Matched Green)",
            marker_color="#10b981"
        ))

        # Điện lưới xám chưa được bù trừ
        fig_match.add_trace(go.Bar(
            x=match_df["hour"],
            y=match_df["grid_grey_kwh"],
            name="Điện lưới Than/Khí (Residual Grey Grid)",
            marker_color="#94a3b8"
        ))

        fig_match.update_layout(
            barmode="stack",
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
                title_text=""
            ),
            xaxis=dict(
                title=dict(text="Khung giờ trong ngày (0h - 23h)", standoff=15, font=dict(size=12, color="#475569")),
                tickmode="linear",
                tick0=0,
                dtick=2,
                ticksuffix=":00",
                gridcolor="#f1f5f9",
                zeroline=False
            ),
            yaxis=dict(
                title=dict(text="Sản lượng điện (kWh)", font=dict(size=12, color="#475569")),
                gridcolor="#f1f5f9",
                zeroline=False
            ),
            hovermode="x unified",
            margin=dict(l=50, r=20, t=55, b=65),
            height=450
        )
        st.plotly_chart(fig_match, use_container_width=True)

    st.markdown("---")
    st.subheader("🌍 Báo Cáo Phát Thải Scope 2 Sẵn Sàng Kiểm Toán (Audit-Ready ESG Report)")
    
    col_esg1, col_esg2, col_esg3 = st.columns(3)
    with col_esg1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Phát thải Location-based</div>
            <div class="metric-val">{summary['scope2_location_based_tco2']} <span style="font-size: 15px; font-weight: normal; color: #64748b;">tấn CO2e/ngày</span></div>
            <div style="font-size: 12px; color: #64748b; margin-top: 6px;">Tính theo hệ số lưới điện VN ({VIETNAM_GRID_EMISSION_FACTOR})</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_esg2:
        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid #10b981;">
            <div class="metric-label">Phát thải Market-based (Sau khi mua REC)</div>
            <div class="metric-val" style="color: #059669;">{summary['scope2_market_based_tco2']} <span style="font-size: 15px; font-weight: normal; color: #64748b;">tấn CO2e/ngày</span></div>
            <div style="font-size: 12px; color: #059669; margin-top: 6px;">Giảm {(summary['scope2_location_based_tco2'] - summary['scope2_market_based_tco2']):.3f} tấn CO2e nhờ RECxchange</div>
        </div>
        """, unsafe_allow_html=True)

    with col_esg3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Lợi ích Kinh Tế Ròng (Net Benefit)</div>
            <div class="metric-val" style="color: #2563eb;">+{summary['net_benefit_vnd']:,} <span style="font-size: 15px; font-weight: normal; color: #64748b;">VNĐ/ngày</span></div>
            <div style="font-size: 12px; color: #64748b; margin-top: 6px;">Tiết kiệm chi phí CBAM sau khi trừ phí REC</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 📥 Xuất Hồ Sơ Minh Chứng Kiểm Toán")
    csv_data = match_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Tải Báo Cáo Đối Soát Chi Tiết Scope 2 (CSV/Excel)",
        data=csv_data,
        file_name=f"RECxchange_Scope2_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
