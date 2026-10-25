#!/usr/bin/env python3
"""
Pytest integration tests for Additional Features endpoints.

These tests require a running API instance plus valid credentials.
They are skipped by default unless RUN_ADDITIONAL_FEATURES_TESTS=1.
"""

import os
from typing import Dict, Iterable, Tuple

import aiohttp
import pytest


RUN_ADDITIONAL_FEATURES_TESTS = os.getenv("RUN_ADDITIONAL_FEATURES_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_ADDITIONAL_FEATURES_TESTS,
    reason="Requires running API server. Set RUN_ADDITIONAL_FEATURES_TESTS=1 to enable.",
)

# Configuration (can be overridden via environment variables)
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000/api")
ASSESSMENT_ID = os.getenv("TEST_ASSESSMENT_ID", "68dbf9e9047dde3cf58186dd")
JWT_TOKEN = os.getenv("TEST_JWT_TOKEN", "")


def _endpoints_to_test() -> Iterable[Tuple[str, str]]:
    """Yield endpoint tuples to simplify parametrization."""
    base = f"/v1/features/assessment/{ASSESSMENT_ID}"
    mapping: Dict[str, str] = {
        "Performance Monitoring": f"{base}/performance",
        "Compliance": f"{base}/compliance",
        "Experiments": f"{base}/experiments",
        "Quality Metrics": f"{base}/quality",
        "Approval Workflows": f"{base}/approvals",
        "Budget Forecasting": f"{base}/budget",
        "Executive Dashboard": f"{base}/executive",
        "Impact Analysis": f"{base}/impact",
        "Rollback Plans": f"{base}/rollback",
        "Vendor Lock-in Analysis": f"{base}/vendor-lockin",
        "All Features (Combined)": f"{base}/all-features",
    }
    return mapping.items()


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint_name, endpoint", list(_endpoints_to_test()))
async def test_additional_feature_endpoint_returns_payload(
    endpoint_name: str, endpoint: str
) -> None:
    """Call each endpoint and ensure it responds with meaningful data."""
    if not JWT_TOKEN:
        pytest.skip("TEST_JWT_TOKEN is required to run Additional Features tests")

    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json",
    }

    status = None
    data = None

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=30) as response:
                status = response.status
                try:
                    data = await response.json(content_type=None)
                except aiohttp.ContentTypeError:
                    data = await response.text()
        except aiohttp.ClientConnectorError as exc:
            pytest.skip(f"API server unreachable: {exc}")

    assert status == 200, f"{endpoint_name} returned HTTP {status} ({url})"
    assert data, f"{endpoint_name} returned an empty payload"
    assert (
        len(str(data)) > 100
    ), f"{endpoint_name} response too small to contain useful insights"
