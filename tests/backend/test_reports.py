"""
Tests for reports API endpoints (/api/reports/quarterly, /api/reports/monthly-trends).
"""
import pytest


QUARTERLY_FIELDS = {
    "quarter", "total_orders", "total_revenue",
    "delivered_orders", "avg_order_value", "fulfillment_rate",
}
MONTHLY_FIELDS = {"month", "order_count", "revenue", "delivered_count"}


def _quarter_label(order_date: str) -> str:
    year, month = int(order_date[:4]), int(order_date[5:7])
    return f"Q{(month - 1) // 3 + 1}-{year}"


class TestQuarterlyReportEndpoints:
    """Test suite for the quarterly report endpoint."""

    def test_get_all_quarterly_reports(self, client):
        """Test getting quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for quarter in data:
            assert set(quarter.keys()) == QUARTERLY_FIELDS

    def test_quarterly_reports_sorted(self, client):
        """Test that quarters are returned in chronological order."""
        data = client.get("/api/reports/quarterly").json()
        keys = [(int(q["quarter"][3:]), int(q["quarter"][1])) for q in data]
        assert keys == sorted(keys)

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly totals match the raw orders endpoint."""
        all_orders = client.get("/api/orders").json()
        data = client.get("/api/reports/quarterly").json()

        assert sum(q["total_orders"] for q in data) == len(all_orders)
        expected_revenue = sum(o["total_value"] for o in all_orders)
        assert abs(sum(q["total_revenue"] for q in data) - expected_revenue) < 0.05

        for quarter in data:
            in_quarter = [o for o in all_orders if _quarter_label(o["order_date"]) == quarter["quarter"]]
            delivered = sum(1 for o in in_quarter if o["status"] == "Delivered")
            assert quarter["total_orders"] == len(in_quarter)
            assert quarter["delivered_orders"] == delivered
            assert abs(quarter["fulfillment_rate"] - round(delivered / len(in_quarter) * 100, 1)) < 0.01
            assert abs(quarter["avg_order_value"] - quarter["total_revenue"] / len(in_quarter)) < 0.01

    def test_quarterly_revenue_is_rounded(self, client):
        """Test that revenue is rounded to cents (no float summation noise)."""
        data = client.get("/api/reports/quarterly").json()
        for quarter in data:
            assert quarter["total_revenue"] == round(quarter["total_revenue"], 2)

    def test_get_quarterly_reports_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        tokyo_orders = client.get("/api/orders?warehouse=Tokyo").json()
        data = client.get("/api/reports/quarterly?warehouse=Tokyo").json()
        assert sum(q["total_orders"] for q in data) == len(tokyo_orders)

    def test_get_quarterly_reports_by_quarter(self, client):
        """Test that a quarter filter returns only that quarter."""
        data = client.get("/api/reports/quarterly?month=Q2-2025").json()
        assert [q["quarter"] for q in data] == ["Q2-2025"]

    def test_get_quarterly_reports_multiple_filters(self, client):
        """Test filtering quarterly reports with multiple filters."""
        query = "warehouse=London&category=Sensors&status=Delivered"
        expected = client.get(f"/api/orders?{query}").json()
        data = client.get(f"/api/reports/quarterly?{query}").json()

        assert sum(q["total_orders"] for q in data) == len(expected)
        # Only delivered orders remain, so every quarter is 100% fulfilled
        for quarter in data:
            assert quarter["fulfillment_rate"] == 100.0

    def test_quarterly_reports_all_filter_values(self, client):
        """Test that 'all' filter values behave like no filter."""
        unfiltered = client.get("/api/reports/quarterly").json()
        filtered = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert filtered == unfiltered

    def test_quarterly_reports_empty_result(self, client):
        """Test that filters matching nothing return an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrendsEndpoints:
    """Test suite for the monthly trends endpoint."""

    def test_get_all_monthly_trends(self, client):
        """Test getting monthly trends without filters."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for month in data:
            assert set(month.keys()) == MONTHLY_FIELDS
            assert len(month["month"]) == 7  # YYYY-MM

    def test_monthly_trends_sorted(self, client):
        """Test that months are returned in chronological order."""
        months = [m["month"] for m in client.get("/api/reports/monthly-trends").json()]
        assert months == sorted(months)

    def test_monthly_totals_match_quarterly(self, client):
        """Test that monthly and quarterly endpoints agree on totals."""
        monthly = client.get("/api/reports/monthly-trends").json()
        quarterly = client.get("/api/reports/quarterly").json()

        assert sum(m["order_count"] for m in monthly) == sum(q["total_orders"] for q in quarterly)
        assert abs(sum(m["revenue"] for m in monthly) - sum(q["total_revenue"] for q in quarterly)) < 0.05

    def test_monthly_revenue_is_rounded(self, client):
        """Test that revenue is rounded to cents."""
        for month in client.get("/api/reports/monthly-trends").json():
            assert month["revenue"] == round(month["revenue"], 2)

    def test_get_monthly_trends_by_category(self, client):
        """Test filtering monthly trends by category."""
        expected = client.get("/api/orders?category=Actuators").json()
        data = client.get("/api/reports/monthly-trends?category=Actuators").json()
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_get_monthly_trends_by_month(self, client):
        """Test that a single month filter returns only that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in data] == ["2025-03"]

    @pytest.mark.parametrize("status", ["Delivered", "Shipped", "Processing", "Backordered"])
    def test_get_monthly_trends_by_status(self, client, status):
        """Test filtering monthly trends by order status."""
        expected = client.get(f"/api/orders?status={status}").json()
        data = client.get(f"/api/reports/monthly-trends?status={status}").json()
        assert sum(m["order_count"] for m in data) == len(expected)
