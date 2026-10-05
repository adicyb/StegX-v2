import os
from pathlib import Path

def get_safe_output_path(output_directory: str | Path, filename: str) -> Path:
    """
    Securely resolves an output path ensuring it cannot escape the target directory.
    Defends against path traversal (e.g. ../), absolute paths, and symlink attacks.
    """
    # Normalize path separators
    normalized_name = filename.replace("\\", "/")
    
    # Reject payloads that contain directory traversal components or absolute paths
    # rather than silently sanitizing them, as a strong security posture.
    if "/" in normalized_name or ".." in normalized_name:
        raise ValueError(f"Security error: Payload filename '{filename}' contains invalid path traversal characters.")

    safe_filename = Path(normalized_name).name
    
    if not safe_filename or safe_filename == "." or safe_filename == "..":
        safe_filename = "extracted_payload.bin"
        
    # Ensure the output directory exists so realpath/resolve works securely
    os.makedirs(output_directory, exist_ok=True)
    
    base_dir = Path(output_directory).resolve()
    target_path = (base_dir / safe_filename).resolve()
    
    # Python 3.9+ component-aware containment check
    try:
        if not target_path.is_relative_to(base_dir):
            raise ValueError(f"Security error: Payload filename '{filename}' resolves outside the target directory.")
    except AttributeError:
        # Fallback for Python < 3.9 using parents
        if base_dir not in target_path.parents:
            raise ValueError(f"Security error: Payload filename '{filename}' resolves outside the target directory.")
            
    # As an additional strict check against symlink manipulation inside the directory
    if not str(target_path).startswith(str(base_dir)):
        raise ValueError(f"Security error: Payload filename '{filename}' escapes target directory.")

    return target_path
