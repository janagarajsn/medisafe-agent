"""Tests for Fernet-based encryption layer."""

import pytest
from src.security.encryption import encrypt, decrypt


def test_roundtrip_basic():
    plaintext = "Lisinopril 10mg"
    assert decrypt(encrypt(plaintext)) == plaintext


def test_empty_string_passthrough():
    assert encrypt("") == ""
    assert decrypt("") == ""


def test_ciphertext_differs_from_plaintext():
    plaintext = "Metformin 500mg"
    assert encrypt(plaintext) != plaintext


def test_two_encryptions_differ():
    # Fernet includes a random IV so same input → different ciphertext each time
    plaintext = "Atorvastatin 20mg"
    enc1 = encrypt(plaintext)
    enc2 = encrypt(plaintext)
    assert enc1 != enc2
    assert decrypt(enc1) == plaintext
    assert decrypt(enc2) == plaintext


def test_special_characters():
    plaintext = "Ibuprofen 400mg — take with food! (3× daily) & water"
    assert decrypt(encrypt(plaintext)) == plaintext


def test_unicode():
    plaintext = "Médicament 250μg"
    assert decrypt(encrypt(plaintext)) == plaintext


def test_tampered_ciphertext_raises():
    from cryptography.fernet import InvalidToken
    enc = encrypt("safe text")
    tampered = enc[:-4] + "XXXX"
    with pytest.raises(Exception):  # InvalidToken or binascii.Error
        decrypt(tampered)
