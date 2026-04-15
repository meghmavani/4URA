import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


VALID_UI_ROUTES = {"/create-user", "/reset-password", "/login", "/dashboard"}
INVALID_UI_ROUTES = {"/users/create", "/users/{email}/reset-password"}


def _unique_email(prefix: str = "system") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@company.com"


def _extract_html_routes(html: str) -> tuple[set[str], set[str]]:
    links = set(re.findall(r'href="([^"]+)"', html))
    forms = set(re.findall(r'action="([^"]+)"', html))
    return links, forms


@pytest.mark.asyncio
async def test_full_user_flow_end_to_end():
    transport = ASGITransport(app=app)
    email = _unique_email("fullflow")

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post(
            "/login",
            data={"username": "demo", "password": "demo"},
            follow_redirects=True,
        )
        assert login.status_code == 200
        assert "dashboard" in login.text.lower()

        dashboard_before = await ac.get("/dashboard")
        assert dashboard_before.status_code == 200

        create = await ac.post(
            "/create-user",
            data={"email": email, "name": "Full Flow", "role": "User"},
            follow_redirects=True,
        )
        assert create.status_code == 200
        assert "user created successfully" in create.text.lower()

        dashboard_after_create = await ac.get("/dashboard")
        assert dashboard_after_create.status_code == 200
        assert email in dashboard_after_create.text

        reset = await ac.post(
            "/reset-password",
            data={"email": email},
            follow_redirects=True,
        )
        assert reset.status_code == 200
        assert f"password reset successful for {email}" in reset.text.lower()

        dashboard_after_reset = await ac.get("/dashboard")
        assert dashboard_after_reset.status_code == 200
        assert email in dashboard_after_reset.text


@pytest.mark.asyncio
async def test_redirect_validation_for_post_routes():
    transport = ASGITransport(app=app)
    email = _unique_email("redirect")

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post(
            "/login",
            data={"username": "demo", "password": "demo"},
            follow_redirects=False,
        )
        assert login.status_code == 303
        assert login.headers.get("location") == "/dashboard"
        login_target = await ac.get(login.headers["location"])
        assert login_target.status_code == 200

        create = await ac.post(
            "/create-user",
            data={"email": email, "name": "Redirect", "role": "User"},
            follow_redirects=False,
        )
        assert create.status_code == 303
        create_location = create.headers.get("location", "")
        assert create_location.startswith("/dashboard")
        create_target = await ac.get(create_location)
        assert create_target.status_code == 200

        reset = await ac.post(
            "/reset-password",
            data={"email": email},
            follow_redirects=False,
        )
        assert reset.status_code == 303
        reset_location = reset.headers.get("location", "")
        assert reset_location.startswith("/dashboard")
        reset_target = await ac.get(reset_location)
        assert reset_target.status_code == 200


@pytest.mark.asyncio
async def test_ui_route_validation_from_rendered_html():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        dashboard = await ac.get("/dashboard")
        assert dashboard.status_code == 200

        create_page = await ac.get("/create-user")
        assert create_page.status_code == 200

        dashboard_links, dashboard_forms = _extract_html_routes(dashboard.text)
        create_links, create_forms = _extract_html_routes(create_page.text)

        all_routes = dashboard_links | dashboard_forms | create_links | create_forms

        for invalid in INVALID_UI_ROUTES:
            assert invalid not in dashboard.text
            assert invalid not in create_page.text
            assert invalid not in all_routes

        assert "/create-user" in all_routes
        assert "/reset-password" in all_routes
        assert "/create-user" in VALID_UI_ROUTES
        assert "/reset-password" in VALID_UI_ROUTES


@pytest.mark.asyncio
async def test_form_validation_fields_and_reset_hidden_email():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_page = await ac.get("/create-user")
        assert create_page.status_code == 200

        create_html = create_page.text
        assert 'name="email"' in create_html
        assert 'name="name"' in create_html
        assert 'name="role"' in create_html

        dashboard = await ac.get("/dashboard")
        assert dashboard.status_code == 200

        dashboard_html = dashboard.text
        assert 'action="/reset-password"' in dashboard_html
        assert 'type="hidden"' in dashboard_html
        assert 'name="email"' in dashboard_html


@pytest.mark.asyncio
async def test_no_404_for_known_ui_routes():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for route in ["/login", "/dashboard", "/create-user"]:
            response = await ac.get(route)
            assert response.status_code != 404
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_message_visibility_after_create_and_reset():
    transport = ASGITransport(app=app)
    email = _unique_email("msg")

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post(
            "/create-user",
            data={"email": email, "name": "Message Test", "role": "User"},
            follow_redirects=True,
        )
        assert create.status_code == 200
        assert "user created successfully" in create.text.lower()

        reset = await ac.post(
            "/reset-password",
            data={"email": email},
            follow_redirects=True,
        )
        assert reset.status_code == 200
        assert "password reset successful" in reset.text.lower()
        assert email in reset.text


@pytest.mark.asyncio
async def test_multiple_users_creation_and_reset_for_each():
    transport = ASGITransport(app=app)
    users_to_create = [
        _unique_email("multi1"),
        _unique_email("multi2"),
        _unique_email("multi3"),
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for idx, email in enumerate(users_to_create, start=1):
            create = await ac.post(
                "/create-user",
                data={"email": email, "name": f"Multi User {idx}", "role": "User"},
                follow_redirects=True,
            )
            assert create.status_code == 200

        dashboard = await ac.get("/dashboard")
        assert dashboard.status_code == 200
        for email in users_to_create:
            assert email in dashboard.text

        for email in users_to_create:
            reset = await ac.post(
                "/reset-password",
                data={"email": email},
                follow_redirects=True,
            )
            assert reset.status_code == 200
            assert "password reset successful" in reset.text.lower()
            assert email in reset.text
