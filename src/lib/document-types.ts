import type { DocumentTypeKey } from "@/lib/contracts";

/** Mirrors backend/app/doctypes.py (also served at GET /api/document-types). */
export const DOCUMENT_TYPES: Array<{ key: DocumentTypeKey; label: string; description: string }> = [
  {
    key: "specification",
    label: "Technical specification",
    description: "Technical specification or requirements section.",
  },
  {
    key: "tender",
    label: "Tender document",
    description: "Complete tender / NIT with bidding and commercial sections.",
  },
  {
    key: "boq",
    label: "Bill of quantities",
    description: "Schedule of quantities with item descriptions — read in full, including tables.",
  },
  {
    key: "datasheet",
    label: "Vendor datasheet",
    description: "Manufacturer datasheet or guaranteed technical particulars.",
  },
  {
    key: "test_report",
    label: "Test report",
    description: "Type, routine or laboratory test report.",
  },
  {
    key: "inspection_report",
    label: "Inspection report",
    description: "Site or pre-dispatch inspection report.",
  },
  { key: "other", label: "Other", description: "Any other document — name its type." },
];
