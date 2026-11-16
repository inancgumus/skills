# filmlib.pl: what frames.pl and pixels.pl share. Reads a film from vmx film on the host with ffprobe and ffmpeg.
use strict; use warnings;

sub die2 { print STDERR "$_[0]\n"; exit 2 }

# Options shared by both: --from MS, --to MS, --rect x,y,w,h, --out FILE. Returns (hashref, @rest).
sub opts {
    my %o; my @rest;
    while (@_) {
        my $a = shift;
        if ($a =~ /^--(from|to)$/) { my $k = $1; my $v = shift // ''; $v =~ /^\d+$/ or die2("$a needs whole milliseconds of film time"); $o{$k} = $v }
        elsif ($a eq '--rect') { my $v = shift // ''; $v =~ /^\d+,\d+,\d+,\d+$/ or die2("--rect needs x,y,w,h in whole screen points"); $o{rect} = [split /,/, $v] }
        elsif ($a eq '--out') { $o{out} = shift // die2("--out needs a file") }
        else { push @rest, $a }
    }
    return (\%o, @rest);
}

sub need_ffmpeg { for (qw(ffmpeg ffprobe)) { system("command -v $_ >/dev/null 2>&1") == 0 or die2("vmx: $_ is not on the host. Install it (brew install ffmpeg).") } }

# The film: pixel size, frame times in ms (presentation order, so index = ffmpeg's frame number n), and the screen
# area it shows (from <film>.area, written by vmx film), with pixels per point.
sub film {
    my $f = shift;
    -f $f or die2("vmx: no film at $f");
    open(my $p, '-|', 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', $f) or die;
    my ($w, $h) = split /,/, (<$p> // ''); close $p;
    $w && $h or die2("vmx: $f is not a film ffprobe can read");
    chomp $h;
    open($p, '-|', 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time', '-of', 'csv=p=0', $f) or die;
    my @t = sort { $a <=> $b } map { chomp; /^[\d.]+$/ ? $_ * 1000 : () } <$p>; close $p;
    my %film = (file => $f, w => $w, h => $h, ms => \@t);
    if (open(my $a, '<', "$f.area")) {
        my $l = <$a> // ''; close $a;
        if ($l =~ /^(\d+),(\d+),(\d+),(\d+)/) { @film{qw(ax ay aw ah)} = ($1, $2, $3, $4); $film{scale} = $w / $3 }
    }
    print STDERR "vmx: $f has no $f.area (films from before this version), so points count from the film's top left corner, in points of the film, not of the screen.\n" unless defined $film{ax};
    return \%film;
}

# A still picture: pixel size and the screen area it shows. A film's last frame (<film>.png) uses <film>.area. A picture
# without one counts its own pixels as points: 1 pixel per point (a `shot`), 2 for an @2x name.
sub picture {
    my $f = shift;
    -f $f or die2("vmx: no picture at $f");
    open(my $p, '-|', 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', $f) or die;
    my ($w, $h) = split /,/, (<$p> // ''); close $p;
    $w && $h or die2("vmx: $f is not a picture ffprobe can read");
    chomp $h;
    my %pic = (file => $f, w => $w, h => $h, scale => ($f =~ /\@2x\.\w+$/ ? 2 : 1));
    (my $base = $f) =~ s/\.png$//i;
    for my $area ("$f.area", "$base.area") {
        open(my $a, '<', $area) or next;
        my $l = <$a> // ''; close $a;
        if ($l =~ /^(\d+),(\d+),(\d+),(\d+)/) { @pic{qw(ax ay aw ah)} = ($1, $2, $3, $4); $pic{scale} = $w / $3; last }
    }
    return \%pic;
}

# A screen point (or rect) to film pixels. Without <film>.area the numbers count as points of the film itself.
sub to_px {
    my ($film, $x, $y) = @_;
    my $s = $film->{scale} // 2; my ($ox, $oy) = ($film->{ax} // 0, $film->{ay} // 0);
    my ($px, $py) = (int(($x - $ox) * $s), int(($y - $oy) * $s));
    ($px >= 0 && $py >= 0 && $px < $film->{w} && $py < $film->{h}) or
        die2("vmx: $x,$y is outside the film" . (defined $film->{ax} ? " (it shows the screen area $film->{ax},$film->{ay},$film->{aw},$film->{ah})" : '') . '.');
    return ($px, $py);
}

# Frame numbers whose time lies in [from, to].
sub pick { my ($film, $o) = @_; my $t = $film->{ms}; grep { $t->[$_] >= ($o->{from} // 0) && $t->[$_] <= ($o->{to} // 9e9) } 0 .. $#$t }

1;
