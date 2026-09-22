// Write the compact gene table of an Ensembl GTF with mzLib's EnsemblGeneSetWriter, then read it back
// and check it is the same set (genes and the GTF's provenance) before reporting success.
//   dotnet run --project tools/BuildGeneSet -c Release -- <Species.Assembly.Release.gtf.gz> <out.genes.tsv.gz>
using System; using System.IO; using System.Linq; using System.Security.Cryptography;
using UsefulProteomicsDatabases.Ensembl;

var (gtfPath, outPath) = (args[0], args[1]);
var gtf = EnsemblGeneSet.LoadGtf(gtfPath);
EnsemblGeneSetWriter.Write(outPath, gtf);
var table = EnsemblGeneSetReader.Load(outPath);
if (!table.Genes.SequenceEqual(gtf.Genes)
    || (table.SourceFileName, table.SourceSha256, table.Release, table.GenomeBuild, table.GenebuildLastUpdated)
       != (gtf.SourceFileName, gtf.SourceSha256, gtf.Release, gtf.GenomeBuild, gtf.GenebuildLastUpdated))
{
    Console.Error.WriteLine($"{outPath}: read back differs from {gtfPath}");
    return 1;
}
string sha;
using (var s = File.OpenRead(outPath)) sha = Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();
Console.WriteLine($"{Path.GetFileName(outPath)}\t{gtf.Count} genes\t{new FileInfo(outPath).Length} bytes\tsha256 {sha}\t" +
    $"from {gtf.SourceFileName} ({gtf.SourceSha256[..16]}...) release {gtf.Release} build {gtf.GenomeBuild}");
return 0;
