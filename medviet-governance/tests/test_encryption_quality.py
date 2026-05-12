import json

import pandas as pd

from src.encryption.vault import SimpleVault
from src.pii.anonymizer import MedVietAnonymizer
from src.quality.validation import validate_anonymized_data


def test_encryption_round_trip(tmp_path):
    vault = SimpleVault(master_key_path=str(tmp_path / ".vault_key"))
    original = "Nguyen Van A - CCCD: 012345678901"

    encrypted = vault.encrypt_data(original)
    assert encrypted["algorithm"] == "AES-256-GCM"
    assert original not in json.dumps(encrypted)
    assert vault.decrypt_data(encrypted) == original


def test_encrypt_column_replaces_plaintext(tmp_path):
    vault = SimpleVault(master_key_path=str(tmp_path / ".vault_key"))
    df = pd.DataFrame({"cccd": ["012345678901"]})

    encrypted_df = vault.encrypt_column(df, "cccd")

    assert encrypted_df.loc[0, "cccd"] != "012345678901"
    payload = json.loads(encrypted_df.loc[0, "cccd"])
    assert vault.decrypt_data(payload) == "012345678901"


def test_validate_anonymized_data_success(tmp_path):
    raw_df = pd.read_csv("data/raw/patients_raw.csv")
    anonymized_df = MedVietAnonymizer().anonymize_dataframe(raw_df)
    output_path = tmp_path / "patients_anonymized.csv"
    anonymized_df.to_csv(output_path, index=False)

    result = validate_anonymized_data(str(output_path))

    assert result["success"] is True
    assert result["failed_checks"] == []
    assert result["stats"]["total_rows"] == len(raw_df)
