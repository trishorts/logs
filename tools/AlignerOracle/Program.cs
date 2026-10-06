using System; using System.IO;
using Omics.SequenceAlignment;
var free = new PairwiseAligner(); var charged = new PairwiseAligner(freeEndGaps: false);
int n = 0, bad = 0;
foreach (var line in File.ReadLines(args[0])) {
    var c = line.Split('\t'); n++;
    var a = (c[0] == "1" ? free : charged).Align(c[1], c[2]);
    if (a.Score != int.Parse(c[3])) { bad++; if (bad < 5) Console.WriteLine($"{c[0]} {a.Score} vs {c[3]}: {c[1]} {c[2]}"); }
}
Console.WriteLine($"{n} pairs, {bad} differ from Biopython's optimal score");
