// How Ensembl's xref relates to each gene row of a search database: DEF-GENE-RESOLUTION v2's agreement states
// (agrees / silent / disagrees), counted by mzLib's own resolver, not by a Python re-reading (user, 2026-11-10).
//   dotnet run --project tools/XrefAgreementCounts -c Release -- <out.json> <label>=<search.xml>|<genes.tsv.gz>|<uniprot.tsv.gz> ...
// Counts are of ENTRIES (the proteins LoadProteinXML loads before applying variants) unless they say rows.
// An entry is covered by a view when at least one of its rows is in it: "agrees" is v1's default view
// (EnsemblXrefAgrees == true), and "agrees_or_silent" is v2's (aging 022).
using System; using System.Collections.Generic; using System.IO; using System.Linq;
using System.Security.Cryptography; using System.Text.Json;
using UsefulProteomicsDatabases; using UsefulProteomicsDatabases.Ensembl;

var outJson = args[0];
var results = new List<Dictionary<string, object>>();
foreach (var run in args.Skip(1))
{
    var label = run[..run.IndexOf('=')];
    var parts = run[(run.IndexOf('=') + 1)..].Split('|');
    var (xml, genes, xref) = (parts[0], parts[1], parts[2]);
    string sha;
    using (var s = File.OpenRead(xml)) sha = Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();

    var entries = ProteinDbLoader.LoadProteinXML(xml, true, DecoyType.None, null, false, null, out _)
        .Where(p => p.AppliedSequenceVariations.Count == 0).ToList();
    var resolver = new EnsemblGeneResolver(EnsemblGeneSetReader.Load(genes), EnsemblXrefTable.Load(xref));
    var byEntry = entries.ToDictionary(p => p.Accession, p => resolver.Resolve(p, sha));
    var protein = entries.ToDictionary(p => p.Accession);
    var rows = byEntry.Values.SelectMany(r => r).ToList();

    static string Name(EnsemblXrefAgreement? a) => GeneResolutionTsv.AgreementName(a) ?? "none";
    bool Any(string acc, params EnsemblXrefAgreement[] states) => byEntry[acc].Any(r => r.EnsemblXrefAgreement is { } a && states.Contains(a));
    Dictionary<string, object> Coverage(IEnumerable<string> accs)
    {
        var list = accs.ToList();
        var silent = list.Where(a => Any(a, EnsemblXrefAgreement.Silent)).ToList();
        return new Dictionary<string, object>
        {
            ["entries"] = list.Count,
            ["agrees"] = list.Count(a => Any(a, EnsemblXrefAgreement.Agrees)),
            ["agrees_or_silent"] = list.Count(a => Any(a, EnsemblXrefAgreement.Agrees, EnsemblXrefAgreement.Silent)),
            ["with_a_silent_row"] = silent.Count,
            ["with_a_disagrees_row"] = list.Count(a => Any(a, EnsemblXrefAgreement.Disagrees)),
            ["disagrees_only"] = list.Count(a => Any(a, EnsemblXrefAgreement.Disagrees) && !Any(a, EnsemblXrefAgreement.Agrees, EnsemblXrefAgreement.Silent)),
            ["silent_by_created_year"] = silent
                .GroupBy(a => (protein[a].UniProtEntryAttributes?.Created ?? "").Split('-')[0])
                .OrderBy(g => g.Key).ToDictionary(g => g.Key, g => g.Count()),
        };
    }

    // The v1 column must be untouched: agreement is Agrees exactly where the boolean is true, Silent or Disagrees
    // where it is false, and null where it is null.
    int inconsistent = rows.Count(r => r.EnsemblXrefAgrees switch
    {
        null => r.EnsemblXrefAgreement != null,
        true => r.EnsemblXrefAgreement != EnsemblXrefAgreement.Agrees,
        false => r.EnsemblXrefAgreement is not (EnsemblXrefAgreement.Silent or EnsemblXrefAgreement.Disagrees),
    });
    var datasets = entries.GroupBy(p => p.UniProtEntryAttributes?.Dataset ?? "unknown").OrderBy(g => g.Key);
    results.Add(new Dictionary<string, object>
    {
        ["label"] = label, ["search_database"] = Path.GetFileName(xml), ["search_database_sha256"] = sha,
        ["gene_set"] = Path.GetFileName(genes), ["xref"] = Path.GetFileName(xref), ["xref_sha256"] = resolver.Xrefs.SourceSha256,
        ["rows"] = rows.Count,
        ["rows_by_source_and_agreement"] = rows.GroupBy(r => $"{r.Source}|{Name(r.EnsemblXrefAgreement)}")
            .OrderBy(g => g.Key, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Count()),
        ["rows_where_agreement_contradicts_the_v1_boolean"] = inconsistent,
        ["outcome_by_entry"] = byEntry.Values.GroupBy(r => GeneResolutionTsv.OutcomeName(r[0].Outcome))
            .OrderBy(g => g.Key, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Count()),
        ["all"] = Coverage(byEntry.Keys),
        ["by_dataset"] = datasets.ToDictionary(g => g.Key, g => (object)Coverage(g.Select(p => p.Accession))),
    });
    Console.WriteLine($"{label}: {entries.Count} entries, {rows.Count} rows, inconsistent {inconsistent}");
}
File.WriteAllText(outJson, JsonSerializer.Serialize(new Dictionary<string, object>
{
    ["tool"] = "tools/XrefAgreementCounts",
    ["mzlib_branch"] = "feat/ensembl-xref-agreement",
    ["runs"] = results,
}, new JsonSerializerOptions { WriteIndented = true }) + "\n");
