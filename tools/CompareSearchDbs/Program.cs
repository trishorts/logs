// Do two UniProt XML search databases hold the same proteins, as the released mzLib reads them?
//   dotnet run --project tools/CompareSearchDbs -c Release -- <base.xml> <built.xml> <out.json>
// Both files are read with mzLib's ProteinDbLoader.LoadProteinXML, the reader every search uses: no decoys,
// Mods.AllKnownMods, and mzLib's default variant expansion, so the variant proteoforms a search would
// see are compared too. Each protein is matched by accession and compared on its sequence, its candidate
// sequence variants, its gene names, its Ensembl dbReferences, and the modification sites mzLib
// recognizes. "Same proteins" means: the same accessions (entries and proteoforms), and for each the
// same sequence and the same candidate variants. That is what decides whether a build needs its own
// residue alignment (DEF-RESIDUE-CORRESPONDENCE). Replaces logs_orthology.db_equivalence's Python XML parse.
using System; using System.Collections.Generic; using System.IO; using System.Linq;
using System.Security.Cryptography; using System.Text.Json;
using Omics.Modifications; using UsefulProteomicsDatabases;

var (basePath, builtPath, outJson) = (args[0], args[1], args[2]);

static string Sha256(string path)
{
    using var s = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();
}

static Dictionary<string, Proteomics.Protein> Load(string path, out int unknownMods)
{
    var proteins = ProteinDbLoader.LoadProteinXML(path, true, DecoyType.None, Mods.AllKnownMods, false, null,
        out var unknown);
    unknownMods = unknown.Count;
    var byAcc = new Dictionary<string, Proteomics.Protein>();
    foreach (var p in proteins)
        if (!byAcc.TryAdd(p.Accession, p))
            throw new InvalidDataException($"{Path.GetFileName(path)}: accession {p.Accession} loaded twice");
    return byAcc;
}

static string Variants(Proteomics.Protein p) =>
    string.Join(";", p.SequenceVariations.Select(v => v.SimpleString() + "|" + v.Description).OrderBy(s => s, StringComparer.Ordinal));
static string Genes(Proteomics.Protein p) =>
    string.Join(";", p.GeneNames.Select(g => g.Item1 + ":" + g.Item2));
static string Ensembl(Proteomics.Protein p) =>
    string.Join(";", p.DatabaseReferences.Where(r => r.Type == "Ensembl")
        .Select(r => r.Id + "[" + string.Join(",", r.Properties.Select(x => x.Item1 + "=" + x.Item2)) + "]")
        .OrderBy(s => s, StringComparer.Ordinal));
static int ModSites(Proteomics.Protein p) => p.OneBasedPossibleLocalizedModifications.Count;
static int Mods_(Proteomics.Protein p) => p.OneBasedPossibleLocalizedModifications.Sum(kv => kv.Value.Count);
static bool IsEntry(Proteomics.Protein p) => p.AppliedSequenceVariations.Count == 0;

var b = Load(basePath, out int unknownBase);
var t = Load(builtPath, out int unknownBuilt);
var shared = b.Keys.Intersect(t.Keys).ToList();
List<string> Differ(Func<Proteomics.Protein, string> f) =>
    shared.Where(a => f(b[a]) != f(t[a])).OrderBy(a => a, StringComparer.Ordinal).ToList();

var onlyBase = b.Keys.Except(t.Keys).OrderBy(a => a, StringComparer.Ordinal).ToList();
var onlyBuilt = t.Keys.Except(b.Keys).OrderBy(a => a, StringComparer.Ordinal).ToList();
var seq = Differ(p => p.BaseSequence);
var variants = Differ(Variants);
var result = new Dictionary<string, object>
{
    ["mzlib"] = typeof(ProteinDbLoader).Assembly.GetName().Version?.ToString(),
    ["reader"] = "ProteinDbLoader.LoadProteinXML(generateTargets: true, DecoyType.None, Mods.AllKnownMods, default variant expansion)",
    ["base_file"] = Path.GetFileName(basePath), ["base_sha256"] = Sha256(basePath),
    ["built_file"] = Path.GetFileName(builtPath), ["built_sha256"] = Sha256(builtPath),
    ["entries_base"] = b.Values.Count(IsEntry), ["entries_built"] = t.Values.Count(IsEntry),
    ["proteoforms_base"] = b.Values.Count(p => !IsEntry(p)), ["proteoforms_built"] = t.Values.Count(p => !IsEntry(p)),
    ["only_in_base"] = onlyBase, ["only_in_built"] = onlyBuilt,
    ["sequence_differs"] = seq, ["candidate_variants_differ"] = variants,
    ["gene_names_differ"] = Differ(Genes), ["ensembl_dbreferences_differ"] = Differ(Ensembl),
    ["recognized_mod_sites_base"] = b.Values.Where(IsEntry).Sum(ModSites),
    ["recognized_mod_sites_built"] = t.Values.Where(IsEntry).Sum(ModSites),
    ["recognized_mods_base"] = b.Values.Where(IsEntry).Sum(Mods_),
    ["recognized_mods_built"] = t.Values.Where(IsEntry).Sum(Mods_),
    ["entries_with_changed_mods"] = shared.Count(a => IsEntry(b[a]) && Mods_(b[a]) != Mods_(t[a])),
    ["unknown_mod_names_base"] = unknownBase, ["unknown_mod_names_built"] = unknownBuilt,
    ["same_proteins"] = onlyBase.Count == 0 && onlyBuilt.Count == 0 && seq.Count == 0 && variants.Count == 0,
};
File.WriteAllText(outJson, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }) + "\n");
foreach (var kv in result)
    Console.WriteLine($"{kv.Key}: {(kv.Value is List<string> l ? $"{l.Count} {string.Join(",", l.Take(5))}" : kv.Value)}");
