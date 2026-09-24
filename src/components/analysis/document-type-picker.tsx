import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DocumentTypeKey } from "@/lib/contracts";
import { DOCUMENT_TYPES } from "@/lib/document-types";

export type DocumentTypeValue = { documentType: DocumentTypeKey; documentTypeLabel: string };

/** Choose what a document is; "Other" asks for a name of the user's own type. */
export function DocumentTypePicker({
  value,
  onChange,
  id = "document-type",
}: {
  value: DocumentTypeValue;
  onChange: (value: DocumentTypeValue) => void;
  id?: string;
}) {
  const selected = DOCUMENT_TYPES.find((t) => t.key === value.documentType);
  return (
    <div className="grid gap-3 sm:grid-cols-[16rem_minmax(0,1fr)] sm:items-start">
      <div>
        <label
          htmlFor={id}
          className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground"
        >
          Document type
        </label>
        <Select
          value={value.documentType}
          onValueChange={(documentType) =>
            onChange({
              documentType: documentType as DocumentTypeKey,
              documentTypeLabel: value.documentTypeLabel,
            })
          }
        >
          <SelectTrigger id={id} className="mt-2 w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DOCUMENT_TYPES.map((t) => (
              <SelectItem key={t.key} value={t.key}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {value.documentType === "other" ? (
        <div>
          <label
            htmlFor={`${id}-label`}
            className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground"
          >
            Name this type
          </label>
          <Input
            id={`${id}-label`}
            className="mt-2"
            maxLength={60}
            value={value.documentTypeLabel}
            placeholder="e.g. Consultant review note"
            onChange={(e) => onChange({ documentType: "other", documentTypeLabel: e.target.value })}
          />
        </div>
      ) : (
        <p className="text-xs leading-5 text-muted-foreground sm:mt-7">{selected?.description}</p>
      )}
    </div>
  );
}
