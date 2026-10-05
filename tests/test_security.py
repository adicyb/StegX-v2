import os
import pytest
from pathlib import Path

from stegx.utils.fs import get_safe_output_path
from stegx.core.payload import get_payload_info, MAGIC

def test_path_traversal_image_extraction():
    # Attempting to use a traversal sequence
    base_dir = Path("/tmp/safe_dir")
    evil_filename = "../../etc/passwd"
    
    with pytest.raises(ValueError, match="Security error"):
        get_safe_output_path(base_dir, evil_filename)

def test_path_traversal_absolute_path():
    base_dir = Path("/tmp/safe_dir")
    evil_filename = "/etc/passwd"
    
    with pytest.raises(ValueError, match="Security error"):
        get_safe_output_path(base_dir, evil_filename)

def test_path_traversal_windows_unc():
    base_dir = Path("/tmp/safe_dir")
    evil_filename = "\\\\localhost\\c$\\windows\\system32\\cmd.exe"
    
    with pytest.raises(ValueError, match="Security error"):
        get_safe_output_path(base_dir, evil_filename)

def test_payload_size_memory_exhaustion():
    # Manually construct a header with an enormous payload size
    version = 1
    flags = 0
    filename = "test.txt".encode("utf-8")
    filename_len = len(filename)
    payload_size = 0xFFFFFFFFFFFFFFFF # 18 Exabytes
    
    import struct
    header = (
        MAGIC
        + struct.pack("B", version)
        + struct.pack("B", flags)
        + struct.pack("H", filename_len)
        + filename
        + struct.pack("Q", payload_size)
    )
    
    with pytest.raises(ValueError, match="exceeds absolute maximum limit"):
        get_payload_info(header)

def test_filename_length_resource_exhaustion():
    # Construct a header with an absurdly large filename length
    version = 1
    flags = 0
    filename_len = 65535 # 65 KB filename length
    payload_size = 0
    
    import struct
    header = (
        MAGIC
        + struct.pack("B", version)
        + struct.pack("B", flags)
        + struct.pack("H", filename_len)
        + struct.pack("Q", payload_size)
    )
    
    with pytest.raises(ValueError, match="exceeds security limits"):
        get_payload_info(header)

def test_malformed_payload_truncation():
    # Construct a header that ends prematurely
    version = 1
    flags = 0
    filename_len = 50
    # But we don't supply 50 bytes of filename
    filename = "test".encode("utf-8")
    payload_size = 0
    
    import struct
    header = (
        MAGIC
        + struct.pack("B", version)
        + struct.pack("B", flags)
        + struct.pack("H", filename_len)
        + filename
        + struct.pack("Q", payload_size)
    )
    
    with pytest.raises(ValueError, match="ends prematurely"):
        get_payload_info(header)
