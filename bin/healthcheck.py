import sys
import json
import os
import ssl
import socket
import urllib.request
import urllib.parse
from datetime import datetime, timezone

if len(sys.argv) < 2:
    print(json.dumps({"error": "No URL provided", "state": "error"}))
    sys.exit(1)

url = sys.argv[1]

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version_file = os.path.join(project_root, "version.txt")
cert_path = os.path.join(project_root, "webnc_server.crt")

expected_version = None
if os.path.exists(version_file):
    with open(version_file) as f:
        expected_version = f.read().strip()

parsed = urllib.parse.urlparse(url)
host = parsed.hostname
port = parsed.port or 443


def make_request(ctx):
    """Perform HTTP request and validate response fields."""
    resp = urllib.request.urlopen(url, timeout=3, context=ctx)
    data = json.loads(resp.read().decode())
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON response from server")
    if data.get("state") != "running":
        raise ValueError(f"state is '{data.get('state')}', expected 'running'")
    if expected_version and data.get("version") != expected_version:
        raise ValueError(f"version is '{data.get('version')}', expected '{expected_version}'")
    return data


def verify_cert_chain(host, port, trusted_ca_path):
    """Connect with full verification to analyze server certificate."""
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    if trusted_ca_path and os.path.exists(trusted_ca_path):
        ctx.load_verify_locations(trusted_ca_path)
    with socket.create_connection((host, port), timeout=3) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert()


# --- MAIN FLOW ---
try:
    data = None
    warning_msg = None

    # Step 1: Fetch with full TLS 1.3 validation
    try:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        if os.path.exists(cert_path):
            ctx.load_verify_locations(cert_path)
        data = make_request(ctx)
    except urllib.error.URLError as e:
        # Fallback: bypass server cert validation but keep TLS 1.3
        if isinstance(getattr(e, "reason", None), ssl.SSLError):
            print(f"DEBUG: Initial TLS 1.3 handshake failed validation: {e.reason}", file=sys.stderr)
            ctx_fallback = ssl.create_default_context()
            ctx_fallback.check_hostname = False
            ctx_fallback.verify_mode = ssl.CERT_NONE
            ctx_fallback.minimum_version = ssl.TLSVersion.TLSv1_3
            data = make_request(ctx_fallback)
            warning_msg = "SSL validation bypassed for API read"
        else:
            raise e

    # Step 2: Deep certificate audit on a separate connection
    if data and isinstance(data, dict):
        try:
            cert_details = verify_cert_chain(host, port, cert_path)
            raw_issuer = cert_details.get("issuer", [])
            raw_subject = cert_details.get("subject", [])

            # Self-signed check (issuer == subject)
            if raw_issuer == raw_subject and raw_issuer:
                warning_msg = "Self-signed certificate"

        except ssl.SSLCertVerificationError as cert_err:
            print(f"DEBUG: Certificate chain validation failed "
                  f"code [{cert_err.verify_code}]: {cert_err.verify_message}", file=sys.stderr)

            error_reason = None
            code = cert_err.verify_code
            msg = cert_err.verify_message.lower() if cert_err.verify_message else ""

            if code == 44 or "revoked" in msg:
                error_reason = f"CRITICAL SECURITY: Server certificate has been REVOKED! (Code {code})"
            elif code in (10, 14) or "expired" in msg:
                error_reason = f"SECURITY ERROR: Server certificate has EXPIRED! (Code {code})"
            elif code in (18, 19):
                warning_msg = "Untrusted self-signed certificate"
            elif code == 3:
                # unable to get CRL — expected for self-signed certs without CRL distribution points
                warning_msg = "Self-signed certificate (no CRL)"
            else:
                error_reason = (f"SECURITY ERROR: Invalid certificate chain "
                                f"({cert_err.verify_message}). Code {code}")

            if error_reason:
                print(json.dumps({"error": error_reason, "state": "error", "status": "failed"}))
                sys.exit(1)

        except Exception as conn_err:
            print(json.dumps({"error": f"Security check network failure: {conn_err}", "state": "error"}))
            sys.exit(1)

    if warning_msg:
        data["warning"] = warning_msg

    print(json.dumps(data))
    sys.exit(0)

except Exception as e:
    # Server not ready yet (port not listening) — signal PS to retry
    print(json.dumps({"error": str(e), "state": "booting"}))
    sys.exit(1)
