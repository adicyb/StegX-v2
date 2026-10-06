import sys
import pytest
from pathlib import Path

def test_launcher_imports():
    """Verify the launcher module can be imported without syntax errors."""
    try:
        import stegx.ui.launcher
    except ImportError:
        pytest.fail("Failed to import launcher")

def test_launcher_resolves_app():
    """Verify the launcher logic accurately resolves the app.py file."""
    try:
        from importlib.resources import files
        app_path = str(files("stegx.ui") / "app.py")
    except ImportError:
        import stegx.ui
        app_path = str(Path(stegx.ui.__file__).parent / "app.py")
        
    assert Path(app_path).is_file(), f"app.py not found at {app_path}"
    assert app_path.endswith("app.py"), "Resolved path does not end with app.py"

def test_pyproject_entry_points():
    """Verify that both stegx and stegx-web are defined in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.is_file()
    
    content = pyproject_path.read_text()
    assert 'stegx = "stegx.cli:main"' in content, "Missing stegx CLI entry point"
    assert 'stegx-web = "stegx.ui.launcher:main"' in content, "Missing stegx-web launcher entry point"
