import pandas as pd
from faker import Faker
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def fake_cccd() -> str:
    return fake.numerify("############")


def fake_vn_phone() -> str:
    return "0" + fake.random_element(elements=("3", "5", "7", "8", "9")) + fake.numerify("########")


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize detected PII in a single text value.

        Supported strategies:
        - replace: replace PII with fake values.
        - mask: mask detected PII characters.
        - hash: replace detected PII with a SHA-256 hash.
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return str(text)

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": fake_vn_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "DEFAULT": OperatorConfig(
                    "mask",
                    {"masking_char": "*", "chars_to_mask": 100, "from_end": False},
                )
            }
        elif strategy == "hash":
            operators = {
                "DEFAULT": OperatorConfig(
                    "hash",
                    {
                        "hash_type": "sha256",
                        "salt": "medviet-task2-salt",
                    },
                )
            }
        else:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")

        anonymized = self.anonymizer.anonymize(
            text=str(text),
            analyzer_results=results,
            operators=operators,
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize patient-level PII while preserving model-useful columns.

        patient_id is kept as the pseudonymous identifier. benh,
        ket_qua_xet_nghiem, and ngay_kham are kept for analytics/training.
        """
        df_anon = df.copy()

        if "ho_ten" in df_anon:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "bac_si_phu_trach" in df_anon:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "email" in df_anon:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon:
            df_anon["dia_chi"] = [fake.address().replace("\n", ", ") for _ in range(len(df_anon))]
        if "cccd" in df_anon:
            df_anon["cccd"] = [fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon:
            df_anon["so_dien_thoai"] = [fake_vn_phone() for _ in range(len(df_anon))]
        if "ngay_sinh" in df_anon:
            df_anon["ngay_sinh"] = [
                fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%d/%m/%Y")
                for _ in range(len(df_anon))
            ]

        return df_anon

    def calculate_detection_rate(self, original_df: pd.DataFrame, pii_columns: list) -> float:
        """
        Calculate the share of cells in pii_columns with at least one detected entity.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
