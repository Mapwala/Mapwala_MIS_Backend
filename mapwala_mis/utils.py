# mapwala_mis/utils.py
from django.db import transaction
from django.utils import timezone
from .models import NoteSequence, QuotationSequence


# ---------------- Note Number Generator ----------------
def generate_note_number(note_type: str) -> str:
    """
    Thread-safe, concurrency-safe note number generator.
    Format:
        Debit  → DN-YYYY-001
        Credit → CN-YYYY-001
    """
    year = timezone.now().year

    with transaction.atomic():
        seq, _ = NoteSequence.objects.select_for_update().get_or_create(
            year=year,
            note_type=note_type,
            defaults={"last_number": 0},
        )

        seq.last_number += 1
        seq.save(update_fields=["last_number"])

        prefix = "DN" if note_type == "debit" else "CN"
        return f"{prefix}-{year}-{seq.last_number:03d}"


# --------- Quotation Number Generator ---------
def generate_quotation_number() -> str:
    """
    Thread-safe, concurrency-safe quotation number generator.
    Format: QT-YYYY-001
    """
    year = timezone.now().year

    with transaction.atomic():
        seq, _ = QuotationSequence.objects.select_for_update().get_or_create(
            year=year,
            defaults={"last_number": 0},
        )

        seq.last_number += 1
        seq.save(update_fields=["last_number"])

        return f"QT-{year}-{seq.last_number:03d}"


def format_order_id(order):
    """Returns 'ORD001' style label from OrderEntry instance."""
    return f"ORD{order.id:03d}"


def get_media_path(file):
    return f"media/{file.name}" if file else None
