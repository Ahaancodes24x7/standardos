CREATE TABLE "analysis_runs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"document_id" uuid NOT NULL,
	"owner_id" uuid NOT NULL,
	"status" text DEFAULT 'queued' NOT NULL,
	"stage" integer DEFAULT 0 NOT NULL,
	"stage_name" text,
	"attempts" integer DEFAULT 0 NOT NULL,
	"error" text,
	"error_code" text,
	"pipeline_version" text,
	"corpus_version" text,
	"llm_model" text,
	"parser" text,
	"page_count" integer,
	"extracted_text" text,
	"warnings" jsonb,
	"readiness" integer,
	"readiness_detail" jsonb,
	"applicable_standard_ids" jsonb,
	"graph" jsonb,
	"timings" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"started_at" timestamp with time zone,
	"heartbeat_at" timestamp with time zone,
	"finished_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "audit_events" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"actor_id" uuid,
	"document_id" uuid,
	"entity_type" text NOT NULL,
	"entity_id" text NOT NULL,
	"action" text NOT NULL,
	"before" jsonb,
	"after" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "corpus_versions" (
	"version" text PRIMARY KEY NOT NULL,
	"source" text NOT NULL,
	"standard_count" integer NOT NULL,
	"relationship_count" integer NOT NULL,
	"loaded_at" timestamp with time zone DEFAULT now() NOT NULL,
	"is_active" boolean DEFAULT false NOT NULL
);
--> statement-breakpoint
CREATE TABLE "documents" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"owner_id" uuid NOT NULL,
	"name" text NOT NULL,
	"organization" text NOT NULL,
	"source_format" text NOT NULL,
	"filename" text,
	"mime_type" text,
	"byte_size" integer NOT NULL,
	"sha256" text NOT NULL,
	"original" "bytea",
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "evidence" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"finding_id" uuid NOT NULL,
	"ordinal" integer NOT NULL,
	"kind" text NOT NULL,
	"label" text NOT NULL,
	"excerpt" text NOT NULL,
	"requirement_local_id" text,
	"span_start" integer,
	"span_end" integer,
	"standard_id" text,
	"clause_id" text,
	"relationship_ids" jsonb
);
--> statement-breakpoint
CREATE TABLE "findings" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"document_id" uuid NOT NULL,
	"local_id" text NOT NULL,
	"kind" text NOT NULL,
	"rule" text NOT NULL,
	"parameter" text,
	"title" text NOT NULL,
	"severity" text NOT NULL,
	"requirement_local_id" text,
	"requirement_text" text NOT NULL,
	"standard_id" text,
	"clause_id" text,
	"standard_label" text NOT NULL,
	"reason" text NOT NULL,
	"action" text NOT NULL,
	"provenance" jsonb NOT NULL,
	"review_status" text DEFAULT 'open' NOT NULL,
	"review_note" text,
	"reviewed_by" uuid,
	"reviewed_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "repairs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"finding_id" uuid NOT NULL,
	"local_id" text NOT NULL,
	"original" text NOT NULL,
	"recommended" text NOT NULL,
	"evidence_label" text NOT NULL,
	"reason" text NOT NULL,
	"provenance" jsonb NOT NULL,
	"status" text DEFAULT 'pending' NOT NULL,
	"final_text" text,
	"decided_by" uuid,
	"decided_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "requirement_standard_links" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"requirement_id" uuid NOT NULL,
	"standard_id" text NOT NULL,
	"clause_id" text NOT NULL,
	"rank" integer NOT NULL,
	"score" real NOT NULL,
	"confidence" real NOT NULL,
	"basis" text NOT NULL,
	"explanation" text NOT NULL,
	"provenance" jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "requirements" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"run_id" uuid NOT NULL,
	"local_id" text NOT NULL,
	"text" text NOT NULL,
	"span_start" integer NOT NULL,
	"span_end" integer NOT NULL,
	"page" integer,
	"section_label" text,
	"modality" text NOT NULL,
	"category" text NOT NULL,
	"category_scores" jsonb NOT NULL,
	"attributes" jsonb NOT NULL,
	"quantities" jsonb NOT NULL,
	"references" jsonb NOT NULL,
	"entities" jsonb NOT NULL,
	"terms" jsonb NOT NULL,
	"vague" boolean NOT NULL,
	"provenance" jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "standard_clauses" (
	"id" text PRIMARY KEY NOT NULL,
	"standard_id" text NOT NULL,
	"ordinal" integer NOT NULL,
	"ref" text,
	"heading" text NOT NULL,
	"text" text NOT NULL,
	"constraints" jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "standard_prior_editions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"designation" text NOT NULL,
	"year" integer NOT NULL,
	"replaced_by_id" text NOT NULL
);
--> statement-breakpoint
CREATE TABLE "standard_relationships" (
	"id" text PRIMARY KEY NOT NULL,
	"type" text NOT NULL,
	"from_standard_id" text NOT NULL,
	"to_standard_id" text NOT NULL,
	"clause_id" text,
	"confidence" real NOT NULL,
	"method" text NOT NULL,
	"note" text NOT NULL
);
--> statement-breakpoint
CREATE TABLE "standard_version_events" (
	"id" text PRIMARY KEY NOT NULL,
	"standard_id" text NOT NULL,
	"date" text,
	"kind" text NOT NULL,
	"summary" text NOT NULL,
	"severity" text NOT NULL,
	"replaced_by_id" text,
	"recorded_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "standards" (
	"id" text PRIMARY KEY NOT NULL,
	"designation" text NOT NULL,
	"year" integer NOT NULL,
	"number" text NOT NULL,
	"title" text NOT NULL,
	"scope" text NOT NULL,
	"category" text NOT NULL,
	"kind" text NOT NULL,
	"status" text NOT NULL,
	"aliases" jsonb NOT NULL,
	"keywords" jsonb NOT NULL,
	"certification" jsonb NOT NULL,
	"checklist" jsonb NOT NULL,
	"source" jsonb NOT NULL,
	"corpus_version" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "analysis_runs" ADD CONSTRAINT "analysis_runs_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "analysis_runs" ADD CONSTRAINT "analysis_runs_owner_id_users_id_fk" FOREIGN KEY ("owner_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "audit_events" ADD CONSTRAINT "audit_events_actor_id_users_id_fk" FOREIGN KEY ("actor_id") REFERENCES "public"."users"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "audit_events" ADD CONSTRAINT "audit_events_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_owner_id_users_id_fk" FOREIGN KEY ("owner_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "evidence" ADD CONSTRAINT "evidence_finding_id_findings_id_fk" FOREIGN KEY ("finding_id") REFERENCES "public"."findings"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "findings" ADD CONSTRAINT "findings_run_id_analysis_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."analysis_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "findings" ADD CONSTRAINT "findings_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "findings" ADD CONSTRAINT "findings_reviewed_by_users_id_fk" FOREIGN KEY ("reviewed_by") REFERENCES "public"."users"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "repairs" ADD CONSTRAINT "repairs_run_id_analysis_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."analysis_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "repairs" ADD CONSTRAINT "repairs_finding_id_findings_id_fk" FOREIGN KEY ("finding_id") REFERENCES "public"."findings"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "repairs" ADD CONSTRAINT "repairs_decided_by_users_id_fk" FOREIGN KEY ("decided_by") REFERENCES "public"."users"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "requirement_standard_links" ADD CONSTRAINT "requirement_standard_links_run_id_analysis_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."analysis_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "requirement_standard_links" ADD CONSTRAINT "requirement_standard_links_requirement_id_requirements_id_fk" FOREIGN KEY ("requirement_id") REFERENCES "public"."requirements"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "requirements" ADD CONSTRAINT "requirements_run_id_analysis_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."analysis_runs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "standard_clauses" ADD CONSTRAINT "standard_clauses_standard_id_standards_id_fk" FOREIGN KEY ("standard_id") REFERENCES "public"."standards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "standard_prior_editions" ADD CONSTRAINT "standard_prior_editions_replaced_by_id_standards_id_fk" FOREIGN KEY ("replaced_by_id") REFERENCES "public"."standards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "standard_relationships" ADD CONSTRAINT "standard_relationships_from_standard_id_standards_id_fk" FOREIGN KEY ("from_standard_id") REFERENCES "public"."standards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "standard_relationships" ADD CONSTRAINT "standard_relationships_to_standard_id_standards_id_fk" FOREIGN KEY ("to_standard_id") REFERENCES "public"."standards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "standard_version_events" ADD CONSTRAINT "standard_version_events_standard_id_standards_id_fk" FOREIGN KEY ("standard_id") REFERENCES "public"."standards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "analysis_runs_document_idx" ON "analysis_runs" USING btree ("document_id");--> statement-breakpoint
CREATE INDEX "analysis_runs_status_idx" ON "analysis_runs" USING btree ("status");--> statement-breakpoint
CREATE INDEX "audit_events_document_idx" ON "audit_events" USING btree ("document_id");--> statement-breakpoint
CREATE INDEX "documents_owner_idx" ON "documents" USING btree ("owner_id");--> statement-breakpoint
CREATE INDEX "evidence_finding_idx" ON "evidence" USING btree ("finding_id");--> statement-breakpoint
CREATE INDEX "findings_run_idx" ON "findings" USING btree ("run_id");--> statement-breakpoint
CREATE INDEX "findings_document_idx" ON "findings" USING btree ("document_id");--> statement-breakpoint
CREATE INDEX "repairs_run_idx" ON "repairs" USING btree ("run_id");--> statement-breakpoint
CREATE INDEX "req_std_links_run_idx" ON "requirement_standard_links" USING btree ("run_id");--> statement-breakpoint
CREATE INDEX "req_std_links_standard_idx" ON "requirement_standard_links" USING btree ("standard_id");--> statement-breakpoint
CREATE INDEX "requirements_run_idx" ON "requirements" USING btree ("run_id");--> statement-breakpoint
CREATE INDEX "standard_clauses_standard_idx" ON "standard_clauses" USING btree ("standard_id");--> statement-breakpoint
CREATE INDEX "standard_rel_from_idx" ON "standard_relationships" USING btree ("from_standard_id");--> statement-breakpoint
CREATE INDEX "standard_rel_to_idx" ON "standard_relationships" USING btree ("to_standard_id");--> statement-breakpoint
CREATE INDEX "standards_designation_idx" ON "standards" USING btree ("designation");