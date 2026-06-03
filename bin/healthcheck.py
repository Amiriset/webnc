import sys, json, os, ssl, socket, urllib.request, urllib.parse
from datetime import datetime, timezone

url = sys.argv[1]

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version_file = os.path.join(project_root, "version.txt")
expected_version = None
if os.path.exists(version_file):
    with open(version_file) as f:
        expected_version = f.read().strip()

server_cert_path = os.path.join(project_root, "webnc_server.crt")

parsed = urllib.parse.urlparse(url)
host = parsed.hostname
port = parsed.port or 443

def check_cert(host, port):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    if os.path.exists(server_cert_path):
        ctx.load_verify_locations(server_cert_path)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    with socket.create_connection((host, port), timeout=5) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert()

def make_request(ctx):
    resp = urllib.request.urlopen(url, timeout=5, context=ctx)
    data = json.loads(resp.read().decode())
    if data.get("state") != "running":
        raise ValueError(f"state is '{data.get('state')}', expected 'running'")
    if expected_version and data.get("version") != expected_version:
        raise ValueError(f"version is '{data.get('version')}', expected '{expected_version}'")
    return data

try:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    data = make_request(ctx)
    print(json.dumps(data))
    sys.exit(0)
except urllib.error.URLError as e:
    reason = getattr(e, "reason", None)
    if isinstance(reason, ssl.SSLError):
        try:
            cert = check_cert(host, port)
            issuer = dict(x[0] for x in cert.get("issuer", []))
            subject = dict(x[0] for x in cert.get("subject", []))
            is_self_signed = issuer == subject
            not_after = cert.get("notAfter", "")
            not_before = cert.get("notBefore", "")
            try:
                expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires:
                    print(json.dumps({"error": f"Server certificate expired on {not_after}", "state": "error"}))
                    sys.exit(1)
            except (ValueError, KeyError):
                pass
            if is_self_signed:
                print(f"WARN: Self-signed certificate ({issuer.get('commonName', '?')}) - {not_before} to {not_after}", file=sys.stderr)
        except Exception as cert_err:
            print(f"WARN: Could not check certificate: {cert_err}", file=sys.stderr)
        print("WARN: Proceeding with SSL validation disabled", file=sys.stderr)
        ctx2 = ssl.create_default_context()
        ctx2.check_hostname = False
        ctx2.verify_mode = ssl.CERT_NONE
        ctx2.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            data = make_request(ctx2)
            print(json.dumps(data))
            sys.exit(0)
        except Exception as e2:
            print(json.dumps({"error": str(e2), "state": "error"}))
            sys.exit(1)
    print(json.dumps({"error": str(reason or e), "state": "error"}))
    sys.exit(1)
except Exception as e:
    print(json.dumps({"error": str(e), "state": "error"}))
    sys.exit(1)
