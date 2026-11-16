#!/usr/bin/perl
# vmx frames <film> [--from MS] [--to MS] [--rect x,y,w,h] [--cols N] [--zoom N] [--out sheet.png]
# vmx frames <picture>... [--rect x,y,w,h] [--cols N] [--zoom N] [--out sheet.png]
# One contact sheet of the film's real frames (the film holds a frame only when pixels changed), in order, each labeled
# with its film time in ms, the same times as <film>.times.txt. Or one sheet of pictures (.png, .jpg), each labeled with
# its file name, all cropped to the same --rect, to compare them side by side. --rect is in screen points (a `shot`
# pixel). A picture without <picture>.area counts its own pixels, halved for an @2x name. Tiles keep full detail when
# they fit 2400 px across and 4800 px down; --cols sets the columns (1 stacks them), --zoom N enlarges small crops N times with sharp
# pixels. At most 24 frames: with more, it picks evenly and says which. Runs on the host only.
use strict; use warnings; use File::Basename qw(dirname basename); use POSIX qw(ceil);
{ use Cwd (); my $lib = Cwd::abs_path(dirname(__FILE__)) . '/filmlib.pl'; require $lib; }
my @args; my ($cols, $zoom);
while (@ARGV) {
    my $a = shift @ARGV;
    if ($a eq '--cols') { $cols = shift @ARGV // ''; $cols =~ /^[1-8]$/ or die2('--cols needs 1 to 8') }
    elsif ($a eq '--zoom') { $zoom = shift @ARGV // ''; $zoom =~ /^[1-8]$/ or die2('--zoom needs 1 to 8') }
    else { push @args, $a }
}
$zoom //= 1;
my ($o, @in) = opts(@args);
my $usage = 'usage: vmx frames <film> [--from MS] [--to MS] [--rect x,y,w,h] [--cols N] [--zoom N] [--out sheet.png]
       vmx frames <picture>... [--rect x,y,w,h] [--cols N] [--zoom N] [--out sheet.png]';
@in or die2($usage);
need_ffmpeg();
my $pics = !grep { !/\.(png|jpe?g)$/i } @in;
$pics || @in == 1 or die2("vmx: give one film, or one or more pictures (.png, .jpg).\n$usage");
!$pics || !defined($o->{from}) && !defined($o->{to}) or die2('vmx: --from and --to are for films, not pictures');

# The crop of one source in its pixels, clamped to it.
sub crop {
    my $s = shift;
    return (0, 0, $s->{w}, $s->{h}) unless my $r = $o->{rect};
    my ($x, $y) = to_px($s, $r->[0], $r->[1]);
    my $sc = $s->{scale} // 2;
    my ($w, $h) = (int($r->[2] * $sc), int($r->[3] * $sc));
    $w = $s->{w} - $x if $x + $w > $s->{w}; $h = $s->{h} - $y if $y + $h > $s->{h};
    $w >= 8 && $h >= 8 or die2("vmx: --rect is too small or outside $s->{file}");
    return ($x, $y, $w, $h);
}

my (@src, @labels, $all, @n, $film);
if ($pics) {
    @src = map { picture($_) } @in;
    @labels = map { my $b = basename($_->{file}); $b =~ s/[^\w.@-]/_/g; $b } @src;
    $all = @src;
    @src <= 24 or die2('vmx: at most 24 pictures in one sheet');
} else {
    $film = film($in[0]);
    @n = pick($film, $o);
    @n or die2("vmx: no frames between " . ($o->{from} // 0) . " and " . ($o->{to} // 'the end') . " ms. The film's frames run from " . int($film->{ms}[0] // 0) . " to " . int($film->{ms}[-1] // 0) . " ms.");
    $all = @n; my $MAX = 24;
    @n = map { $n[int($_ * ($all - 1) / ($MAX - 1) + 0.5)] } 0 .. $MAX - 1 if $all > $MAX;
    @src = ($film);
}
my $count = $pics ? @src : @n;

# Tiles: as many across as fit 2400 px at full detail (1 to 4), the tile never larger than the crop times --zoom.
my @c = map { [crop($_)] } @src;
my ($cw, $ch) = @{$c[0]}[2, 3];
for (@c) { $cw = $_->[2] if $_->[2] > $cw; $ch = $_->[3] if $_->[3] > $ch }
my $full = $cw * $zoom;
# With no --cols, more columns (up to 4, shrinking the tiles) keep the sheet under 4800 px tall.
$cols //= do {
    my $k = int(2400 / $full); $k = $k < 1 ? 1 : $k > 4 ? 4 : $k;
    while ($k < 4 && $k < $count) { my $w = $full < 2400 / $k ? $full : 2400 / $k; last if ceil($count / $k) * $ch * $w / $cw <= 4800; $k++ }
    $k };
$cols = $count if $cols > $count;
my $rows = ceil($count / $cols);
my $tw = int(2400 / $cols); $tw = $full if $full < $tw; $tw -= $tw % 2;
my $th = int($ch * $tw / $cw); $th -= $th % 2;
my $sharp = $tw > $cw ? ':flags=neighbor' : '';
my $out = $o->{out} // ($pics ? dirname($in[0]) . '/sheet.png' : "$in[0].frames.png");
my $font = $th > 120 ? 28 : 16;
my $drawtext = system('ffmpeg -hide_banner -filters 2>/dev/null | grep -q drawtext') == 0;
my $box = ":x=8:y=8:fontsize=$font:fontcolor=white:box=1:boxcolor=black\@0.7:boxborderw=6";
my @cmd = ('ffmpeg', '-v', 'error', '-y');
my $vf;
if ($pics) {
    push @cmd, map { ('-i', $_->{file}) } @src;
    $vf = join(';', map {
        my ($x, $y, $w, $h) = @{$c[$_]};
        "[$_:v]format=rgb24,crop=$w:$h:$x:$y,scale=$tw:$th:force_original_aspect_ratio=decrease$sharp,pad=$tw:$th:0:0:gray"
          . ($drawtext ? ",drawtext=text='$labels[$_]'$box" : '') . "[t$_]"
    } 0 .. $#src) . ';' . join('', map { "[t$_]" } 0 .. $#src) . "concat=n=" . scalar(@src) . ":v=1:a=0,tile=${cols}x${rows}:padding=4:color=gray";
    push @cmd, '-filter_complex', $vf;
} else {
    my ($x, $y, $w, $h) = @{$c[0]};
    my $sel = join '+', map { "eq(n\\,$_)" } @n;
    $vf = "select='$sel',format=rgb24,crop=$w:$h:$x:$y,scale=$tw:$th$sharp"
        . ($drawtext ? ",drawtext=text='%{eif\\:t*1000+0.5\\:d} ms'$box" : '') . ",tile=${cols}x${rows}:padding=4:color=gray";
    push @cmd, '-i', $in[0], '-vf', $vf, '-fps_mode', 'passthrough';
}
system(@cmd, '-frames:v', '1', $out) == 0 && -s $out or die2("vmx: ffmpeg could not make the sheet");
my $detail = $tw >= $cw ? ($tw > $cw ? sprintf('enlarged %.4gx', $tw / $cw) : 'at full detail') : sprintf('shrunk to %d%%', 100 * $tw / $cw) . ($tw < 0.95 * $cw ? ($cols > 1 ? '; use --cols 1' : '; use a smaller --rect') . ' for full detail' : '');
if ($pics) {
    print "saved $out: " . scalar(@src) . " pictures, $cols across, $detail, left to right, top to bottom:\n";
    print join('  ', map { basename($_->{file}) } @src), "\n";
} else {
    print "saved $out: $count frames" . ($all > $count ? " of $all (picked evenly; narrow --from and --to to see them all)" : '') . ", $cols across, $detail, left to right, top to bottom, " . ($drawtext ? 'each labeled with its time' : 'at these times') . ":\n";
    print join('  ', map { int($film->{ms}[$_] + 0.5) . ' ms' } @n), "\n";
    print "Read the sheet to look. Times are film time, as in $in[0].times.txt.\n" if -f "$in[0].times.txt";
}
