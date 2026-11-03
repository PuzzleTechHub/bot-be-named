def hyperlink(url: str, label: str) -> str:
    """Build a Sheets HYPERLINK formula with escaped string arguments."""
    url = url.replace('"', '""')
    label = label.replace('"', '""')
    return f'=HYPERLINK("{url}", "{label}")'
