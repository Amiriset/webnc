import os
import sys
import time
import struct
import socket
import secrets
import hashlib
import hmac
import base64
import winreg
import logging
import ctypes
import json
from threading import Lock
from pathlib import Path
from typing import Optional, List
from fastapi import Request
from cryptography.fernet import Fernet

# Жесткий платформенный guard на этапе импорта модуля
if sys.platform != "win32":
    raise RuntimeError("CRITICAL: WebNC cryptographic core requires Microsoft Windows. WinAPI bindings unavailable.")

logger = logging.getLogger("nc_server.crypto")

V3_VERSION_BYTE = b'\x03'
SALT_LEN = 32
KEY_LEN = 32
KDF_SALT_LEN = 16
RECOVERY_KEY_LEN = 20  # байт -> ~27 символов Base32

TRUSTED_PROXIES: List[str] = ["127.0.0.1", "::1"]

# Глобальный атомарный кэш MasterKey (Pepper) в памяти процесса
_PEPPER_KEY_CACHE: Optional[bytes] = None

# Слой хранения Rate Limit с автоматическим TTL и защитой потокобезопасности
LOGIN_TRACKER = {}
_LOGIN_TRACKER_LOCK = Lock()
CLEANUP_INTERVAL = 3600
LAST_CLEANUP_TIME = time.time()


def _format_smbios_uuid(b: bytes) -> str:
    """Форматирует 16 байт в RFC 4122 UUID с учетом Little-Endian в SMBIOS spec 2.6+."""
    time_low = int.from_bytes(b[0:4], 'little')
    time_mid = int.from_bytes(b[4:6], 'little')
    time_hi  = int.from_bytes(b[6:8], 'little')
    clock    = b[8:10].hex().upper()
    node     = b[10:16].hex().upper()
    return f"{time_low:08X}-{time_mid:04X}-{time_hi:04X}-{clock}-{node}"


def _parse_smbios_uuid(data: bytes) -> str:
    """Защищенный парсер UUID из структуры SMBIOS Type 1 (System Information)."""
    total_len = len(data)
    if total_len <= 8:
        raise RuntimeError("CRITICAL: SMBIOS buffer is too small to contain valid firmware data.")
        
    offset = 8  # Пропускаем 8-байтный заголовок RawSMBIOSData Windows
    
    while offset < total_len:
        if offset + 2 > total_len:
            break
            
        struct_type = data[offset]
        struct_len = data[offset + 1]
        
        if struct_len < 2:
            raise RuntimeError("CRITICAL: Corrupted SMBIOS structure length detected (< 2).")
            
        if struct_type == 1:
            if struct_len >= 0x19:
                uuid_offset = offset + 8
                if uuid_offset + 16 <= total_len:
                    uuid_bytes = data[uuid_offset:uuid_offset + 16]
                    if any(uuid_bytes) and uuid_bytes != b'\xff' * 16:
                        return _format_smbios_uuid(uuid_bytes)
                        
        offset += struct_len
        while offset < total_len - 1:
            if data[offset] == 0 and data[offset + 1] == 0:
                offset += 2
                break
            offset += 1
        else:
            offset += 1
            
    raise RuntimeError("CRITICAL: Valid SMBIOS Type 1 (System Information) UUID not found.")


def get_hardware_fingerprint() -> str:
    """Собирает чистый аппаратный отпечаток хоста на базе WinAPI GetSystemFirmwareTable и реестра."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            machine_guid = str(guid).strip()
    except Exception as e:
        raise RuntimeError(f"CRITICAL: System Registry access failed. MachineGuid unreadable: {e}")

    firmware_table_provider = 0x52534D42  # 'RSMB' в LE
    kernel32 = ctypes.windll.kernel32
    kernel32.GetSystemFirmwareTable.restype = ctypes.c_uint32
    kernel32.GetSystemFirmwareTable.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32
    ]
    
    size = kernel32.GetSystemFirmwareTable(firmware_table_provider, 0, None, 0)
    if size == 0:
        raise RuntimeError("CRITICAL: GetSystemFirmwareTable returned 0 size buffer.")
        
    buf = (ctypes.c_uint8 * size)()
    result = kernel32.GetSystemFirmwareTable(firmware_table_provider, 0, buf, size)
    if result == 0:
        raise RuntimeError("CRITICAL: GetSystemFirmwareTable failed to populate firmware buffer.")
        
    smbios_uuid = _parse_smbios_uuid(bytes(buf))
    return f"{machine_guid}:{smbios_uuid}"


def generate_recovery_key() -> str:
    """Генерирует Recovery Key в читаемом формате WNC3-XXXX-XXXX-XXXX-XXXX."""
    raw = secrets.token_bytes(RECOVERY_KEY_LEN)
    encoded = base64.b32encode(raw).decode('utf-8')
    groups = [encoded[i:i+4] for i in range(0, len(encoded), 4)]
    return "WNC3-" + "-".join(groups)


def derive_master_key(machine_fingerprint: str, recovery_key: str, kdf_salt: bytes) -> bytes:
    """Собирает MasterKey (Pepper) из двух независимых факторов через Scrypt KDF."""
    combined = f"{machine_fingerprint}:{recovery_key}:WebNC-Master-2026".encode('utf-8')
    raw_key = hashlib.scrypt(
        password=combined,
        salt=kdf_salt,
        n=16384, r=8, p=1,
        maxmem=32 * 1024 * 1024,
        dklen=32
    )
    return base64.urlsafe_b64encode(raw_key)


def init_crypto_store(secrets_path: Path) -> str:
    """Первичная инициализация: создает соль, генерирует Recovery Key и считает HMAC-маркер верификации."""
    recovery_key = generate_recovery_key()
    kdf_salt = secrets.token_bytes(KDF_SALT_LEN)
    
    # Считаем маркер проверки для реализации Fail-Fast при вводе ключа
    fingerprint = get_hardware_fingerprint()
    master_key = derive_master_key(fingerprint, recovery_key, kdf_salt)
    verification_tag = hmac.new(master_key, b"WebNC-Vault-Verify-Tag-2026", 'sha256').hexdigest()
    
    store = {
        "kdf_salt": base64.b64encode(kdf_salt).decode('utf-8'),
        "vault_verify": verification_tag,
        "schema_version": "v3",
        "username": "admin",
        "password_hash": "__UNSET__"  # Заменяем пустую строку на жесткий маркер неинициализированности
    }
    secrets_path.write_text(json.dumps(store, indent=4), encoding='utf-8')
    return recovery_key


def unlock_vault(recovery_key: str, secrets_path: Path) -> bool:
    """Вызывается при старте сервера. Реализует Fail-Fast верификацию Recovery Key."""
    global _PEPPER_KEY_CACHE
    try:
        store = json.loads(secrets_path.read_text(encoding='utf-8'))
        kdf_salt = base64.b64decode(store["kdf_salt"])
        expected_tag = store.get("vault_verify")
        if not expected_tag:
            raise RuntimeError("CRITICAL: vault_verify tag missing. Secrets file may be corrupted or pre-v3.")
            
        fingerprint = get_hardware_fingerprint()
        computed_master_key = derive_master_key(fingerprint, recovery_key, kdf_salt)
        
        # Проверяем ключ с помощью HMAC-тега за константное время
        actual_tag = hmac.new(computed_master_key, b"WebNC-Vault-Verify-Tag-2026", 'sha256').hexdigest()
        if not secrets.compare_digest(str(expected_tag), actual_tag):
            logger.error("VAULT_UNLOCK_FAILED: Cryptographic signature mismatch. Invalid recovery key or hardware diff.")
            return False
            
        _PEPPER_KEY_CACHE = computed_master_key
        logger.info("VAULT_UNLOCKED: Master key derived natively via WinAPI and safely cached. Server ready.")
        return True
    except Exception as e:
        logger.error(f"VAULT_UNLOCK_FAILED: Unexpected storage read failure: {e}")
        return False


def get_machine_bound_pepper() -> bytes:
    """Возвращает прогретый кэш ключа. Защита от CPU Exhaustion атак."""
    if _PEPPER_KEY_CACHE is None:
        raise RuntimeError("CRITICAL: Cryptographic engine is cold. Vault must be unlocked before serving requests.")
    return _PEPPER_KEY_CACHE


def get_client_ip(request: Request) -> str:
    """Исправлено: Безопасно извлекает IP с защитой от спуфинга и корректным строковым методом strip()."""
    raw_client_ip = request.client.host
    if raw_client_ip in TRUSTED_PROXIES:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()  # Исправлен баг: добавлен индекс [0] перед .strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return raw_client_ip


def check_rate_limit(ip: str) -> bool:
    """Исправлено: Добавлена потокобезопасная блокировка Lock на операции с LOGIN_TRACKER."""
    global LAST_CLEANUP_TIME
    now = time.time()
    
    with _LOGIN_TRACKER_LOCK:
        if now - LAST_CLEANUP_TIME > CLEANUP_INTERVAL:
            expired_ips = [k for k, v in LOGIN_TRACKER.items() if now - v["last_seen"] > 86400]
            for k in expired_ips:
                del LOGIN_TRACKER[k]
            LAST_CLEANUP_TIME = now

        if ip not in LOGIN_TRACKER:
            LOGIN_TRACKER[ip] = {"attempts": 0, "locked_until": 0.0, "last_seen": now}
            return True
            
        record = LOGIN_TRACKER[ip]
        record["last_seen"] = now
        if record["locked_until"] > now:
            return False
        if record["locked_until"] > 0 and now >= record["locked_until"]:
            record["attempts"] = 0
            record["locked_until"] = 0.0
        return True


def register_failed_attempt(ip: str):
    with _LOGIN_TRACKER_LOCK:
        if ip in LOGIN_TRACKER:
            LOGIN_TRACKER[ip]["attempts"] += 1
            if LOGIN_TRACKER[ip]["attempts"] >= 5:
                LOGIN_TRACKER[ip]["locked_until"] = time.time() + 900


def register_successful_attempt(ip: str):
    with _LOGIN_TRACKER_LOCK:
        if ip in LOGIN_TRACKER:
            LOGIN_TRACKER[ip]["attempts"] = 0
            LOGIN_TRACKER[ip]["locked_until"] = 0.0


def encode_password_v3(raw_password: str) -> str:
    """Запечатывает пароль в бинарный 68-байтный payload на базе прогретого Pepper."""
    if not raw_password:
        raise ValueError("Password cannot be empty")
        
    salt = secrets.token_bytes(SALT_LEN)
    dynamic_iterations = secrets.randbelow(300000) + 600000
    
    pbkdf2_hash = hashlib.pbkdf2_hmac(
        'sha256', raw_password.encode('utf-8'), salt, dynamic_iterations, KEY_LEN
    )
    
    binary_payload = struct.pack("!I32s32s", dynamic_iterations, salt, pbkdf2_hash)    
    pepper_key = get_machine_bound_pepper()
    fernet = Fernet(pepper_key)
    encrypted_bytes = fernet.encrypt(binary_payload)
    final_container = V3_VERSION_BYTE + encrypted_bytes
    return base64.urlsafe_b64encode(final_container).decode('utf-8')
    
def matches_password_v3(raw_password: str, stored_string: str) -> bool:
    """Исправлено: stack-trace заменен на предупреждение warning; добавлен явный return False в финале."""
    if not raw_password or not stored_string or stored_string == "__UNSET__":
        return False

    try:
        raw_container = base64.urlsafe_b64decode(stored_string.encode('utf-8'))
        version_byte = raw_container[0:1]
        encrypted_payload = raw_container[1:]
        if version_byte != V3_VERSION_BYTE:
            logger.warning("AUTH_DECODE: Unsupported container version format.")
            return False
        pepper_key = get_machine_bound_pepper()
        fernet = Fernet(pepper_key)
        binary_payload = fernet.decrypt(encrypted_payload)
        dynamic_iterations, salt, expected_hash = struct.unpack("!I32s32s", binary_payload)
        attempted_hash = hashlib.pbkdf2_hmac(
            'sha256', raw_password.encode('utf-8'), salt, dynamic_iterations, KEY_LEN
        )
        return secrets.compare_digest(expected_hash, attempted_hash)
    except Exception as e:
        logger.warning(f"AUTH_EXCEPTION: Password verification failed due to data/key corruption: {type(e).__name__}")
    return False



