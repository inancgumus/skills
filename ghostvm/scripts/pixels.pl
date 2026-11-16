#!/usr/bin/perl
# vmx pixels <film> X,Y [X,Y...] [--from MS] [--to MS] [--all]
# Each point's color (#rrggbb) in the film's frames, as a table by film time in ms. Points are screen points (a `shot`
# pixel). Prints a row only when a color changed, plus the first and last frame, unless --all. Runs on the host only.
use strict; use warnings; use File::Basename qw(dirname);
{ my $lib = dirname(__FILE__) . '/filmlib.pl'; require $lib; }
my $every = grep { $_ eq '--all' } @ARGV; @ARGV = grep { $_ ne '--all' } @ARGV;
my ($o, $f, @pts) = opts(@ARGV);
defined $f && @pts && !grep { !/^\d+,\d+$/ } @pts or die2('usage: vmx pixels <film> X,Y [X,Y...] [--from MS] [--to MS] [--all]   (points in whole screen points)');
need_ffmpeg();
my $film = film($f);
my @px = map { [to_px($film, split /,/)] } @pts;
my %want = map { $_ => 1 } pick($film, $o);
%want or die2("vmx: no frames in that time range. The film's frames run from " . int($film->{ms}[0] // 0) . " to " . int($film->{ms}[-1] // 0) . " ms.");

# Decode only the box around the points, as raw RGB.
my ($x0, $y0) = ($px[0][0], $px[0][1]); my ($x1, $y1) = ($x0, $y0);
for (@px) { $x0 = $_->[0] if $_->[0] < $x0; $y0 = $_->[1] if $_->[1] < $y0; $x1 = $_->[0] if $_->[0] > $x1; $y1 = $_->[1] if $_->[1] > $y1 }
my ($bw, $bh) = ($x1 - $x0 + 1, $y1 - $y0 + 1);
open(my $p, '-|', 'ffmpeg', '-v', 'error', '-i', $f, '-vf', "format=rgb24,crop=$bw:$bh:$x0:$y0", '-fps_mode', 'passthrough', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-') or die;
binmode $p;
printf "%8s  %s\n", 'ms', join('  ', map { sprintf '%-9s', $_ } @pts);
my ($n, $prev, $last, $rows) = (0, '', '', 0);
my $size = $bw * $bh * 3;
while (read($p, my $buf, $size) == $size) {
    if ($want{$n}) {
        my $row = join '  ', map { my $i = (($_->[1] - $y0) * $bw + ($_->[0] - $x0)) * 3; sprintf '#%02x%02x%02x  ', unpack('C3', substr($buf, $i, 3)) } @px;
        $last = sprintf "%8d  %s\n", $film->{ms}[$n] + 0.5, $row;
        if ($every || $row ne $prev) { print $last; $rows++; $last = '' }
        $prev = $row;
    }
    $n++;
}
close $p;
print $last if $last;
print "(only frames where a color changed; --all prints every frame)\n" unless $every;
