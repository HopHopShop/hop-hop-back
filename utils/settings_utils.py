def add_prefix_to_allowed_hosts(allowed_hosts: str) -> list:
    """
    Adds 'https://' prefix to allowed hosts for CORS and CSRF settings.

    This function takes a comma-separated string of allowed hosts and
    converts them into a list of hosts with 'https://' prefix if not already present.

    Args:
        allowed_hosts (str): A comma-separated string of allowed hosts.

    Returns:
        list: A list of hosts with 'https://' prefix.
    """
    updated_hosts = []
    updated_hosts.append("http://localhost:80")
    for host in allowed_hosts.split(","):
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        updated_hosts.append(host)

    return updated_hosts