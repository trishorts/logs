# Oracle findings — does the orthology layer belong in mzLib?

*Run 2026-09-22. Searched `smith/master @ 0b614b4b` (1 day old). Three investigators: accession/gene
prior art, orthology/taxon prior art, external-data conventions. Open-PR sweep against
`smith-chem-wisc/mzLib`, 61 open PRs.*

**This is a findings record, not a locked decision.** It exists so the decision, when made, is made
against what mzLib actually contains rather than against a guess.

---

## Verdict: the project splits, and each layer lands differently

The seed design's three layers are not one decision. They have three different answers.

| Layer | Verdict | Home |
|---|---|---|
| 1. Accession → source gene, from an already-loaded entry | **EXTEND** | mzLib — `Proteomics\Protein\Protein.cs` |
| 1b. Accession string normalization | **ADD-NEW** | mzLib — `MzLibUtil\ClassExtensions.cs` |
| 1c. RefSeq / FASTA parity for gene IDs | **ADD-NEW** | mzLib — `UsefulProteomicsDatabases\ProteinDbLoader.cs` |
| 2a. Network ID-mapping / Ensembl client | **ADD-NEW** | mzLib — `UsefulProteomicsDatabases\`, sibling to `ProteinDbRetriever.cs` |
| 2b. **The versioned relational orthology store** | **DOES NOT BELONG IN MZLIB** | `logs` |
| 3. Cross-species analysis views | **`logs`** | `logs` |

---

## Layer 1 — the cross-references are already in memory

`ProteinXmlEntry.ParseDatabaseReferenceEndElement` (`ProteinXmlEntry.cs:668`) captures **every**
`<dbReference>` untyped and unfiltered — type, id, and all `<property>` children. After
`LoadProteinXML`, a protein's Ensembl, GeneID, RefSeq, HGNC, MGI, RGD and GO cross-references are
already on `Protein.DatabaseReferences` (`Protein.cs:312`), fully parsed, and `ProteinDbWriter`
(`:420-430`) round-trips them. Nothing discards them. mzLib simply never reads them back by type —
except taxonomy.

**The precedent to copy is `Protein.NcbiTaxonomyId`** (`Protein.cs:273`): a computed property over
`DatabaseReferences`, with its type string declared once as a `const`
(`NcbiTaxonomyDatabaseReferenceType`, `Protein.cs:266`) and re-exported from `ProteinDbLoader`
(`:54`). No stored field, no constructor parameter, no parser change.

State of play by input path:

| Input | Today |
|---|---|
| UniProt **XML** | **~70% solved** — data present, accessor absent. One filter by `Type` yields a stable gene ID with no network call. |
| UniProt **FASTA** | ~10% — `GN=<symbol>` only (`ProteinDbLoader.cs:30`). A species-local display symbol, no ID. |
| **RefSeq protein** (`NP_`/`XP_`) | 0% — `DetectFastaHeaderFormat` (`ProteinDbLoader.cs:560`) knows only UniProt / Ensembl / Gencode / Unknown. |
| gene → gene across species | Absent entirely. |

### The projection is not the same shape as `NcbiTaxonomyId`

UniProt writes **one `<dbReference type="Ensembl">` per transcript**, and the ENSG is in a
`<property type="gene ID">`, not in `Id`:

```xml
<dbReference type="Ensembl" id="ENST...">
  <property type="protein sequence ID" value="ENSP..."/>
  <property type="gene ID" value="ENSG..."/>
</dbReference>
```

So `FirstOrDefault(...)?.Id` — the taxonomy shape — is **wrong here**. It needs
`SelectMany(Properties)` plus `Distinct()` (`DatabaseReference` already has value equality,
`DatabaseReference.cs:37`), and a stated answer to *what a multi-ENSG protein means*. That is a
modelling decision for this project, not plumbing, and it is the first place the one-to-many
principle bites inside mzLib rather than in our own schema.

### PENDING-IN-PR — do not invent a second mechanism

**mzLib #1336** (`feat/go-terms-accessor`, ours, updated the same day) does exactly this for GO
terms: `Protein.GoTerms` as a derived view over `DatabaseReferences`, following `NcbiTaxonomyId`,
with a `const` type string, dedupe by id, and union of evidence — no parser change. It also already
solved three problems we would hit verbatim: filtering by `Type` is mandatory because the parser
applies no depth guard (386 dbReferences in one fixture, 39 GO, 86 PubMed); duplicate-entry merges
union rather than collapse; and properties are an unordered bag that `ProteinDbWriter` re-sorts, so
they are matched by type and never by position.

**Move: wait for #1336 to merge, then follow it.** Two typed views over the same list, written
independently a week apart, is the exact duplication this check exists to prevent.

---

## Layer 1b — there is no accession normalization of any kind

No isoform-suffix split, no RefSeq `.1` version strip, no decoy-prefix strip, no canonicalization
before comparison. `IBioPolymer.Equals` (`IBioPolymer.cs:42`) keys identity on **raw string
equality** of `Accession`. The only accession-string helper in the repo is
`MzLibUtil.ClassExtensions.SplitProteinAccessions` (`ClassExtensions.cs:315`), which splits a
protein-group name and normalizes nothing.

Meanwhile the loaders themselves mangle accessions:

- `DECOY_` prefix — `DecoyProteinGenerator.cs:189`, configurable `decoyIdentifier` (default `"DECOY"`)
- ...but **hardcoded** `"DECOY_"` at `PeptideWithSetModifications.cs:1114, :1292, :1384`
- `Random_` entrapment prefix, which **nests**: `DECOY_Random_P12345` (`ProteinXmlEntry.cs:445`)
- `_2`, `_3` collision suffixes on FASTA load (`ProteinDbLoader.cs:333-343`) — a **collision
  counter, not UniProt isoform semantics**; a real `P12345-2` header keeps its `-2` verbatim

A normalizer must take the decoy identifier as a parameter **and** tolerate the hardcoded literal.
Home: `MzLibUtil\ClassExtensions.cs` — dependency-free, already the home of accession-string
helpers, and reachable from Omics/Proteomics/Transcriptomics alike (Proteomics cannot be referenced
from Omics).

---

## Layer 1c — FASTA parity is an established bar, not a nice-to-have

`ProteinDbLoader.UniprotOrganismIdRegex` (`:46`) and the synthesized
`DatabaseReference("NCBI Taxonomy", ...)` at `:361-368` exist **specifically because** "the XML path
kept it and the FASTA path threw it away" was judged a defect worth closing (comment at `:33-47`).
Its stated rationale is one we should adopt wholesale:

> *"A taxonomy id is a join key, where a silently wrong value is worse than a missing one."*

Expect the same standard: if the XML path yields ENSG, the FASTA path must too. `RnaDbLoader`
already contains working patterns to lift — `gene:(ENSG\d+\.\d+)` at `:94` and `\[GeneID=(\d+)\]` at
`:119`. **Gotcha:** the RNA side flattens both into `geneNames = [(v, v)]` (`RnaDbLoader.cs:258-266`),
writing the same string into both tuple slots, so a GeneID `7157` becomes `("7157","7157")` —
indistinguishable from a symbol. The type information is destroyed. Do not copy that.

---

## Layer 2a — the client is a natural sibling

`UsefulProteomicsDatabases\` unambiguously owns "fetch reference data from an external service".
It already holds `ProteinDbRetriever.cs` (UniProt REST), `PrideArchiveClient.cs` (EBI PRIDE), and
`Loaders.cs` (Unimod / PSI-MOD refresh). Newtonsoft 13.0.4 is already referenced, so DTOs need no
new dependency.

Conventions a new client must match — the **binding** ones are enforced by CI, not review:

| Axis | Convention | Binding? |
|---|---|---|
| Failure taxonomy | `Argument*`/`DirectoryNotFound` = fix the call · `MzLibException` = fix the identifier · `HttpRequestException` = transient outage. Status code + URL carried in the message. | advisory (documented) |
| Expected absence | `(bool Found, T)` `Try*` for "service answered, no such thing" **only**. Never null-as-failure. | advisory |
| 408/429/5xx | The *only* "unavailable" band. `ExternalServiceTestHelper.ThrowIfUnavailable:112` and `ProteinDbRetriever.ThrowIfServiceUnavailable:656` must stay in step. | **binding** |
| Exception → test outcome | `HttpRequestException` ⇒ **skipped**; anything else ⇒ **failed** (`ExternalServiceTestHelper.RunAsync:41-44`). Wrong type silently disables the test. | **binding** |
| Test category | `[Category("ExternalService")]` — excluded from the required job via `Test\required.runsettings:21` (`<Where>cat != ExternalService</Where>`, an NUnit `Where`, not a VSTest filter). Miss it and a live test reddens every PR. | **binding** |
| Async | Copy `PrideArchiveClient`: async, `CancellationToken` threaded, `ConfigureAwait(false)` on every await. `ProteinDbRetriever`'s sync API is legacy preserved for MetaMorpheus's WPF window. | advisory |
| Body-stall deadline | `BodyStallTimeout = 2 min`, hand-rolled copy loop (**not** `Stream.CopyToAsync`, which lacks a read deadline). Added after a real incident: one live test held 12m43s of a 20-minute CI job and reddened every open PR. | advisory |
| Partial writes | `.partial` + `File.Move(overwrite: true)`, GUID scratch name to survive concurrent retrievals. | advisory |
| Test seam | `internal` overload taking an `HttpClient`; per-file `StubHandler : HttpMessageHandler` (no shared fixture exists — you will copy it again). | advisory |
| Serialization | Newtonsoft for the wire; System.Text.Json only for embedded/local resources. | advisory |

---

## Layer 2b — the store is the first of its kind, and mzLib argues against it

**mzLib has no persistent, application-managed, cross-run data store of any kind.** Every
downloaded artifact is a file at a path the *caller* supplies, invalidated by MD5 comparison with
**no release identifier recorded anywhere in code** (`Loaders.cs:63-74`, `FilesAreEqual_Hash:316`).
There is no cache-directory concept — no `SpecialFolder`/`LocalApplicationData` use in the repo.
The only relational dependency, `System.Data.SQLite.Core 1.0.118` in `Readers.csproj`, exists to
**read someone else's** `.baf`/`.tdf` files, never to write mzLib's own — and `Readers` sits *above*
`UsefulProteomicsDatabases` in the reference graph, so that project cannot borrow it. It would have
to take the package itself, a first.

What mzLib *does* have is a strong, twice-stated precedent that reference data is **release-pinned
and refreshed by a reviewed commit** — `UsefulProteomicsDatabases\Resources\PROVENANCE.md:6-8`:

> *"deliberately **pinned**, not downloaded: resolving a term against a moving target means the same
> experiment annotated a year apart gets different accessions, and a corpus built that way silently
> stops joining to itself. Refreshing one is a reviewable change to this repository."*

That is our own versioning principle in mzLib's words, and it is an argument *for* pinning — but
its **form** is a trimmed file committed to the repo with a markdown provenance table, embedded as a
resource. Not a database a component builds and manages on a user's disk.

### The comment we have to answer

`ControlledVocabulary.cs:25-27` pre-empts this directly:

> *"The large sample ontologies — NCBITaxon at roughly 600 MB, UBERON, MONDO — are deliberately NOT
> here: an organism identifier comes from the search database that was already loaded (see
> `ProteinDbLoader.NcbiTaxonomyDatabaseReferenceType`), so it never has to be looked up."*

The honest counter-argument is that **an orthology map is a join table, not a lookup vocabulary**.
A vocabulary answers "what does this accession mean" for one entry in isolation, which is why the
loaded search database can supply it. A join table answers "which genes in species B correspond to
this gene in species A", which no single loaded database contains — it is irreducibly cross-corpus,
release-versioned, and many-to-many. That is a real distinction, and it is the argument to make if
this is ever proposed for mzLib. It is *not*, however, an argument that it should live there now.

**Conclusion: the store lives in `logs`.** Proposing mzLib's first self-managed on-disk database
and its first DB dependency outside vendor-file reading, at inception, on an unproven design, is
the wrong order of operations. Build it here; if the schema stabilizes and a second native C#
consumer appears, revisit with the join-table argument in hand.

---

## What mzLib has for orthology today: nothing

`ortholog`, `paralog`, `orthogroup`, `Compara`, `Blast`, `SmithWaterman`, `Levenshtein`,
`SequenceSimilarity`, `idmapping`, `CrossReference` — **zero matches, all of them.** No alignment,
no sequence-similarity machinery, so there is no basis for a homology fallback in mzLib.

### Name traps

- **`maximumHomology` is a false friend.** `PeptideWithSetModifications.cs:1150` — per-position
  percent identity between a peptide and a same-length scramble of itself, for decoy generation. No
  alignment, no gaps, no substitution matrix. Do not reuse the name.
- **`Compara` only ever matches `IComparable`.**
- **`Species` is a mass-spec word here**, not a biology word (`TraceCorrector`, `MassFeature`,
  `FlashLfqEngine` use it for charge/isotope species). Avoid it as a type name.
- **`Organism` means three different things**: free text on `Protein`/`IBioPolymer`; a typed
  `CvParam` on `SdrfBuilderInputs.Organism` (`SdrfBuilderInputs.cs:30`); and `List<CvParam>` on the
  PRIDE DTOs, which is *sample* metadata, not search-database metadata.
- **`GeneNames.Item1` is not a namespace.** It is UniProt's `"primary"`/`"synonym"`/`"ORF"`. Do not
  overload it as a database tag.

---

## Blast radius / separate-PR items

- **`Protein.NcbiTaxonomyId` is a `string`, not an int**, and is a LINQ `FirstOrDefault` scan of
  `DatabaseReferences` on **every access** (`Protein.cs:273`). Fine for one call; a real cost if an
  orthology join calls it per-protein in a tight loop. Cache or introduce a typed value object —
  but that is its own change.
- **`ProteinDbRetriever.UniprotProteomesList` (`:516`) already downloads the Organism Id column and
  drops it at `:548`** — `dictionaryOfAvailableProteomes[arr[0]] = arr[1]`. mzLib's closest thing to
  a species registry throws the taxon id away. Two-line fix, but changing that return type is a
  **breaking API change for MetaMorpheus**: separate PR, on its own terms.
- **`DatabaseReferences` is on `Protein`, not `IBioPolymer`**; RNA's parallel bag is a flat
  `Dictionary<string,string>? AdditionalDatabaseFields` (`NucleicAcid.cs:169`) with different
  semantics, and the RNA side captures no taxon id at all. Unifying them is larger than this project
  needs — **scope to `Protein` first**, and note that a genuinely generic-over-omics orthology layer
  would require lifting the taxon accessor up, which is a prerequisite, not a detail.
- `ProteinDbRetriever.Columns` (`:793`) is an empty enum stub and `UniprotColumnsList()` (`:557`)
  reads from `Directory.GetCurrentDirectory()`. Neither is usable for requesting
  `xref_ensembl`/`xref_geneid` return fields. Unfinished, not prior art.

---

## Open-PR sweep

61 open PRs on `smith-chem-wisc/mzLib`. With discriminating terms
(`ortholog, orthology, homolog, orthogroup, Compara, Ensembl, HGNC, IdMapping, TaxonId, taxonomy,
CrossReference, DatabaseReference, GeneName`), two intersect:

- **#1336** `feat/go-terms-accessor` — the pattern to follow; see above. **Wait for merge.**
- **#1328** `fix/missing-unimod-accessions` — incidental `DatabaseReference` mention, no collision.

Nothing in flight adds orthology, taxon typing, or ID mapping.
