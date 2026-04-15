import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_duplicate_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create user first time
        await ac.post("/create-user", data={
            "email": "dup@company.com",
            "name": "Dup",
            "role": "Engineer"
        })

        # Attempt duplicate
        response = await ac.post("/create-user", data={
            "email": "dup@company.com",
            "name": "Dup",
            "role": "Engineer"
        })

        assert response.status_code in (200, 303, 400)


@pytest.mark.asyncio
async def test_reset_nonexistent_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/reset-password", data={
            "email": "ghost@company.com"
        })

        assert response.status_code in (200, 303)


@pytest.mark.asyncio
async def test_empty_create_user():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/create-user", data={
            "email": "",
            "name": "",
            "role": ""
        })

        assert response.status_code in (200, 400, 422)


@pytest.mark.asyncio
async def test_user_persists_in_dashboard():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/create-user", data={
            "email": "persist@company.com",
            "name": "Persist",
            "role": "Engineer"
        })

        response = await ac.get("/dashboard")

        assert "persist@company.com" in response.text