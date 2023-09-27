def deobfuscate(guid: str, data: bytes) -> bytes:
    """Deobfuscate a .odttf font file's header using its GUID."""

    guid = guid.strip("{}").replace("-", "")
    guid = bytes.fromhex(guid)[::-1]

    # GUID repeated to make 32 bytes
    key = guid * 2

    # First 32 bytes are obfuscated
    obfuscated_header = data[:32]

    # XOR to deobfuscate the header
    deobfuscated_header = bytes(b ^ k for b, k in zip(obfuscated_header, key))

    # Append remaining bytes (non-obfuscated)
    return deobfuscated_header + data[32:]
