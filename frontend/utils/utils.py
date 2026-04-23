def format_bytes(size: int | None) -> str:
    """Format a byte size using binary units (1KB = 1024 bytes, 1MB = 1024KB, etc.)
    with up to 2 decimal places and no unnecessary trailing zeros.

    Examples:
        >>> format_bytes(1024)
        '1 KB'
        >>> format_bytes(1536)
        '1.5 KB'
        >>> format_bytes(1269)
        '1.24 KB'
        >>> format_bytes(10485760)
        '10 MB'
    """
    if size is None:
        return ""

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    formatted = f"{size:.2f}".rstrip("0").rstrip(".")
    return f"{formatted} {units[unit_index]}"
