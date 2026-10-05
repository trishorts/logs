// Usage: BuildOrthologySnapshot <release> <compara dir> <gene-sets dir> <out dir | -> <species...>
// Builds the snapshot in memory and prints the counts that tests/test_reported_claims.py pins, so the
// C# builder can be checked against numbers already sent to partners (007-logs).
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using UsefulProteomicsDatabases.Ensembl;

string release = args[0], compara = args[1], geneSetsDir = args[2];
string outDir = args[3];
var species = args.Skip(4).OrderBy(s => s, StringComparer.Ordinal).ToList();
var clock = Stopwatch.StartNew();

var geneSets = species.ToDictionary(s => s, s =>
{
    string stem = char.ToUpperInvariant(s[0]) + s.Substring(1);
    string table = Directory.GetFiles(geneSetsDir, $"{stem}.*.{release}.genes.tsv.gz").Single();
    return EnsemblGeneSetReader.Load(table);
});
var trees = ComparaGeneTreeContent.Load(
    Path.Combine(compara, $"vertebrates.GeneTree_content.default.e{release}.txt.gz"), geneSets.Values);
var dumps = species.Select(s => ComparaHomologyDump.Load(
    Path.Combine(compara, $"{s}.protein_default.homologies.tsv.gz"), species)).ToList();
var snap = OrthologySnapshot.Build(release, geneSets, trees, dumps);
Console.WriteLine($"built in {clock.Elapsed.TotalSeconds:F0} s; identical duplicates dropped: {snap.IdenticalDuplicatesDropped}");

foreach (var (a, b) in snap.Pairs)
{
    var rows = snap.Pair(a, b);
    Console.WriteLine($"pair {a}__{b}: {rows.Count} rows; " +
        string.Join(", ", rows.GroupBy(r => r.HomologyType).OrderBy(g => g.Key, StringComparer.Ordinal).Select(g => $"{g.Key} {g.Count()}")));
}

// The eligible set cardinality.py uses: protein_coding plus the IG/TR gene segments Compara also trees.
var eligible = new HashSet<string>(StringComparer.Ordinal)
{
    "protein_coding", "IG_V_gene", "IG_C_gene", "IG_J_gene", "IG_D_gene", "IG_LV_gene",
    "TR_V_gene", "TR_C_gene", "TR_J_gene", "TR_D_gene",
};
foreach (string a in species)
foreach (string b in species.Where(b => b != a))
{
    var counts = snap.PairStatus(a, b).Where(x => eligible.Contains(x.Gene.Biotype))
        .GroupBy(x => x.Status).ToDictionary(g => g.Key, g => g.Count());
    Console.WriteLine($"status {a}->{b}: " + string.Join(", ", Enum.GetValues<OrthologyStatus>()
        .Select(s => $"{s} {counts.GetValueOrDefault(s)}")));
}

if (species.Count == 3 && species.Contains("homo_sapiens"))
{
    var others = species.Where(s => s != "homo_sapiens").ToArray();
    var tuples = snap.SpeciesSet(new[] { "homo_sapiens" }.Concat(others).ToArray()).ToList();
    var eligibleHuman = tuples.Where(t => geneSets["homo_sapiens"].TryGetGene(t.GeneIds[0], out var g) && eligible.Contains(g.Biotype)).ToList();
    Console.WriteLine($"species_set human-anchored: {tuples.Count} tuples; eligible human genes in an all-one2one tuple: " +
        $"{eligibleHuman.Where(t => t.AllOneToOne).Select(t => t.GeneIds[0]).Distinct().Count()}");
}
Console.WriteLine($"done in {clock.Elapsed.TotalSeconds:F0} s");
if (outDir != "-")
{
    var written = await OrthologySnapshotWriter.WriteAsync(snap, outDir);
    Console.WriteLine($"wrote snapshot {written.SnapshotId[..16]} to {outDir}: {written.Files.Count} files, " +
        $"{written.Files.Sum(f => f.Bytes):N0} bytes, in {clock.Elapsed.TotalSeconds:F0} s");
}
