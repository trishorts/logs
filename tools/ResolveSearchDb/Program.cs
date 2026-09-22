// Resolve every protein in a UniProt XML search database to stable Ensembl genes with mzLib's
// EnsemblGeneResolver, and write the long-format table.
//   dotnet run --project tools/ResolveSearchDb -c Release -- <search.xml> <gtf.gz> <uniprot-xref.tsv.gz> <out.tsv>
// The XML must be the DECOMPRESSED file the search read: its sha256 is the key every row carries.
using System; using System.IO; using System.Linq; using System.Security.Cryptography;
using UsefulProteomicsDatabases; using UsefulProteomicsDatabases.Ensembl;

var (xml, gtf, xref, outTsv) = (args[0], args[1], args[2], args[3]);
string sha;
using (var s = File.OpenRead(xml)) sha = Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();
var proteins = ProteinDbLoader.LoadProteinXML(xml, true, DecoyType.None, null, false, null, out _);
var resolver = new EnsemblGeneResolver(EnsemblGeneSet.LoadGtf(gtf), EnsemblXrefTable.Load(xref));
var rows = resolver.ResolveAll(proteins, sha).ToList();
using (var w = new StreamWriter(outTsv)) GeneResolutionTsv.Write(w, rows);
Console.WriteLine($"search db sha256 {sha}\nproteins {proteins.Count}  rows {rows.Count}  " +
    $"gene set {resolver.GeneSet.SourceFileName} ({resolver.GeneSet.Count} genes)  xref {resolver.Xrefs.SourceFileName}");
