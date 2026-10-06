import pytest

def test_ui_imports():
    """
    Ensure the StegX UI modules can be imported correctly
    without immediately launching expensive crypto operations or failing.
    """
    try:
        import stegx.ui.app
        import stegx.ui.theme
        import stegx.ui.components
        import stegx.ui.pages.dashboard
    except ImportError as e:
        pytest.fail(f"UI Import failed: {e}")

def test_cli_compatibility():
    """
    Verify the existing CLI still exists and is importable alongside the new UI.
    """
    try:
        import stegx.cli
        assert hasattr(stegx.cli, "app")
    except ImportError as e:
        pytest.fail(f"CLI Import failed after UI additions: {e}")
