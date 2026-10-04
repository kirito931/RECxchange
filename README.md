# RECxchange Prototype (MVP Vòng Triển Khai)

**Cuộc thi:** Sáng tạo trẻ 2026  
**Đội thi:** Green Farmer  
**Lĩnh vực:** (2) Công nghệ Môi trường & Năng lượng tái tạo  
**Phụ trách Kỹ thuật & Data Science:** Nguyễn Quang Tùng (Khoa học Dữ liệu – ĐH Bách Khoa, ĐHQG-HCM)

---

## 🌟 Giới thiệu Dự án
**RECxchange** là nền tảng đo lường, xác minh và minh bạch hóa Chứng chỉ Năng lượng Tái tạo (REC) tận gốc cho các nguồn phát quy mô nhỏ (điện mặt trời áp mái hộ gia đình, nhà xưởng) và kết nối với các doanh nghiệp vừa và nhỏ (SME) xuất khẩu đang chịu áp lực tuân thủ **Cơ chế Điều chỉnh Biên giới Carbon của EU (CBAM)** và **báo cáo giảm phát thải Scope 2**.

Dự án áp dụng chuẩn đối soát theo giờ (**Hourly Matching / Granular Certificates** theo chuẩn **EnergyTag** và bản cập nhật Scope 2 của **GHG Protocol**).

---

## 🏗️ Kiến trúc Hệ thống

```
                         [ Luồng Xử Lý RECxchange ]
                         
  [1. Thiết bị Đo lường IoT / Simulator]
          │
          ▼ (Dữ liệu chuỗi thời gian: Giờ, Bức xạ, Công suất, Nhiệt độ)
  [2. Engine Xác minh & Chống Gian lận (Data Verification)]
          │  ├── Kiểm tra quy tắc vật lý mặt trời (Physics bounds)
          │  ├── Phát hiện gian lận ban đêm (Night fraud detection)
          │  └── Lọc sai số, đóng băng cảm biến (Replay attack detection)
          │
          ├──> [Bản ghi Bất thường (Flagged Anomaly)] ──> Báo động & Loại bỏ
          │
          ▼ [Bản ghi Hợp lệ (Verified Green Energy)]
  [3. Sổ Cái Lưu Ký Số Hóa (EnergyTag Granular Ledger)]
          │  └── Đóng gói chứng chỉ theo từng giờ + Khóa băm SHA-256
          │
          ▼
  [4. Engine Khớp Lệnh Năng Lượng Theo Giờ (Hourly Matching Engine)]
          │  ├── Khớp với hồ sơ phụ tải tiêu thụ thực tế của nhà máy SME
          │  ├── Tính chỉ số 24/7 CFE Score (% bao phủ điện sạch)
          │  └── Tính toán giảm phát thải Scope 2 (Location-based vs Market-based)
          │
          ▼
  [5. Dashboard Điều Khiển Trực Quan (Streamlit Web App)]
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Kích hoạt môi trường và chạy ứng dụng:
Trên máy tính cá nhân (Windows PowerShell):
```powershell
# Di chuyển vào thư mục dự án
cd d:\RECxchange

# Khởi chạy ứng dụng Web Dashboard
.venv\Scripts\streamlit run app.py
```
Ứng dụng sẽ tự động mở trình duyệt tại địa chỉ `http://localhost:8501`.

### 2. Chạy kiểm thử tự động (Unit Tests):
```powershell
.venv\Scripts\python -m unittest discover -s tests
```

---

## 🎯 3 Tính Năng Trọng Tâm Trình Diễn Cho Ban Giám Khảo

1. **Tab 1: Mạng Lưới Nguồn Phát & Giám Sát IoT:**
   - Xem biểu đồ công suất 24h của 6 trạm áp mái tại TP.HCM & Bình Dương.
   - Radar chống gian lận phát hiện chính xác: hộ khai khống sản lượng ban đêm, hộ vượt 180% công suất biến tần, cảm biến bị treo.
2. **Tab 2: Sổ Cái Chứng Chỉ Số (EnergyTag):**
   - Từng kWh được đúc thành **Granular Certificate** theo từng giờ (1-hour granularity).
   - Kiểm tra chuỗi băm bảo vệ dữ liệu (SHA-256 Hash Chain Integrity: ĐẠT CHUẨN).
3. **Tab 3: Cổng SME Khách Hàng & Báo Cáo Scope 2:**
   - Lựa chọn ngành hàng xuất khẩu (Dệt may, Gỗ, Da giày).
   - Biểu đồ khớp lệnh giờ-theo-giờ (EnergyTag Hourly Matching curve).
   - Báo cáo tài chính: Tiết kiệm chi phí thuế carbon CBAM so với chi phí mua REC.
   - Nút xuất file CSV báo cáo kiểm toán sẵn sàng nộp cho đối tác châu Âu.
