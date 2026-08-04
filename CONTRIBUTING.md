# Contributing to Orion

Thank you for your interest in Orion.

Orion is an open-source Home Cinema Operations Centre for Windows. The goal is to build reliable, well-structured software that improves the HTPC experience without unnecessary complexity.

---

# Development Philosophy

Orion follows a few core principles:

- Keep classes small and focused.
- One responsibility per class.
- Test new functionality before integrating it.
- Prefer readability over cleverness.
- Build features that solve real Home Cinema problems.

---

# Project Structure

```
app/
config/
data/
docs/
models/
tests/
ui/
```

Each folder has a specific purpose and new code should be placed in the appropriate module.

---

# Coding Standards

- Follow PEP 8 where practical.
- Use descriptive class and method names.
- Keep methods short.
- Avoid duplicated logic.
- Add comments only where they improve understanding.

---

# Workflow

Each feature follows the same development process:

1. Design
2. Prototype
3. Test
4. Integrate
5. Document
6. Commit

---

# Commit Messages

Use descriptive commit messages.

Examples:

```
feat(display): add display detection

feat(playback): implement playback session

fix(doctor): correct health calculation

docs: update roadmap

refactor(menu): simplify navigation
```

---

# Testing

Every significant feature should include an isolated test before being integrated into Orion.

Examples:

```
tests/test_detector.py
tests/test_display_controller.py
tests/test_health.py
```

---

# Vision

Orion is intended to become an intelligent Home Cinema Operations Centre capable of automatically monitoring, verifying and optimising Windows-based media playback.