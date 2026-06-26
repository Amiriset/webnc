# Security Policy

## Supported Versions

| Version | Supported |
|----------|----------|
| 0.13.x | ✅ |
| < 0.13 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability, please do not create a public GitHub issue.

Instead:

- Open a GitHub Security Advisory
- Or contact the maintainer directly

Please include:

- WebNC version
- OS version
- Steps to reproduce
- Impact assessment

## Security Model

WebNC is designed as a local-first administration utility.

By default:

- HTTPS is enabled
- TLS 1.3 is enforced
- Session authentication is required
- Access is bound to localhost (127.0.0.1)

The application is intended to be deployed behind additional security controls when exposed remotely.

## Threat Model

WebNC assumes:

- The host machine is trusted
- The authenticated user is trusted
- The application may have unrestricted filesystem access

WebNC does not attempt to protect a trusted user from their own actions.

Examples:

- Deleting files
- Overwriting files
- Executing allowed commands
- Browsing sensitive directories

## Current Limitations

The following areas are still under active development:

- Fine-grained RBAC
- Audit logging
- Multi-user support
- Filesystem allowlists
- Read-only mode
- SFTP isolation

## Remote Exposure Warning

Running WebNC on `--host 0.0.0.0` or exposing it directly to the Internet is not recommended without:

- Reverse proxy
- Additional authentication
- Firewall restrictions
- TLS certificate management
