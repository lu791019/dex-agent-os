
# Invoice Organizer

Transforms chaotic folders of invoices, receipts, and financial documents into a clean, tax-ready filing system.

## What This Skill Does

1. **Reads invoice content**: Extracts vendor, date, amount, invoice number, description from PDFs, images, and documents
2. **Renames consistently**: `YYYY-MM-DD Vendor - Invoice - Description.ext`
3. **Organizes by category**: By vendor, expense type, time period, or tax category
4. **Generates summary**: CSV with all invoice details for accountants

## Supported Formats

PDF invoices, scanned receipts (JPG, PNG), email attachments, screenshots, bank statements.

## Quick Usage

```
Organize these invoices for taxes
```

Or more specifically:
```
Read all invoices in this folder, rename them to
"YYYY-MM-DD Vendor - Invoice - Product.pdf" format,
and organize them by vendor
```

## Reference Files

- **`references/workflow.md`** — 7-step organization process: scan, extract info, choose strategy, rename, execute, generate CSV, summarize. Load when organizing invoices.
- **`references/examples-patterns.md`** — Real examples (tax prep, monthly reconciliation, multi-year archive, email cleanup), common folder patterns, pro tips, special cases (missing info, duplicates, multi-page). Load for reference and edge cases.
