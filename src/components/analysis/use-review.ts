import { useRouter } from "@tanstack/react-router";
import { toast } from "sonner";
import type {
  DocumentAnalysis,
  Finding,
  Repair,
  RepairStatus,
  ReviewStatus,
} from "@/lib/contracts";
import { decideRepair, reviewFinding } from "@/services/analysis";

/** Review callbacks that persist decisions (or explain that demo decisions are not saved). */
export function useReviewActions(docs: Array<Pick<DocumentAnalysis, "id" | "persisted">>) {
  const router = useRouter();
  const docFor = (documentId: string | undefined) =>
    docs.find((d) => d.id === documentId) ?? docs[0] ?? { persisted: false };

  const onReview = async (finding: Finding, status: ReviewStatus, note: string) => {
    try {
      const saved = await reviewFinding(docFor(finding.documentId), finding.id, status, note);
      toast.success(
        saved
          ? `Finding ${status === "open" ? "reopened" : status}. Recorded in the audit trail.`
          : "Demo workspace: decision shown but not saved.",
      );
      if (saved) await router.invalidate();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not record the decision.");
      throw error;
    }
  };

  const onDecide = async (repair: Repair, decision: RepairStatus, text?: string) => {
    try {
      const saved = await decideRepair(docFor(docs[0]?.id), repair.id, decision, text);
      if (!saved) toast.message("Demo workspace: decision shown but not saved.");
      else if (decision !== "pending")
        toast.success(`Repair ${decision}. Recorded in the audit trail.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not record the decision.");
      throw error;
    }
  };

  return { onReview, onDecide };
}
