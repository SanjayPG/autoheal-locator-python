# AutoHeal Locator Python — Start Here

This is the **library source**. If you just want to run tests against a demo site, go straight to one of the demo projects below.

---

## Choose Your Path

### I want to see it working immediately

| Demo Project | Framework | Repo |
|---|---|---|
| Selenium demo | Selenium + Python | [autoheal-selenium-python-demo](https://github.com/SanjayPG/autoheal-selenium-python-demo) |
| Playwright demo | Playwright + Python | [playwright-autoheal-python-demo](https://github.com/SanjayPG/playwright-autoheal-python-demo) |

Each demo has its own **START_HERE.md** that walks you through setup step by step — from zero to a running test in 5 minutes.

---

### I want to install the library in my own project

```bash
# Selenium project
pip install autoheal-locator

# Playwright project
pip install autoheal-locator[playwright]

# Both + Redis cache
pip install autoheal-locator[all]
```

Then follow the **[README.md](README.md)** for full usage documentation.

---

### I want to contribute or modify the library source

```bash
git clone https://github.com/SanjayPG/autoheal-locator-python.git
cd autoheal-locator-python
pip install -e .   # editable install — changes take effect immediately
```

---

## What Is AutoHeal Locator?

AutoHeal Locator is a Python library that makes Selenium and Playwright tests **self-healing**.

When a test selector breaks because the UI changed, AutoHeal:
1. Reads the page HTML (or takes a screenshot)
2. Sends it to an AI with a description of the element
3. Gets back the correct selector
4. Caches the result so future runs don't need AI at all

```
#user-name-wrong  ──AI──►  #user-name   ✓ test passes
#password-wrong   ──AI──►  #password    ✓ test passes
#login-btn-wrong  ──AI──►  #login-button ✓ test passes

Second run — all served from cache in <5ms, no AI cost
```

---

## Supported AI Providers

| Provider | Free Tier | Best For |
|---|---|---|
| **Groq** | Yes — generous | Getting started (recommended) |
| **Google Gemini** | Yes — limited | Low-cost production |
| **OpenAI** | No — paid | High accuracy |
| **Anthropic** | No — paid | High accuracy |
| **DeepSeek** | Low cost | DOM-only, code-heavy pages |
| **Ollama (local)** | Free | Privacy, no internet needed |

---

## Supported Frameworks

| Framework | Sync API | Async API | Status |
|---|---|---|---|
| Selenium | `find_element()` | `find_element_async()` | Available |
| Playwright | `find_element_async()` | `find_async()` | Available |

---

## PyPI

```bash
pip install autoheal-locator
```

https://pypi.org/project/autoheal-locator/

---

## Links

| Resource | URL |
|---|---|
| PyPI | https://pypi.org/project/autoheal-locator/ |
| GitHub (library) | https://github.com/SanjayPG/autoheal-locator-python |
| Selenium demo | https://github.com/SanjayPG/autoheal-selenium-python-demo |
| Playwright demo | https://github.com/SanjayPG/playwright-autoheal-python-demo |
| Java version | https://github.com/SanjayPG/autoheal-locator |
| Free Groq API key | https://console.groq.com |
