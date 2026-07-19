import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit


class UnsafeUrlError(ValueError):
    pass


async def validate_public_url(url: str, allow_private: bool = False) -> str:
    """Validate URL scheme and DNS targets to reduce SSRF exposure."""
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http:// and https:// URLs are supported")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in URLs are not allowed")
    if parsed.hostname.lower() == "localhost" and not allow_private:
        raise UnsafeUrlError("Local/private network targets are blocked")

    if not allow_private:
        try:
            addresses = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: socket.getaddrinfo(
                    parsed.hostname,
                    parsed.port or (443 if parsed.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                ),
            )
        except socket.gaierror as exc:
            raise UnsafeUrlError(
                f"Hostname could not be resolved: {parsed.hostname}"
            ) from exc
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise UnsafeUrlError(f"Non-public target is blocked: {ip}")

    return parsed.geturl()
