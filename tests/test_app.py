import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_login_redirect():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/login", data={"username": "x", "password": "y"})
        assert response.status_code in (302, 303)


@pytest.mark.asyncio
async def test_dashboard_loads():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/dashboard")
        assert response.status_code == 200
        assert "user" in response.text.lower()


@pytest.mark.asyncio
async def test_create_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/create-user",
            data={
                "email": "john@company.com",
                "name": "John",
                "role": "Engineer",
            },
        )

        assert response.status_code in (200, 302, 303)


@pytest.mark.asyncio
async def test_reset_password():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/reset-password", data={"email": "john@company.com"})

        assert response.status_code in (200, 303)
        if response.status_code == 303:
            dashboard = await ac.get("/dashboard")
            assert "password reset" in dashboard.text.lower() or dashboard.status_code == 200