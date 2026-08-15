import { AttackAtlasExplorer } from "@/components/attack-atlas-explorer";
import { PageHeader } from "@/components/page-header";
import { ProvenanceChip } from "@/components/provenance-chip";
import { Alert } from "@/components/ui/alert";
import { loadAttackAtlas } from "@/lib/evidence/loader";
import { format } from "@/lib/format";

export const metadata = { title: "Identify · Attack Atlas" };

export default async function IdentifyPage() {
  const cards = await loadAttackAtlas();
  const variants = cards.reduce((sum, card) => sum + card.variants.length, 0);
  return <div><PageHeader eyebrow="Identify · Attack atlas" title="Eight equal-priority hypotheses, not a ranked threat list." conclusion={`The atlas translates emerging GenAI-enabled fraud into ${format.integer(cards.length)} testable campaign archetypes and ${format.integer(variants)} variants spanning cards, account-to-account payments, identity, merchants and disputes.`}><ProvenanceChip source="artifacts/precomputed/attack_atlas.json" field="all fields; array length and sum(variants.length)" /></PageHeader><Alert title="How to read the atlas" className="mb-6">Every archetype has equal status. Selecting one changes the detail view only; it does not imply higher likelihood, impact or build priority.</Alert><AttackAtlasExplorer cards={cards} /></div>;
}
