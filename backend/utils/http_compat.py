import http.client


_original_http_response_close = http.client.HTTPResponse.close


def patch_http_response_close() -> None:
    if getattr(http.client.HTTPResponse.close, "_enderpanel_patched", False):
        return

    def safe_close(self):
        try:
            return _original_http_response_close(self)
        except ValueError as exc:
            if "I/O operation on closed file" not in str(exc):
                raise
            return None

    safe_close._enderpanel_patched = True  # type: ignore[attr-defined]
    http.client.HTTPResponse.close = safe_close
