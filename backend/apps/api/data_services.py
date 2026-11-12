from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

MAX_ROWS = 20_000
MAX_COLUMNS = 100
MAX_XLSX_UNCOMPRESSED_BYTES = 80 * 1024 * 1024
MAX_XLSX_ARCHIVE_ENTRIES = 500
METRIC_BY_REPORT = {
    "SALES": "reported_revenue",
    "CASH": "reported_collections",
    "BANK": "reported_cash_balance",
    "EXPENSES": "reported_expenses",
    "RECEIVABLES": "reported_receivables",
    "PAYABLES": "reported_payables",
    "OTHER": "reported_other_amount",
}
METRIC_LABELS = {
    "reported_revenue": "Chiffre d’affaires rapporté",
    "reported_collections": "Encaissements rapportés",
    "reported_cash_balance": "Solde de trésorerie déclaré",
    "reported_expenses": "Dépenses rapportées",
    "reported_receivables": "Créances clients",
    "reported_payables": "Dettes fournisseurs",
    "reported_other_amount": "Autre montant rapporté",
}


def read_tabular_file(path: str, filename: str) -> tuple[list[str], list[dict[str, str]]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        raw = Path(path).read_bytes()
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("cp1252")
        sample = content[:8192]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(content), dialect=dialect)
        headers = [(h or "").strip() for h in (reader.fieldnames or [])]
        if not headers or len(headers) > MAX_COLUMNS:
            raise ValueError("En-têtes absents ou nombre de colonnes trop élevé.")
        rows = []
        for index, row in enumerate(reader, start=2):
            if index > MAX_ROWS + 1:
                raise ValueError(f"Limite de {MAX_ROWS} lignes dépassée.")
            rows.append({str(k or "").strip(): str(v or "").strip() for k, v in row.items() if k is not None})
        return headers, rows
    if suffix == ".xlsx":
        # XLSX is a ZIP container. Bound expansion and entry count before parsing
        # to reduce zip-bomb and excessive shared-string/XML risks.
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_XLSX_ARCHIVE_ENTRIES:
                    raise ValueError("Le classeur contient trop d’éléments internes.")
                uncompressed_size = sum(item.file_size for item in entries)
                if uncompressed_size > MAX_XLSX_UNCOMPRESSED_BYTES:
                    raise ValueError("Le classeur dépasse la limite de décompression autorisée.")
                for item in entries:
                    normalized_name = item.filename.replace("\\", "/")
                    parts = normalized_name.split("/")
                    if normalized_name.startswith("/") or any(part == ".." for part in parts):
                        raise ValueError("Le classeur contient un chemin interne non autorisé.")
        except (zipfile.BadZipFile, InvalidFileException, KeyError, OSError) as exc:
            raise ValueError("Classeur XLSX invalide.") from exc
        workbook = load_workbook(path, read_only=True, data_only=False)
        try:
            sheet = workbook.active
            iterator = sheet.iter_rows()
            first = next(iterator, None)
            headers = [str(cell.value).strip() if cell.value is not None else "" for cell in (first or [])]
            while headers and not headers[-1]:
                headers.pop()
            if not headers or len(headers) > MAX_COLUMNS:
                raise ValueError("En-têtes absents ou nombre de colonnes trop élevé.")
            rows = []
            for index, cells in enumerate(iterator, start=2):
                if index > MAX_ROWS + 1:
                    raise ValueError(f"Limite de {MAX_ROWS} lignes dépassée.")
                row = {}
                for col, cell in zip(headers, cells):
                    value = cell.value
                    if cell.data_type == "f" or (isinstance(value, str) and value.lstrip().startswith("=")):
                        raise ValueError(
                            "Les cellules contenant des formules ne sont pas importées. "
                            "Convertis-les en valeurs dans une copie du fichier avant l’import."
                        )
                    if isinstance(value, (date, datetime)):
                        row[col] = value.isoformat()
                    else:
                        row[col] = "" if value is None else str(value).strip()
                if any(row.values()):
                    rows.append(row)
            return headers, rows
        finally:
            workbook.close()
    raise ValueError("Le parsing tabulaire accepte CSV et XLSX. Le PDF est disponible en extraction textuelle assistée.")


def parse_decimal(raw: str, *, allow_negative: bool = False) -> Decimal:
    value = str(raw).strip().replace("\u00a0", "").replace(" ", "")
    value = re.sub(r"[^0-9,.-]", "", value)
    if not value or value in {"-", ".", ","}:
        raise InvalidOperation
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        # One or two trailing digits are interpreted as decimal separators.
        tail = value.rsplit(",", 1)[-1]
        value = value.replace(",", ".") if len(tail) <= 2 else value.replace(",", "")
    amount = Decimal(value)
    if not amount.is_finite() or (amount < 0 and not allow_negative):
        raise InvalidOperation
    return amount.quantize(Decimal("0.000001"))


def parse_source_date(raw: str) -> date:
    value = str(raw).strip()
    if not value:
        raise ValueError("date absente")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError("date non reconnue") from exc
