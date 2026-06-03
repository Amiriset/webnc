import sys
import json
import ssl
import urllib.request

url = sys.argv[1]
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.minimum_version = ssl.TLSVersion.TLSv1_2

try:
    resp = urllib.request.urlopen(url, timeout=5, context=ctx)
    data = json.loads(resp.read().decode())
    print(json.dumps(data))
    sys.exit(0)
except Exception as e:
    print(json.dumps({"error": str(e), "state": "error"}))
    sys.exit(1)
