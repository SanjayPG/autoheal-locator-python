"""
Shared test fixtures for AutoHeal integration tests.
"""

import asyncio
import pytest
import aiohttp

# Local model endpoint configuration
LOCAL_MODEL_URL = "https://tricks-stakeholders-output-received.trycloudflare.com/v1/chat/completions"
LOCAL_MODEL_ANTHROPIC_URL = "https://tricks-stakeholders-output-received.trycloudflare.com/v1/messages"
LOCAL_MODEL_HEALTH_URL = "https://tricks-stakeholders-output-received.trycloudflare.com/health"
LOCAL_MODEL_NAME = "deepseek-coder-v2:16b"


def is_endpoint_available():
    """Check if the local model endpoint is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(LOCAL_MODEL_HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# Skip marker for when endpoint is unavailable
requires_local_model = pytest.mark.skipif(
    not is_endpoint_available(),
    reason="Local model endpoint not available"
)


SAMPLE_HTML_LOGIN = """
<div class="form-container">
  <h2>Login</h2>
  <form id="login-form" action="/login" method="POST">
    <label for="username">Username</label>
    <input type="text" id="username" name="user" placeholder="Enter username" class="form-input">
    <label for="password">Password</label>
    <input type="password" id="password" name="pass" placeholder="Enter password" class="form-input">
    <button id="login-btn" class="btn btn-primary" type="submit">Login</button>
    <a href="/forgot" class="forgot-link">Forgot Password?</a>
    <a href="/register" class="register-link">Create Account</a>
  </form>
</div>
"""

SAMPLE_HTML_TABLE = """
<div class="data-table-container">
  <table id="users-table" class="table table-striped">
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Role</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr data-testid="row-1">
        <td>John Doe</td>
        <td>john@example.com</td>
        <td>Admin</td>
        <td>
          <button class="btn btn-edit" data-action="edit" data-user-id="1">Edit</button>
          <button class="btn btn-delete" data-action="delete" data-user-id="1">Delete</button>
        </td>
      </tr>
      <tr data-testid="row-2">
        <td>Jane Smith</td>
        <td>jane@example.com</td>
        <td>User</td>
        <td>
          <button class="btn btn-edit" data-action="edit" data-user-id="2">Edit</button>
          <button class="btn btn-delete" data-action="delete" data-user-id="2">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
"""

SAMPLE_HTML_NAVIGATION = """
<nav class="main-nav" role="navigation" aria-label="Main Navigation">
  <ul class="nav-list">
    <li><a href="/" class="nav-link active" aria-current="page">Home</a></li>
    <li><a href="/products" class="nav-link">Products</a></li>
    <li><a href="/about" class="nav-link">About Us</a></li>
    <li><a href="/contact" class="nav-link">Contact</a></li>
  </ul>
  <div class="nav-actions">
    <button class="btn-search" aria-label="Search">
      <span class="icon-search"></span>
    </button>
    <button class="btn-cart" aria-label="Shopping Cart">
      <span class="icon-cart"></span>
      <span class="cart-count">3</span>
    </button>
  </div>
</nav>
"""
