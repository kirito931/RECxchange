# BẢN THUYẾT MINH KỸ THUẬT & KIẾN TRÚC HỆ THỐNG RECxchange
> **Người viết:** Tùng (Phụ trách Kỹ thuật & Data Science) gửi các thành viên đội Green Farmer  
> **Mục tiêu:** Tùng diễn giải chi tiết kiến trúc kỹ thuật của nền tảng thành ngôn ngữ kinh doanh, logic kinh tế và bằng chứng kiểm toán để cả team cùng hiểu sâu giải pháp, tự tin xây dựng Pitch Deck và thuyết trình trước Hội đồng Giám khảo cuộc thi Sáng tạo trẻ 2026.

---

## PHẦN 1: TỔNG QUAN BÀI TOÁN & GIẢI PHÁP CỐT LÕI

### 1. Nỗi đau thị trường dưới góc nhìn Kỹ thuật & Kinh tế
* **Áp lực từ Cơ chế CBAM (EU) và GHG Protocol Scope 2:**  
  Từ năm 2026, các doanh nghiệp SME Việt Nam xuất khẩu sang thị trường Châu Âu (Dệt may, Da giày, Gỗ, Thép...) bắt buộc phải kê khai lượng phát thải gián tiếp từ điện tiêu thụ (Scope 2). Nếu không có minh chứng sử dụng điện sạch hợp lệ, doanh nghiệp sẽ bị áp **hệ số phát thải mặc định (Default Grid Factor) rất cao của Việt Nam (`0.7212 kg CO2/kWh`)** và bị đánh thuế carbon với mức giá tham chiếu của sàn EU ETS (~**80 EUR/tấn CO2**).
* **Bế tắc của thị trường REC truyền thống (I-REC cũ):**
  - **Chỉ bán theo lô lớn (Bulk Volume):** Các sàn I-REC chỉ phục vụ nhà máy điện mặt trời/điện gió tập trung hàng chục MW; giao dịch theo lô hàng nghìn MWh. Doanh nghiệp SME nhỏ lẻ không đủ tiền mua.
  - **Thống kê theo năm/tháng (Yearly Matching) bị xem là "Tẩy xanh" (Greenwashing):** Doanh nghiệp dùng điện ban đêm nhưng lại mua REC của nhà máy điện mặt trời phát ban ngày để bù trừ bình quân năm. Chuẩn quốc tế mới (**GHG Protocol Scope 2 Revision 2025–2026** và **EnergyTag**) yêu cầu phải đối soát **theo từng giờ (Hourly Matching / 24/7 CFE)**: Tiêu thụ giờ nào phải bù đắp bằng điện sạch sản xuất đúng giờ đó.
  - **Hộ nhỏ lẻ bị bỏ rơi:** Hàng chục nghìn hộ áp mái và nhà xưởng nhỏ không thể tự đăng ký bán chứng chỉ vì chi phí kiểm toán ban đầu vượt quá giá trị năng lượng sinh ra.

### 2. Định vị của RECxchange
RECxchange là nền tảng **tổng hợp (Aggregator)**, **xác minh dữ liệu tận gốc qua IoT (Verification Engine)**, **đúc chứng chỉ số theo giờ (EnergyTag Granular Ledger)** và **khớp lệnh đối soát phụ tải cho nhà máy SME (Hourly Matching Engine)**.

---

## PHẦN 2: KIẾN TRÚC KỸ THUẬT 4 TẦNG (GIẢI THÍCH DỄ HIỂU)

Kiến trúc RECxchange vận hành khép kín theo luồng:

```
[TẦNG 1: CÔNG TƠ IOT] ──(Dữ liệu thô)──> [TẦNG 2: ENGINE CHỐNG GIAN LẬN]
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼ (Bất thường: Bức xạ = 0, Vượt công suất)                     ▼ (Hợp lệ 100%)
             [CÁCH LY KHỎI HỆ THỐNG]                                     [TẦNG 3: SỔ CÁI BĂM SHA-256]
             (Ghi nhật ký Radar Radar)                                   (Đúc Granular Certificate theo giờ)
                                                                                      │
                                                                                      ▼
                                                                         [TẦNG 4: KHỚP LỆNH PHỤ TẢI SME]
                                                                         (Tính CFE Score & Tiết kiệm CBAM)
```

---

### TẦNG 1: THU THẬP & MÔ PHỎNG DỮ LIỆU IOT
* **Chức năng:** Mô phỏng luồng dữ liệu thời gian thực gửi từ các thiết bị đo (Smart Meter / IoT Gateway) lắp tại 6 trạm prosumer mẫu tại TP.HCM và Bình Dương (quy mô 5 kWp – 60 kWp).
* **Mỗi bản ghi IoT gửi về trong 1 giờ gồm 4 thông số cốt lõi:**
  1. `timestamp` & `hour`: Khung giờ đo lường (0h – 23h).
  2. `active_power_kw` & `energy_kwh`: Công suất và sản lượng điện thực tế phát ra lưới.
  3. `irradiance_wm2`: Bức xạ mặt trời đo tại khu vực (W/m²). Đây là căn cứ đối chiếu quan trọng nhất!
  4. `inverter_temp_c`: Nhiệt độ hoạt động của bộ biến tần (Inverter).
* **Kịch bản cài cắm kiểm thử thuật toán:**
  - *Hộ Bình Chánh:* Cố tình báo phát điện lúc 22h, 23h và 1h sáng (`NIGHT_FRAUD`).
  - *Hộ Hóc Môn:* Báo công suất vượt 185% công suất thiết kế lúc 12h–13h trưa (`OVERCAPACITY`).
  - *Xưởng Mộc Thủ Đức:* Cảm biến bị treo cứng ở một giá trị công suất suốt 4 tiếng buổi chiều (`FROZEN_DATA`).

---

### TẦNG 2: ENGINE XÁC MINH & CHỐNG GIAN LẬN
* **Ý nghĩa đối với kinh tế:** Đây là "bức tường bảo vệ" uy tín của nền tảng. Nhờ thuật toán này, chứng chỉ RECxchange phát hành có thể **vượt qua các đợt kiểm toán khắt khe của đối tác EU**, ngăn chặn triệt để hành vi cấp khống REC để trục lợi.
* **4 quy tắc vật lý & thống kê tự động:**
  1. **Quy tắc Ban đêm (Night Check):** Nếu bức xạ mặt trời $< 20\text{ W/m}^2$ mà công suất báo về $> 0.05\text{ kW}$ $\to$ Đánh dấu lỗi `ERR_NIGHT_GEN` (gian lận đấu nối máy phát diesel hoặc hack phần mềm công tơ).
  2. **Quy tắc Giới hạn Biến tần (Inverter Tolerance Check):** Công suất phát tức thời không thể vượt quá $115\%$ công suất danh định của Inverter ($\text{Capacity} \times 1.15$). Nếu vượt $\to$ Đánh dấu `ERR_OVER_CAPACITY`.
  3. **Quy tắc Tương quan Bức xạ - Công suất (Physical Mismatch):** Nếu bức xạ yếu ($< 150\text{ W/m}^2$) do mây mù hoặc chiều muộn nhưng lại báo công suất $> 50\%$ công suất đỉnh $\to$ Đánh dấu `ERR_PHYS_MISMATCH`.
  4. **Quy tắc Kiểm tra Treo Cảm biến (Frozen Data / Replay Attack):** Trong khung giờ nắng (9h–16h), bức xạ mặt trời luôn biến thiên liên tục. Nếu công suất giữ nguyên không đổi suốt 3–4 giờ liên tiếp $\to$ Đánh dấu `ERR_FROZEN_DATA` (cảm biến treo hoặc hacker phát lại gói tin cũ).
* **Xử lý:** Toàn bộ bản ghi vi phạm bị dán nhãn `FLAGGED_ANOMALY` và **bị loại bỏ ngay lập tức**, không bao giờ được đưa vào Sổ cái phát hành chứng chỉ.

---

### TẦNG 3: SỔ CÁI LƯU KÝ SỐ HÓA THEO GIỜ
* **Chuẩn áp dụng:** **EnergyTag Standard** (Granular Certificates - GC).
* **Cấu trúc của 1 Chứng chỉ số (1-Hour GC):**
  - `cert_id`: Mã định danh duy nhất (VD: `GC-VN-20260928-1100-REC-HCM-001`).
  - `hour`: Khung giờ phát điện cụ thể.
  - `energy_kwh`: Lượng điện sạch đã xác minh (kWh).
  - `grid_zone`: Khu vực lưới điện (Miền Nam Việt Nam).
  - `fuel_type`: Nguồn gốc (Điện mặt trời áp mái - `SOLAR_ROOFTOP`).
* **Cơ chế chống sửa đổi (Tamper-evident SHA-256 Hash Chain):**
  - Mỗi chứng chỉ mang một mã băm mật mã học `hash` tính từ nội dung của nó kết hợp với `prev_hash` của chứng chỉ đứng trước.
  - **Logic sổ cái:** Nếu bất kỳ ai can thiệp sửa đổi dù chỉ 0.001 kWh trong quá khứ, toàn bộ chuỗi mã băm phía sau sẽ lập tức bị đứt gãy.
  - Hàm kiểm toán tính toàn vẹn sổ cái cho phép kiểm toán viên độc lập chạy kiểm tra tự động chỉ trong vài mili-giây với kết quả **ĐẠT CHUẨN**.

---

### TẦNG 4: ENGINE KHỚP LỆNH & TÍNH TOÁN CBAM / SCOPE 2
* **Ý nghĩa đối với khách hàng SME:** Đây là nơi tạo ra **giá trị tài chính trực tiếp** cho khách hàng mua chứng chỉ.
* **Cơ chế khớp lệnh giờ-theo-giờ (Hourly Matching):**
  - Tại từng khung giờ $h$ từ 0h đến 23h:
    $$\text{Matched Green (kWh)} = \min(\text{Nhu cầu Nhà máy}_h, \text{Sản lượng Xanh Hợp lệ}_h)$$
    $$\text{Điện Lưới Xám (kWh)} = \text{Nhu cầu Nhà máy}_h - \text{Matched Green}_h$$
* **Chỉ số 24/7 CFE Score (% Năng lượng sạch đáp ứng):**
  $$\text{CFE Score} = \frac{\sum \text{Matched Green}}{\sum \text{Tổng Nhu Cầu Tiêu Thụ}} \times 100\%$$
* **Hai phương pháp tính Scope 2 theo GHG Protocol:**
  1. **Location-based (Phát thải theo vị trí lưới điện):**
     $$\text{Scope 2}_{\text{Location}} = \text{Tổng điện tiêu thụ (kWh)} \times 0.7212\text{ kg CO}_2/\text{kWh}$$
     *(Đây là mức phạt doanh nghiệp phải chịu nếu không mua chứng chỉ xanh)*.
  2. **Market-based (Phát thải theo hợp đồng thị trường sau khi bù trừ REC):**
     $$\text{Scope 2}_{\text{Market}} = \text{Điện lưới xám còn lại (kWh)} \times 0.7212\text{ kg CO}_2/\text{kWh}$$
* **Bài toán Tiết kiệm Kinh tế Ròng (Net Economic Benefit):**
  - Lượng CO2 giảm được: $\Delta \text{CO}_2 = (\text{Scope 2}_{\text{Location}} - \text{Scope 2}_{\text{Market}}) / 1000$ (tấn CO2).
  - Tiết kiệm chi phí thuế CBAM:
    $$\text{Tiết kiệm CBAM (VNĐ)} = \Delta \text{CO}_2 \times 80\text{ EUR/tấn} \times 27.000\text{ VNĐ/EUR}$$
  - Chi phí mua RECxchange:
    $$\text{Phí mua REC (VNĐ)} = \frac{\text{Matched Green}}{1000} \times 50.000\text{ VNĐ/MWh}$$
  - **Lợi ích kinh tế ròng (Net Benefit):**
    $$\text{Net Benefit} = \text{Tiết kiệm CBAM} - \text{Chi phí mua REC}$$
    *(Thực tế hệ thống chứng minh: Doanh nghiệp SME bỏ ra vài chục nghìn VNĐ mua REC nhưng tiết kiệm được hàng triệu VNĐ tiền thuế CBAM mỗi ngày)*.

---

## PHẦN 3: HƯỚNG DẪN DEMO GIAO DIỆN STREAMLIT

Khi trình diễn trước Ban Giám khảo, team mình có thể dẫn dắt bài thuyết trình theo 4 bước:
1. **Sidebar:** Bấm *"Tái tạo luồng dữ liệu IoT"* với các `Random Seed` khác nhau để BGK thấy thuật toán phản ứng tự động theo thời gian thực.
2. **Tab 1 (Mạng lưới nguồn phát & IoT):** Chỉ cho BGK thấy đồ thị công suất 24h và **Radar chống gian lận** bắt được chính xác 7 bản ghi bất thường (bản ghi đêm, vượt công suất, treo cảm biến) với các huy hiệu cảnh báo màu đỏ trực quan.
3. **Tab 2 (Sổ cái EnergyTag):** Nhấn mạnh tính toàn vẹn của chuỗi băm SHA-256 (`Ledger Integrity: ĐẠT CHUẨN`), chứng minh dữ liệu không thể làm giả hồi tố.
4. **Tab 3 (Cổng SME & Báo cáo Scope 2):** Chọn các ngành xuất khẩu (Dệt may, Gỗ, Da giày), kéo thanh công suất tiêu thụ để thấy tỷ lệ CFE Score và số tiền tiết kiệm thuế CBAM ròng nhảy tự động, sau đó bấm nút **"Tải Báo Cáo Đối Soát Chi Tiết Scope 2 (CSV)"** để chứng minh tính sẵn sàng kiểm toán.

---

## PHẦN 4: KẾ HOẠCH HÀNH ĐỘNG TIẾP THEO (ACTION PLAN)

Để đưa dự án từ giai đoạn mô phỏng (TRL 3) lên giai đoạn thử nghiệm phần cứng thực tế (TRL 4) theo đúng cam kết trong Thuyết minh Cuộc thi, Tùng tổng hợp phân công nhiệm vụ kỹ thuật cụ thể giữa **Khoa (IoT / Tự động hóa)** và **Tùng (Data Science)** như sau:

### 1. Nhiệm vụ của Khoa (IoT / Tự động hóa):
* **Giai đoạn 1: Lựa chọn & Khảo sát phần cứng đo lường**
  - Chọn 1 bộ công tơ điện tử đa năng công nghiệp hỗ trợ chuẩn giao tiếp **Modbus-RTU / RS485** (ví dụ: *Schneider EM1200*, *Acrel DTSD1352*, hoặc công tơ Selec/Chint giá rẻ dành cho hộ gia đình).
  - Chọn 1 bộ cảm biến bức xạ mặt trời (Pyranometer) hoặc tấm pin tham chiếu nhỏ để đo thông số $W/m^2$ thực tế.
* **Giai đoạn 2: Xây dựng IoT Gateway**
  - Dùng vi điều khiển **ESP32** hoặc máy tính nhúng **Raspberry Pi Zero / 4** đóng vai trò Gateway kết nối với công tơ qua module RS485-to-TTL.
  - Viết firmware định kỳ (mỗi 1 phút hoặc 5 phút) đọc các thanh ghi Modbus: Điện áp (V), Dòng điện (A), Công suất tác dụng (kW), Bức xạ ($W/m^2$), Tổng sản lượng tích lũy (kWh).
* **Giai đoạn 3: Truyền thông an toàn**
  - Cấu hình Gateway gửi dữ liệu lên máy chủ thông qua giao thức **MQTT (có bảo mật TLS/MQTTS)** hoặc **HTTP POST**.
  - Tích hợp cơ chế **Offline Storage (Lưu đệm thẻ nhớ/Flash):** Nếu mất kết nối Wi-Fi/4G, Gateway phải lưu tạm bản ghi vào bộ nhớ và tự động đồng bộ bù khi có mạng trở lại.

### 2. Nhiệm vụ của Tùng (Data Science):
* **Giai đoạn 1: Xây dựng Broker & API Ingestion Server**
  - Dựng một dịch vụ backend nhỏ (FastAPI hoặc MQTT Subscriber bằng Python) để hứng các gói tin JSON thực tế gửi về từ Gateway của Khoa.
  - Viết cơ chế xác thực thiết bị: Mỗi trạm phát có 1 cặp `Device_ID` và `API_Key` hoặc chữ ký mã hóa HMAC để chống giả mạo nguồn phát.
* **Giai đoạn 2: Nâng cấp Thuật toán Tối ưu hóa Phân bổ (Cost Optimization Module)**
  - Hiện tại thuật toán matching đang khớp lệnh tuần tự. Tùng sẽ bổ sung mô hình tối ưu toán học (**Linear Programming / MILP** bằng thư viện `scipy.optimize` hoặc `PuLP`):
    - *Đầu vào:* 10 nguồn phát nhỏ với giá chào bán khác nhau và vị trí địa lý khác nhau.
    - *Mục tiêu:* Giúp nhà máy SME mua được danh mục REC sao cho **Tối đa hóa chỉ số CFE Score với Tổng chi phí bỏ ra là thấp nhất**.
* **Giai đoạn 3: Hoàn thiện Báo cáo Kiểm toán (Audit Export)**
  - Nâng cấp chức năng xuất báo cáo: Ngoài file CSV, tạo mẫu báo cáo PDF chính thức có logo EnergyTag, bảng tóm tắt phát thải Scope 2 Location-based vs Market-based, và mã QR chứa mã băm chứng chỉ để kiểm toán viên quốc tế quét kiểm tra.

### 3. Giao ước Dữ liệu (Data Contract giữa IoT và Data Science):
Khoa và Tùng thống nhất định dạng JSON truyền tin giữa Gateway (Khoa) và Backend (Tùng) như sau:

```json
{
  "device_id": "REC-HCM-001",
  "gateway_timestamp": "2026-09-28T14:00:00Z",
  "active_power_kw": 4.82,
  "accumulated_energy_kwh": 28.45,
  "irradiance_wm2": 780.5,
  "inverter_temp_c": 42.1,
  "grid_voltage_v": 228.4,
  "firmware_version": "v1.0.4",
  "checksum": "a8f3b2..."
}
```

---

*Tài liệu do Tùng biên soạn đầy đủ để cả team Green Farmer sử dụng làm tài liệu nội bộ, làm phụ lục thuyết minh kỹ thuật và chuyển đổi thành slide thuyết trình cho Vòng Triển Khai.*
