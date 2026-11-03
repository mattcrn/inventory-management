"""
Tests for restocking order API endpoints.
"""
import json
from datetime import date, timedelta

import pytest

import main
import mock_data


@pytest.fixture(autouse=True)
def isolated_restocking_orders(tmp_path, monkeypatch):
    """Point persistence at a temp file and start every test with no orders.

    main.restocking_orders is the same list object as mock_data's, so it is
    cleared in place (rebinding it would leave the endpoint on the old list).
    The original contents are restored afterwards so a developer's real
    orders file is never touched by the test run.
    """
    orders_file = tmp_path / "restocking_orders.json"
    monkeypatch.setattr(mock_data, "RESTOCKING_ORDERS_FILE", str(orders_file))
    saved = list(main.restocking_orders)
    main.restocking_orders.clear()
    yield orders_file
    main.restocking_orders.clear()
    main.restocking_orders.extend(saved)


@pytest.fixture
def forecasts(client):
    """Demand forecasts keyed by SKU."""
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestDemandPricingFields:
    """Forecasts carry the pricing data restocking depends on."""

    def test_forecasts_have_unit_cost_and_lead_time(self, client):
        """Every forecast has a positive unit_cost and lead_time_days."""
        data = client.get("/api/demand").json()
        assert len(data) > 0
        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0


class TestRestockingOrdersEndpoints:
    """Test suite for restocking order endpoints."""

    def test_get_restocking_orders_empty(self, client):
        """No orders are returned before anything is submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client, forecasts):
        """A valid order is priced server-side and gets the max lead time."""
        payload = {
            "budget": 100000,
            "items": [
                {"item_sku": "WDG-001", "quantity": 100},
                {"item_sku": "MTR-304", "quantity": 2},
            ],
        }
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["budget"] == 100000
        assert len(order["items"]) == 2

        expected_total = sum(
            forecasts[line["item_sku"]]["unit_cost"] * line["quantity"]
            for line in payload["items"]
        )
        assert abs(order["total_cost"] - expected_total) < 0.01

        for line in order["items"]:
            forecast = forecasts[line["item_sku"]]
            assert line["item_name"] == forecast["item_name"]
            assert line["unit_cost"] == forecast["unit_cost"]
            assert abs(line["line_total"] - line["quantity"] * line["unit_cost"]) < 0.01

    def test_restocking_order_lead_time_calculation(self, client, forecasts):
        """Lead time is the slowest line; delivery is today plus that."""
        payload = {
            "budget": 100000,
            "items": [
                {"item_sku": "GSK-203", "quantity": 10},
                {"item_sku": "VLV-506", "quantity": 10},
            ],
        }
        order = client.post("/api/restocking-orders", json=payload).json()

        expected_lead = max(forecasts[s]["lead_time_days"] for s in ("GSK-203", "VLV-506"))
        assert order["lead_time_days"] == expected_lead
        assert order["created_date"] == date.today().isoformat()
        assert order["expected_delivery"] == (
            date.today() + timedelta(days=expected_lead)
        ).isoformat()

    def test_submitted_order_listed_newest_first(self, client):
        """Submitted orders appear in GET, newest first."""
        for qty in (1, 2):
            client.post(
                "/api/restocking-orders",
                json={"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": qty}]},
            )
        data = client.get("/api/restocking-orders").json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]

    def test_restocking_order_persisted_to_file(self, client, isolated_restocking_orders):
        """Submitting an order writes it to the JSON file."""
        client.post(
            "/api/restocking-orders",
            json={"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": 5}]},
        )
        saved = json.loads(isolated_restocking_orders.read_text())
        assert len(saved) == 1
        assert saved[0]["order_number"] == "RST-0001"

    def test_restocking_order_over_budget(self, client):
        """An order whose server-computed total exceeds the budget is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 100, "items": [{"item_sku": "MTR-304", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]
        assert client.get("/api/restocking-orders").json() == []

    def test_restocking_order_unknown_sku(self, client):
        """An SKU not in the demand forecast is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 1000, "items": [{"item_sku": "NOPE-999", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "unknown" in response.json()["detail"].lower()

    def test_restocking_order_duplicate_sku(self, client):
        """The same SKU may not appear twice in one order."""
        response = client.post(
            "/api/restocking-orders",
            json={
                "budget": 1000,
                "items": [
                    {"item_sku": "FLT-405", "quantity": 1},
                    {"item_sku": "FLT-405", "quantity": 1},
                ],
            },
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("payload", [
        {"budget": 1000, "items": []},
        {"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": 0}]},
        {"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": -3}]},
        {"budget": 0, "items": [{"item_sku": "FLT-405", "quantity": 1}]},
    ])
    def test_restocking_order_validation_errors(self, client, payload):
        """Empty orders, non-positive quantities and budgets are 422."""
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 422

    def test_restocking_order_exact_budget_boundary(self, client, forecasts):
        """A total exactly equal to the budget passes; one cent less fails."""
        unit_cost = forecasts["WDG-001"]["unit_cost"]
        exact = round(unit_cost * 7, 2)
        items = [{"item_sku": "WDG-001", "quantity": 7}]

        response = client.post("/api/restocking-orders", json={"budget": exact - 0.01, "items": items})
        assert response.status_code == 400

        response = client.post("/api/restocking-orders", json={"budget": exact, "items": items})
        assert response.status_code == 201

    def test_restocking_order_save_failure_not_committed(self, client, monkeypatch):
        """If persisting fails, the order must not linger in memory."""
        def failing_save(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(mock_data, "save_restocking_orders", failing_save)

        with pytest.raises(OSError):
            client.post(
                "/api/restocking-orders",
                json={"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": 1}]},
            )
        assert main.restocking_orders == []

    def test_restocking_order_number_follows_max_existing(self, client):
        """Numbering continues from the highest number, not the list length."""
        main.restocking_orders.append({"order_number": "RST-0007"})
        order = client.post(
            "/api/restocking-orders",
            json={"budget": 1000, "items": [{"item_sku": "FLT-405", "quantity": 1}]},
        ).json()
        assert order["order_number"] == "RST-0008"
