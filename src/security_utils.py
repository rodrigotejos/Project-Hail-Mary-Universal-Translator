"""
Security and validation utility module for Universal Translator.
Enforces OWASP Top 10 and AI-DLC Security Baseline constraints.
"""
import os
import re
import unicodedata
from typing import Optional

SAFE_IDENTIFIER_REGEX = re.compile(r'^[a-zA-Z0-9_\-]+$')
SAFE_WORD_REGEX = re.compile(r'^[a-zA-Z0-9_\-\s]+$')

MAX_IDENTIFIER_LENGTH = 64
MAX_WORD_LENGTH = 128
MAX_MESSAGE_LENGTH = 1000


class SecurityError(Exception):
    """Exception raised for security policy violations."""
    pass


def sanitize_filename(filename: str, max_length: int = MAX_WORD_LENGTH) -> str:
    """
    Sanitizes a file name preserving case, stripping path traversal characters,
    null bytes, and hazardous symbols.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string.")
    
    normalized = unicodedata.normalize('NFKC', filename).strip()
    cleaned = normalized.replace('\x00', '').replace('/', '').replace('\\', '').replace('..', '')
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned)
    cleaned = cleaned.strip('._-')
    
    if not cleaned:
        raise ValueError(f"Filename '{filename}' contains no valid characters.")
        
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        
    return cleaned


def sanitize_identifier(name: str, max_length: int = MAX_IDENTIFIER_LENGTH) -> str:
    """
    Sanitize an identifier (e.g. language name, category) to prevent Path Traversal,
    Command Injection, and filesystem anomalies.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Identifier must be a non-empty string.")
    
    normalized = unicodedata.normalize('NFKC', name).strip()
    cleaned = normalized.replace('\x00', '').replace('/', '').replace('\\', '').replace('..', '')
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', cleaned)
    cleaned = cleaned.strip('._-')
    
    if not cleaned:
        raise ValueError(f"Identifier '{name}' contains no valid characters.")
        
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        
    return cleaned.lower()


def sanitize_word_key(word: str, max_length: int = MAX_WORD_LENGTH) -> str:
    """
    Sanitize word keys for dictionaries and file naming.
    """
    if not word or not isinstance(word, str):
        raise ValueError("Word must be a non-empty string.")
        
    normalized = unicodedata.normalize('NFKC', word).strip()
    cleaned = normalized.replace('\x00', '').replace('/', '').replace('\\', '').replace('..', '')
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\s]', '', cleaned)
    cleaned = re.sub(r'\s+', '_', cleaned).strip('._-')
    
    if not cleaned:
        raise ValueError(f"Word '{word}' contains no valid characters.")
        
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        
    return cleaned.upper()


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Verify if target_path is strictly within base_dir (prevents Path Traversal).
    """
    try:
        base_abs = os.path.abspath(base_dir)
        target_abs = os.path.abspath(target_path)
        common = os.path.commonpath([base_abs, target_abs])
        return common == base_abs
    except Exception:
        return False


def resolve_safe_filepath(base_dir: str, language: str, filename_or_word: str, extension: str = ".wav") -> str:
    """
    Safely resolve a file path within a language subdirectory, guaranteeing containment.
    """
    clean_lang = sanitize_identifier(language)
    clean_name = sanitize_filename(filename_or_word)
    if clean_name.endswith(extension):
        clean_name = clean_name[:-len(extension)]
    
    lang_dir = os.path.join(base_dir, clean_lang)
    os.makedirs(lang_dir, exist_ok=True)
    
    safe_path = os.path.join(lang_dir, f"{clean_name}{extension}")
    if not is_safe_path(base_dir, safe_path):
        raise SecurityError(f"Path traversal detected: {safe_path} is outside {base_dir}")
        
    return safe_path
