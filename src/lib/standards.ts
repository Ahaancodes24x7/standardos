export type Clause = { id: string; text: string; section: string };

export type Standard = {
  id: string;
  number: string;
  title: string;
  scope: string;
  category: string;
  language: string;
  year: number;
  clauses: Clause[];
  relatedStandardIds: string[];
  certificationBodies: string[];
};

export type SearchResult = {
  standard: Standard;
  matchedClause: Clause;
  confidenceScore: number;
  explanation: string;
};

export const standards: Standard[] = [
  {
    id: "is-732-2019", number: "IS 732:2019", title: "Code of Practice for Electrical Wiring Installations",
    scope: "Design, selection, erection and verification of electrical installations in buildings.", category: "Electrical", language: "English", year: 2019,
    clauses: [{ id: "732-5.3.3", section: "Clause 5.3.3 — Protection", text: "Each circuit shall be protected against overcurrent by a suitable protective device selected for the current-carrying capacity of the conductor." }, { id: "732-6.4", section: "Clause 6.4 — Verification", text: "Every installation shall be inspected and tested before being placed in service." }],
    relatedStandardIds: ["is-3043-2018", "is-694-2010"], certificationBodies: ["Bureau of Indian Standards", "Central Electricity Authority"],
  },
  {
    id: "is-3043-2018", number: "IS 3043:2018", title: "Code of Practice for Earthing",
    scope: "Guidance on earthing systems and protective conductors for electrical installations.", category: "Electrical", language: "English", year: 2018,
    clauses: [{ id: "3043-12.2", section: "Clause 12.2 — Earth continuity", text: "The earth continuity conductor shall be capable of carrying the prospective earth fault current without excessive temperature rise." }],
    relatedStandardIds: ["is-732-2019"], certificationBodies: ["Bureau of Indian Standards"],
  },
  {
    id: "is-694-2010", number: "IS 694:2010", title: "PVC Insulated Cables for Working Voltages up to 1100 V",
    scope: "Requirements and tests for copper and aluminium conductor PVC insulated cables.", category: "Electrical", language: "English", year: 2010,
    clauses: [{ id: "694-8.1", section: "Clause 8.1 — Conductor resistance", text: "The DC resistance of each conductor at 20 °C shall not exceed the specified maximum value." }],
    relatedStandardIds: ["is-732-2019"], certificationBodies: ["Bureau of Indian Standards"],
  },
  {
    id: "is-456-2000", number: "IS 456:2000", title: "Plain and Reinforced Concrete — Code of Practice",
    scope: "General structural use of plain and reinforced concrete in buildings and civil works.", category: "Civil Engineering", language: "English", year: 2000,
    clauses: [{ id: "456-8.2.4", section: "Clause 8.2.4 — Durability", text: "The minimum cement content and maximum free water-cement ratio shall be governed by the exposure conditions." }],
    relatedStandardIds: ["is-383-2016", "is-1786-2008"], certificationBodies: ["Bureau of Indian Standards", "CPWD"],
  },
  {
    id: "is-383-2016", number: "IS 383:2016", title: "Coarse and Fine Aggregate for Concrete — Specification",
    scope: "Requirements for natural, manufactured and recycled aggregates used in concrete.", category: "Civil Engineering", language: "English", year: 2016,
    clauses: [{ id: "383-5.2", section: "Clause 5.2 — Grading", text: "Fine aggregate shall conform to the grading requirements of the specified grading zone." }],
    relatedStandardIds: ["is-456-2000"], certificationBodies: ["Bureau of Indian Standards"],
  },
  {
    id: "is-1786-2008", number: "IS 1786:2008", title: "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
    scope: "Requirements for high-strength deformed steel reinforcement used in concrete structures.", category: "Materials", language: "English", year: 2008,
    clauses: [{ id: "1786-7.2", section: "Clause 7.2 — Mechanical properties", text: "The material shall meet the specified proof stress, tensile strength and elongation requirements for its grade." }],
    relatedStandardIds: ["is-456-2000"], certificationBodies: ["Bureau of Indian Standards"],
  },
  {
    id: "is-10500-2012", number: "IS 10500:2012", title: "Drinking Water — Specification",
    scope: "Acceptable and permissible limits for physical, chemical and bacteriological drinking-water quality.", category: "Water & Environment", language: "English / Hindi", year: 2012,
    clauses: [{ id: "10500-4.1", section: "Clause 4.1 — Requirements", text: "Drinking water shall comply with the acceptable requirements specified; permissible limits apply only in the absence of an alternate source." }],
    relatedStandardIds: ["is-1622-1981"], certificationBodies: ["Bureau of Indian Standards", "Ministry of Jal Shakti"],
  },
  {
    id: "is-1622-1981", number: "IS 1622:1981", title: "Methods of Sampling and Microbiological Examination of Water",
    scope: "Sampling and microbiological examination procedures for water quality assessment.", category: "Water & Environment", language: "English", year: 1981,
    clauses: [{ id: "1622-3.2", section: "Clause 3.2 — Sampling", text: "Samples shall be collected in sterile containers and protected from contamination during transport." }],
    relatedStandardIds: ["is-10500-2012"], certificationBodies: ["Bureau of Indian Standards"],
  },
];

const makeResult = (standardId: string, confidenceScore: number, explanation: string): SearchResult => {
  const standard = standards.find((item) => item.id === standardId);
  const matchedClause = standard?.clauses[0];
  if (!standard || !matchedClause) throw new Error(`Missing demonstration standard: ${standardId}`);
  return { standard, matchedClause, confidenceScore, explanation };
};

export const searchResults: SearchResult[] = [
  makeResult("is-732-2019", 96, "The tender asks for low-voltage building wiring with circuit-level overload protection. This clause directly governs protective-device selection for those conductors."),
  makeResult("is-3043-2018", 91, "The requirement for a continuous protective earth maps to the standard’s earth-continuity and fault-current provisions."),
  makeResult("is-694-2010", 84, "The specified 1.1 kV PVC cable falls within this product standard’s voltage and conductor-resistance scope."),
];

export const getStandard = (id: string) => standards.find((standard) => standard.id === id);
export const getRelated = (ids: string[]) => standards.filter((standard) => ids.includes(standard.id));