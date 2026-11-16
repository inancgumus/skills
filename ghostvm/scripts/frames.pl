#!/usr/bin/perl
# vmx frames <film> [--from MS] [--to MS] [--rect x,y,w,h] [--out sheet.png]
# One contact sheet of the film's real frames (the film holds a frame only when pixels changed), in order, each labeled
# with its film time in ms, the same times as <film>.times.txt. --rect crops to a part of the screen, in screen points
# (a `shot` pixel). At most 24 frames: with more, it picks evenly and says which. Runs on the host only.
use strict; use warnings; use File::Basename qw(dirname); use POSIX qw(ceil);
{ my $lib = dirname(__FILE__) . '/filmlib.pl'; require $lib; }
my ($o, $f, @extra) = opts(@ARGV);
defined $f && !@extra or die2('usage: vmx frames <film> [--from MS] [--to MS] [--rect x,y,w,h] [--out sheet.png]');
need_ffmpeg();
my $film = film($f);
my @n = pick($film, $o);
@n or die2("vmx: no frames between " . ($o->{from} // 0) . " and " . ($o->{to} // 'the end') . " ms. The film's frames run from " . int($film->{ms}[0] // 0) . " to " . int($film->{ms}[-1] // 0) . " ms.");
my $all = @n; my $MAX = 24;
@n = map { $n[int($_ * ($all - 1) / ($MAX - 1) + 0.5)] } 0 .. $MAX - 1 if $all > $MAX;

# The crop in film pixels.
my ($cx, $cy, $cw, $ch) = (0, 0, $film->{w}, $film->{h});
if (my $r = $o->{rect}) {
    ($cx, $cy) = to_px($film, $r->[0], $r->[1]);
    my ($x2, $y2) = to_px($film, ($r->[0] + $r->[2] < ($film->{ax} // 0) + ($film->{aw} // 1e9) ? $r->[0] + $r->[2] : ($film->{ax} // 0) + $film->{aw} - 1),
                                 ($r->[1] + $r->[3] < ($film->{ay} // 0) + ($film->{ah} // 1e9) ? $r->[1] + $r->[3] : ($film->{ay} // 0) + $film->{ah} - 1));
    ($cw, $ch) = ($x2 - $cx, $y2 - $cy);
    $cw >= 8 && $ch >= 8 or die2('vmx: --rect is too small');
}
# Tiles: up to 4 across, the sheet at most 2400 px wide, a tile never larger than the crop.
my $cols = @n < 4 ? scalar @n : 4; my $rows = ceil(@n / $cols);
my $tw = int(2400 / $cols); $tw = $cw if $cw < $tw; $tw -= $tw % 2;
my $th = int($ch * $tw / $cw); $th -= $th % 2;
my $out = $o->{out} // "$f.frames.png";
my $sel = join '+', map { "eq(n\\,$_)" } @n;
my $label = system('ffmpeg -hide_banner -filters 2>/dev/null | grep -q drawtext') == 0
    ? ",drawtext=text='%{eif\\:t*1000+0.5\\:d} ms':x=8:y=8:fontsize=" . ($th > 120 ? 28 : 16) . ":fontcolor=white:box=1:boxcolor=black\@0.7:boxborderw=6" : '';
my $vf = "select='$sel',format=rgb24,crop=$cw:$ch:$cx:$cy,scale=$tw:$th$label,tile=${cols}x${rows}:padding=4:color=gray";
system('ffmpeg', '-v', 'error', '-y', '-i', $f, '-vf', $vf, '-fps_mode', 'passthrough', '-frames:v', '1', $out) == 0 && -s $out
    or die2("vmx: ffmpeg could not make the sheet");
print "saved $out: " . scalar(@n) . " frames" . ($all > @n ? " of $all (picked evenly; narrow --from and --to to see them all)" : '') . ", left to right, top to bottom, " . ($label ? 'each labeled with its time' : 'at these times') . ":\n";
print join('  ', map { int($film->{ms}[$_] + 0.5) . ' ms' } @n), "\n";
print "Read the sheet to look. Times are film time, as in $f.times.txt.\n" if -f "$f.times.txt";
