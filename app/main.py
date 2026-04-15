from __future__ import annotations

from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates


app = FastAPI(title="AURA Admin Panel")
templates = Jinja2Templates(directory="app/templates")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


users = [
    {"email": "alice@example.com", "name": "Alice Johnson", "role": "Admin"},
    {"email": "bob@example.com", "name": "Bob Smith", "role": "Manager"},
    {"email": "carol@example.com", "name": "Carol White", "role": "Support"},
    {"email": "david@example.com", "name": "David Brown", "role": "IT"},
    {"email": "emma@example.com", "name": "Emma Davis", "role": "User"},
]


def redirect_with_message(location: str, message: str) -> RedirectResponse:
    return RedirectResponse(url=f"{location}?message={quote_plus(message)}", status_code=303)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "title": "Login",
            "message": request.query_params.get("message"),
        },
    )


@app.post("/login")
def login_submit(username: str = Form(...), password: str = Form(...)) -> RedirectResponse:
    _ = username, password
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": "Dashboard",
            "users": users,
            "message": request.query_params.get("message"),
        },
    )


@app.get("/create-user")
def create_user_page(request: Request):
    return templates.TemplateResponse(
        request,
        "create_user.html",
        {
            "title": "Create User",
            "message": request.query_params.get("message"),
        },
    )


@app.post("/create-user")
def create_user(
    email: str = Form(...),
    name: str = Form(...),
    role: str = Form(...),
) -> RedirectResponse:
    new_user = {"email": email.strip(), "name": name.strip(), "role": role.strip()}

    if any(user["email"].lower() == new_user["email"].lower() for user in users):
        return redirect_with_message("/create-user", f"User already exists: {new_user['email']}")

    users.append(new_user)
    return redirect_with_message("/dashboard", f"User created successfully for {new_user['email']}")


@app.post("/reset-password")
def reset_password(email: str = Form(...)) -> RedirectResponse:
    message = f"Password reset successful for {email}"
    return redirect_with_message("/dashboard", message)
