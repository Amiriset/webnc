# WebNC Compliance Documentation

This document outlines WebNC's compliance with various standards, policies, and best practices related to data handling, security, privacy, and auditability.

## Overview
WebNC is designed as a local-first, keyboard-driven file manager for Windows with enterprise-grade security features. While it provides powerful filesystem access, it implements multiple layers of protection and follows privacy-by-design principles.

## Data Handling Policies

### Authentication Data
- **Session Tokens**: Ephemeral 256-bit secrets generated via `secrets.token_hex(32)` at each server start
- **Storage**: 
  - Server: RAM only (never written to disk)
  - Client: `sessionStorage` (cleared on tab/window close)
- **Transmission**: Never transmitted; only SHA-256 hashes of nonce+timestamp+secret are sent
- **Lifetime**: Valid for 5 minutes from generation (timestamp window)
- **Regeneration**: New token created on each server startup
- **Console Output**: Token printed to `stderr` only (not logger) to prevent token leakage to log files

### Configuration Data
- **Operation Settings** (`config.json`):
  - Stored in project root: `config/config.json`
  - Contains timeout/retry settings for 8 operation types
  - No personal or sensitive data stored
  - Thread-safe atomic writes via `.tmp` + replace
- **UI Preferences** (localStorage):
  - Stored in browser under key `nc_config`
  - Contains view mode, sort preferences, hidden files setting, etc.
  - No personal or sensitive data stored
  - Cleared when browser data is cleared

### Log Data
- **Log File**: `logs/webnc_server.log` (rotating: 5 MB × 3 backups)
- **Log Format**: `%(asctime)s | %(levelname)-8s | %(message)s`
- **Log Configuration**: Custom `log_config` dict passed to `uvicorn.run()` to ensure consistent format across all handlers (uvicorn access, error, and default logs)
- **Logged Information**:
  - Server start/stop events
  - All API calls (endpoint, HTTP method, status code)
  - Authentication successes/failures
  - Warnings for swallowed exceptions
  - Errors with stack traces
  - Certificate generation events
  - Health check results
- **Not Logged**:
  - Authentication tokens or secrets
  - File contents or metadata
  - User passwords or credentials
  - Personal identifying information
  - Sensitive filesystem paths (beyond what's necessary for operation)

### Operational Data
- **File Operations**: 
  - No persistent audit log of file operations currently implemented
  - Operations are performed in real-time with no intermediate storage
  - Error conditions are logged but do not include file contents
- **Operation Queue**:
  - In-memory only during operation execution
  - No persistence of operation history or results
  - Completed operations are discarded from memory
- **Cache**:
  - No intentional caching of filesystem data
  - Frontend may temporarily cache view state for responsiveness
  - Operation polling uses temporary IDs only

## Security Compliance

### Transport Security (TLS 1.3)
- **Protocol**: TLS 1.3 (`minimum_version = TLSv1_3`)
- **Key Exchange**: RSA-4096, auto-generated via `cryptography` library
- **Cipher Configuration**: 
  - Server-preference ordering
  - `OP_NO_COMPRESSION` (CRIME/BREACH protection)
  - `OP_CIPHER_SERVER_PREFERENCE`
- **Certificate**:
  - Auto-generated self-signed RSA-4096 certificate
  - Subject Alternative Name (SAN): `localhost`, `127.0.0.1`, `::1`
  - Validity period: 10 years
  - Auto-renewed on deletion of `.crt`/`.key` files
  - No dependence on `openssl` CLI (pure Python implementation)

### Session Authentication
- **Mechanism**: Zero-knowledge SHA-256 handshake
- **Components**:
  - `X-NC-Nonce`: Cryptographically random nonce per request
  - `X-NC-Timestamp`: Current UNIX timestamp
  - `X-NC-Signature`: SHA-256(nonce + timestamp + secret_token)
- **Protection**:
  - Replay prevention: Nonce tracked in `USED_NONCES` set (cleared at 10k entries)
  - Timestamp window: 5 minutes (`abs(now - ts) > 300` → rejected)
  - Constant-time comparison: `secrets.compare_digest()` prevents timing attacks
  - Secret entropy: 256 bits (`secrets.token_hex(32)`)
- **Storage**: Secret held only in server RAM; client stores token in `sessionStorage`

### Authorization Framework
- **Provider Interface**: `AuthProvider(ABC)` with `authenticate()` and `authorize()` methods
- **Default Provider**: `ConsoleTokenProvider` (zero-knowledge token handshake)
- **Extensibility**: Designed for AD/Kerberos/JWT/LDAP providers without modifying core
- **Middleware**: `SessionAuthMiddleware` validates all requests (except exempt endpoints)
- **Exempt Endpoints**: 
  - `/api/health`: No authentication required
  - `/api/drives`: Drive listing (non-sensitive)
  - `/api/disk`: Disk usage (non-sensitive)
- **Module Registry**: `app.state.modules` enables feature flags per user/role (planned for RBAC)

### Filesystem Access
- **Path Validation**: 
  - All paths converted via `safe_path()` function in VFS layer
  - Protection against directory traversal attacks
  - URL format (`/C/Users/...`) used consistently in API
  - Conversion to Windows paths only at filesystem boundary
- **Error Handling**:
  - `PermissionError`: Logs warning but continues operation (skips inaccessible items)
  - No elevation of privileges or bypass of OS permissions
  - Operations respect Windows ACLs and permissions
- **Information Access**:
  - File owner via Win32 API (`GetNamedSecurityInfoW` + `LookupAccountSidW`)
  - Only retrieved for `/api/info` endpoint (not in directory listings for performance)
  - Falls back to uid:gid format if lookup fails

### Cryptographic Standards
- **Hashing**: SHA-256 for all authentication-related operations
- **Random Generation**: `secrets` module for cryptographically secure random numbers
- **Comparison**: Constant-time functions to prevent timing attacks
- **Key Length**: RSA-4096 for TLS certificates
- **No Weak Algorithms**: No MD5, SHA-1, or RC4 usage

## Privacy Considerations

### Data Minimization
- **Collection**: Only collects data necessary for operation execution
- **Retention**: 
  - Authentication tokens: Ephemeral (5-minute window + sessionStorage lifetime)
  - Logs: Rotating file handler limits disk usage (5 MB × 3 backups)
  - Operation state: In-memory only during execution
  - Configuration: Persists until changed, contains no personal data
- **Purpose Limitation**: 
  - Logs used only for debugging, monitoring, and security analysis
  - Configuration used only to control operation behavior
  - No secondary use of collected data

### User Consent
- **Explicit Consent**: 
  - Initial token entry required via prompt() or URL hash
  - Clear explanation of token purpose in login dialog
  - Browser certificate warning requires explicit user action to proceed
- **Implied Consent**: 
  - Continued use constitutes acceptance of security model
  - Configuration changes via dialogs require explicit Save action
- **Withdrawal**: 
  - Closing browser tab/window revokes client-side token (sessionStorage cleared)
  - Stopping server invalidates all server-side tokens
  - Clearing browser data removes UI preferences

### Data Subject Rights (Conceptual)
While WebNC is not designed as a data processor/controller for personal data:
- **Access**: Users can view their own files through the interface
- **Rectification**: Users can modify/delete their own files via standard operations
- **Erasure**: Users can delete files permanently (no recycle bin)
- **Portability**: Users can copy files to other locations/media
- **Objection**: Users can choose not to use the software
- **Automation**: Not applicable (no automated decision-making)

## Audit and Accountability

### Logging Coverage
- **API Access**: All authenticated API calls logged at INFO level
- **Authentication Events**: Successes and failures logged
- **Security Events**: 
  - Invalid tokens logged as warnings
  - Replay attack attempts logged
  - Timestamp violations logged
  - Signature mismatches logged
- **System Events**: 
  - Server start/stop/shutdown
  - Certificate generation/renewal
  - Health check results
  - Operation queue status
- **Error Handling**:
  - All exception paths log at appropriate level (WARNING/ERROR)
  - No bare `except: pass` - all silent exception blocks upgraded to logging
  - Stack traces included for unexpected errors

### Log Integrity
- **Format**: Consistent, parseable format
- **Rotation**: Prevents unbounded growth (5 MB × 3 backups)
- **Encoding**: UTF-8 for international character support
- **Atomic Writes**: Logging library handles concurrent access safely
- **Timestamps**: ISO-compatible timestamps in local time

### Limitations
- **No Audit Log for File Operations**: Currently no persistent record of who performed what file operations
- **Log Retention**: Limited by rotation policy (approx. 15 MB total)
- **Real-time Alerting**: No built-in alerting on log events (planned)
- **Log Analysis**: No built-in log viewing/searching (requires external tools)

## Regulatory Alignment

### General Data Protection Regulation (GDPR) Considerations
While WebNC is not designed as a SaaS service processing personal data on behalf of others:
- **Data Minimization**: Aligns with Article 5(1)(c) - collects only what is necessary
- **Storage Limitation**: Aligns with Article 5(1)(e) - logs rotated, tokens ephemeral
- **Integrity and Confidentiality**: Aligns with Article 5(1)(f) - TLS encryption, secure authentication
- **Rights of Data Subject**: Users maintain direct control over their data through filesystem access
- **Security of Processing**: Aligns with Article 32 - encryption, confidentiality, resilience

### California Consumer Privacy Act (CCPA) Considerations
- **Right to Know**: Users can see what data is collected via logs and documentation
- **Right to Delete**: Users can delete their own data through normal file operations
- **Right to Opt-out**: Not applicable (no sale of personal information)
- **Non-Discrimination**: Equal access regardless of user characteristics

### Health Insurance Portability and Accountability Act (HIPAA) Considerations
- **Not Designed for PHI**: WebNC is not intended as a HIPAA-compliant system for handling Protected Health Information
- **Technical Safeguards**: 
  - Access control (authentication) aligns with §164.312(a)(1)
  - Audit controls partially implemented (API logging) aligns with §164.312(b)
  - Integrity controls (TLS) align with §164.312(c)(1)
  - Person or entity authentication aligns with §164.312(d)
- **Administrative Safeguards**: Would require additional policies and procedures
- **Physical Safeguards**: Depends on deployment environment

### Payment Card Industry Data Security Standard (PCI DSS) Considerations
- **Not Designed for Cardholder Data**: WebNC is not intended for processing, storing, or transmitting cardholder data
- **Relevant Requirements**:
  - Requirement 3: Protect stored cardholder data - Not applicable (designed not to store CHD)
  - Requirement 4: Encrypt transmission of cardholder data across open, public networks - TLS 1.3 implemented
  - Requirement 7: Restrict access to cardholder data by business need-to-know - Authentication framework supports
  - Requirement 8: Identify and authenticate access to system components - Multi-factor capable via extensible AuthProvider
  - Requirement 10: Track and monitor all access to network resources and cardholder data - API logging implemented
  - Requirement 12: Maintain a policy that addresses information security - Documentation provided

## Software Supply Chain Security

### Dependency Management
- **requirements.txt**: Lists all direct dependencies with version constraints
- **Transitive Dependencies**: Managed via pip's dependency resolution
- **Security Updates**: Recommended to regularly update dependencies
- **Known Vulnerabilities**: No known vulnerabilities in current dependency tree at time of release
- **Verification**: Dependencies obtained from official PyPI repository

### Build and Distribution
- **No Build Process**: Pure Python + static frontend (no compilation step)
- **Source Distribution**: Available as source code only
- **Reproducibility**: Exact versions specified in requirements.txt
- **Integrity**: No binary distribution - users build from source or run directly

### Development Practices
- **Dependency Scanning**: Recommended to use tools like `pip-audit` or `safety`
- **Version Control**: All changes tracked via Git
- **Code Review**: Changes should be reviewed before merging
- **Security Testing**: Regular security review recommended

## Compliance Declarations

### What WebNC Does
1. **Implements Transport Encryption**: TLS 1.3 with RSA-4096 certificates
2. **Uses Strong Authentication**: Zero-knowledge SHA-256 handshake with replay protection
3. **Minimizes Data Persistence**: Tokens ephemeral, logs rotated, no personal data stored
4. **Provides Access Controls**: Authentication required for sensitive operations
5. **Logs Security Events**: Authentication, errors, and system events logged
6. **Respects Filesystem Permissions**: No bypass of OS access controls
7. **Validates All Inputs**: Path sanitization and parameter validation
8. **Avoids Known Vulnerabilities**: No usage of weak cryptography or disabled security features
9. **Provides Clear Documentation**: Security model and limitations clearly disclosed
10. **Designed for Local Use**: Assumes trusted administrator/user context

### What WebNC Does Not Do
1. **Does Not Persist Authentication Tokens**: Tokens exist only in RAM and sessionStorage
2. **Does Not Transmit Secrets**: Only hashes are sent over the network
3. **Does Not Store Personal Data**: No collection of PII beyond what users choose to view/edit
4. **Does Not Bypass Filesystem Security**: Respects Windows permissions and ACLs
5. **Does Not Weaken Encryption**: Uses TLS 1.3 only, no fallback to older versions
6. **Does Not Use Hardcoded Credentials**: All secrets dynamically generated
7. **Does Not Log Sensitive Information**: Excludes tokens, file contents, passwords from logs
8. **Does Not Create Backdoors**: No undocumented access methods or hidden accounts
9. **Does Not Process Payment Card Data**: Not designed for PCI DSS environments
10. **Does Not Claim Unwarranted Certifications**: Makes no claims about GDPR/HIPAA/PCI compliance

## Recommended Complementary Controls

For organizations deploying WebNC in regulated environments:

### Network Controls
- **Segmentation**: Deploy in isolated management VLAN if possible
- **Firewall**: Restrict access to trusted IP ranges only
- **Intrusion Detection**: Monitor for anomalous access patterns
- **Proxy**: Consider reverse proxy with additional authentication (if needed)

### Host Controls
- **Least Privilege**: Run service account with minimal required permissions
- **Patch Management**: Keep OS and dependencies updated
- **Antivirus**: Exclude WebNC directories if necessary for performance (with risk acceptance)
- **Monitoring**: Track service health and resource utilization

### Administrative Controls
- **User Training**: Educate users on proper use and data handling
- **Procedures**: Establish clear procedures for sensitive operations
- **Monitoring**: Regular review of logs for anomalous activity
- **Incident Response**: Have plan for security incidents involving WebNC
- **Backup**: Backup configuration and critical data separately

### Technical Controls
- **Certificate Management**: Replace auto-generated cert with CA-signed certificate for production
- **Authentication Enhancement**: Consider implementing AD/LDAP providers for enterprise environments
- **Audit Enhancement**: Plan to implement persistent audit log for file operations (future feature)
- **Data Loss Prevention**: Consider DLP rules for sensitive data exfiltration
- **Encryption at Rest**: Use BitLocker or similar for disk encryption if required

## Limitations and Exceptions

### Known Limitations
1. **No Persistent Audit Trail**: File operations are not logged for audit purposes
2. **Ephemeral Authentication**: Requires re-authentication on each server start
3. **Local-first Design**: Not optimized for multi-user collaboration without additional controls
4. **Windows-centric**: Current implementation relies on Windows-specific APIs
5. **No DLP Integration**: No built-in data loss prevention controls
6. **Session Sharing**: Tokens not designed for sharing between users or sessions

### Exceptions and Mitigations
- **Self-signed Certificates**: 
  - Exception: Uses self-signed certificate by default
  - Mitigation: Replace with CA-signed certificate in production; valid for local/trusted use
- **Browser Storage for Token**:
  - Exception: Stores token in sessionStorage (browser-side)
  - Mitigation: Limited lifetime, cleared on tab close, never transmitted
- **Log Rotation Limit**:
  - Exception: Logs rotated at 5 MB (may lose older logs)
  - Mitigation: Sufficient for debugging/monitoring; external log aggregation recommended for long-term retention
- **No Operation Cancelling**:
  - Exception: Currently no way to cancel running operations
  - Mitigation: Use timeouts appropriately; planned feature for future releases

## Version and Applicability
- **Document Version**: 1.0.0
- **Applicable Version**: WebNC 1.0.0 (as documented in History.md)
- **Review Frequency**: Should be reviewed with each major release
- **Last Updated**: Corresponds to latest commit in repository
- **Feedback**: Report inaccuracies or concerns via project issue tracker

## Conclusion
WebNC implements a robust security model appropriate for its intended use as a local-first, keyboard-driven file manager for Windows administrators. While not designed as a compliant system for handling regulated data in multi-tenant environments, it provides strong foundational security controls that can be complemented with organizational policies and technical controls to meet various compliance requirements.

The three-layer security approach (TLS, session auth, provider interface) provides defense in depth, and the minimization of persistent sensitive data reduces the attack surface. Organizations should evaluate WebNC against their specific compliance requirements and implement additional controls as necessary.

For the most current information, please refer to the `History.md` file which contains detailed development progress including any security-related changes.