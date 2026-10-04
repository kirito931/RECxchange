"""Automated tests for RECxchange pipeline."""

import unittest
from src.simulator import simulate_prosumers
from src.verification import verify_readings, get_verification_summary
from src.ledger import CertificateLedger
from src.matching import generate_sme_demand_profile, run_hourly_matching

class TestRECxchangePipeline(unittest.TestCase):
    def setUp(self):
        self.raw_df = simulate_prosumers(seed=42)
        self.verified_df = verify_readings(self.raw_df)

    def test_simulation_generates_24_hours(self):
        """Kiểm tra simulator sinh đủ 24 giờ cho tất cả prosumers."""
        self.assertFalse(self.raw_df.empty)
        self.assertEqual(len(self.raw_df), 6 * 24)

    def test_anomaly_detection_catches_fraud(self):
        """Kiểm tra thuật toán phát hiện bất thường bắt được các kịch bản gian lận."""
        flagged = self.verified_df[self.verified_df["verification_status"] == "FLAGGED_ANOMALY"]
        self.assertGreater(len(flagged), 0, "Thuật toán phải phát hiện được các bản ghi gian lận")

    def test_ledger_integrity(self):
        """Kiểm tra chuỗi băm sổ cái không bị đứt gãy."""
        ledger = CertificateLedger()
        ledger.mint_from_verified_data(self.verified_df)
        self.assertTrue(ledger.verify_ledger_integrity(), "Sổ cái chứng chỉ phải đảm bảo toàn vẹn hash chain")

    def test_hourly_matching_and_scope2(self):
        """Kiểm tra thuật toán khớp lệnh Scope 2."""
        demand_df = generate_sme_demand_profile()
        res = run_hourly_matching(self.verified_df, demand_df)
        summary = res["summary"]
        
        self.assertGreater(summary["cfe_score_pct"], 0)
        self.assertLessEqual(summary["cfe_score_pct"], 100)
        self.assertLess(summary["scope2_market_based_tco2"], summary["scope2_location_based_tco2"])

if __name__ == "__main__":
    unittest.main()
