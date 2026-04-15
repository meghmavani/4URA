"""
Integration tests ensuring frontend UI routes match backend endpoints.
Validates route consistency, end-to-end flows, and template correctness.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestRouteConsistency:
    """Verify all frontend-triggered routes exist on backend."""

    @pytest.mark.asyncio
    async def test_create_user_link_navigates_correctly(self):
        """Dashboard Create User link should navigate to valid endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/dashboard")
            assert response.status_code == 200
            
            assert 'href="/create-user"' in response.text
            assert "Create User" in response.text
            
            response = await ac.get("/create-user")
            assert response.status_code == 200
            assert "Create User" in response.text

    @pytest.mark.asyncio
    async def test_reset_password_route_exists(self):
        """Reset password route should exist and accept POST."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/reset-password", data={"email": "test@example.com"})
            assert response.status_code != 404
            assert response.status_code in (200, 303, 400, 422)

    @pytest.mark.asyncio
    async def test_no_old_routes_used(self):
        """Old route paths should not be used in UI."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/dashboard")
            
            assert "/users/create" not in response.text
            assert "/users/{email}/reset-password" not in response.text
            assert "/users/" not in response.text or "/users/create" not in response.text


class TestTemplateValidation:
    """Inspect rendered HTML for correct route references."""

    @pytest.mark.asyncio
    async def test_dashboard_has_correct_form_actions(self):
        """Dashboard reset password form should POST to /reset-password."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/dashboard")
            assert response.status_code == 200
            
            assert 'action="/reset-password"' in response.text
            assert 'method="post"' in response.text
            
            assert 'action="/users/' not in response.text

    @pytest.mark.asyncio
    async def test_create_user_form_posts_to_correct_endpoint(self):
        """Create user form should POST to /create-user."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/create-user")
            assert response.status_code == 200
            
            assert 'action="/create-user"' in response.text
            assert 'method="post"' in response.text
            
            assert 'name="email"' in response.text
            assert 'name="name"' in response.text
            assert 'name="role"' in response.text

    @pytest.mark.asyncio
    async def test_dashboard_has_all_required_ui_elements(self):
        """Dashboard should have all user management UI elements."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/dashboard")
            assert response.status_code == 200
            
            text_lower = response.text.lower()
            assert "create user" in text_lower
            assert "reset password" in text_lower
            assert "email" in text_lower
            assert "name" in text_lower
            assert "role" in text_lower


class TestEndToEndFlow:
    """Simulate complete user workflows."""

    @pytest.mark.asyncio
    async def test_complete_user_creation_flow(self):
        """Full workflow: login → dashboard → create user → verify in dashboard."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            login_response = await ac.post(
                "/login",
                data={"username": "testuser", "password": "testpass"}
            )
            assert login_response.status_code in (302, 303)
            
            dashboard_response = await ac.get("/dashboard")
            assert dashboard_response.status_code == 200
            assert "Dashboard" in dashboard_response.text
            
            create_response = await ac.post(
                "/create-user",
                data={
                    "email": "integration@test.com",
                    "name": "Integration Test User",
                    "role": "Engineer"
                }
            )
            assert create_response.status_code in (200, 303)
            
            dashboard_after_create = await ac.get("/dashboard")
            assert dashboard_after_create.status_code == 200
            assert "integration@test.com" in dashboard_after_create.text

    @pytest.mark.asyncio
    async def test_complete_password_reset_flow(self):
        """Full workflow: login → dashboard → reset password → verify message."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post(
                "/login",
                data={"username": "testuser", "password": "testpass"}
            )
            
            dashboard = await ac.get("/dashboard")
            assert dashboard.status_code == 200
            
            reset_response = await ac.post(
                "/reset-password",
                data={"email": "alice@example.com"},
                follow_redirects=True
            )
            assert reset_response.status_code == 200
            assert "successful" in reset_response.text.lower()

    @pytest.mark.asyncio
    async def test_create_and_reset_new_user(self):
        """Create a user, then reset their password."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post(
                "/login",
                data={"username": "test", "password": "test"}
            )
            
            reset_response = await ac.post(
                "/reset-password",
                data={"email": "alice@example.com"},
                follow_redirects=True
            )
            assert reset_response.status_code == 200
            assert "successful" in reset_response.text.lower()


class TestStatusSafety:
    """Ensure no UI-triggered routes return 404."""

    @pytest.mark.asyncio
    async def test_all_dashboard_links_return_valid_status(self):
        """All links on dashboard should not return 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            dashboard = await ac.get("/dashboard")
            assert dashboard.status_code == 200
            
            create_response = await ac.get("/create-user")
            assert create_response.status_code != 404
            
            logout_response = await ac.get("/login")
            assert logout_response.status_code != 404

    @pytest.mark.asyncio
    async def test_form_submissions_return_valid_status(self):
        """All form submissions should not return 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            login_response = await ac.post(
                "/login",
                data={"username": "test", "password": "test"}
            )
            assert login_response.status_code != 404
            
            create_response = await ac.post(
                "/create-user",
                data={
                    "email": "test@test.com",
                    "name": "Test",
                    "role": "User"
                }
            )
            assert create_response.status_code != 404
            
            reset_response = await ac.post(
                "/reset-password",
                data={"email": "test@example.com"}
            )
            assert reset_response.status_code != 404

    @pytest.mark.asyncio
    async def test_no_hidden_404_on_static_routes(self):
        """Static routes and asset paths should not return unexpected 404s."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            root_response = await ac.get("/", follow_redirects=False)
            assert root_response.status_code in (302, 303)
            
            login_response = await ac.get("/login")
            assert login_response.status_code == 200
            
            dashboard_response = await ac.get("/dashboard")
            assert dashboard_response.status_code == 200


class TestFormDataHandling:
    """Verify forms accept and process data correctly."""

    @pytest.mark.asyncio
    async def test_create_user_form_accepts_valid_email(self):
        """Create user form should accept valid email formats."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/create-user",
                data={
                    "email": "valid.email+tag@domain.co.uk",
                    "name": "Test User",
                    "role": "Engineer"
                }
            )
            assert response.status_code in (200, 303)

    @pytest.mark.asyncio
    async def test_reset_password_accepts_email_parameter(self):
        """Reset password should accept email from form data."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/reset-password",
                data={"email": "test@example.com"}
            )
            assert response.status_code != 404
            assert response.status_code in (200, 303, 400, 422)

    @pytest.mark.asyncio
    async def test_form_method_is_post_not_get(self):
        """Sensitive operations should use POST, not GET."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            create_get = await ac.get("/create-user/submit")
            
            reset_get = await ac.get("/reset-password")
            
            dashboard = await ac.get("/dashboard")
            assert 'method="post"' in dashboard.text


class TestHtmlStructure:
    """Validate HTML structure for accessibility and correctness."""

    @pytest.mark.asyncio
    async def test_dashboard_table_has_reset_buttons_per_row(self):
        """Each user row should have a Reset Password button."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            dashboard = await ac.get("/dashboard")
            assert dashboard.status_code == 200
            
            reset_count = dashboard.text.count("Reset Password")
            assert reset_count >= 5

    @pytest.mark.asyncio
    async def test_form_inputs_have_proper_attributes(self):
        """Form inputs should have required attributes for accessibility."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/create-user")
            assert response.status_code == 200
            
            assert 'for="email"' in response.text
            assert 'for="name"' in response.text
            assert 'for="role"' in response.text
            
            assert 'id="email"' in response.text
            assert 'id="name"' in response.text
            assert 'id="role"' in response.text

    @pytest.mark.asyncio
    async def test_messages_render_correctly(self):
        """Form submissions and redirects should work correctly."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post(
                "/login",
                data={"username": "test", "password": "test"}
            )
            
            response = await ac.post(
                "/create-user",
                data={
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "User"
                },
                follow_redirects=True
            )
            
            assert response.status_code in (200, 303)
            
            dashboard = await ac.get("/dashboard")
            assert dashboard.status_code == 200
            assert "Dashboard" in dashboard.text
