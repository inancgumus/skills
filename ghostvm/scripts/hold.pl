#!/usr/bin/perl
# hold.pl DIR CALL TOKEN: wait until this caller may use the guest, then return with the guest lock held on fd 9.
#   DIR    per-VM state folder: lock (flock file), lease (token, start, last call), wait/ (one file per waiting caller)
#   CALL   what is being run, for the messages other agents see
#   TOKEN  the caller's lease token, or empty
# Order: callers go strictly in the order they started waiting. While another agent's lease is active, everyone else
# waits. A lease ends 45 s after its last call ended, or 120 s after it started. Exit 0 = go (prints "lease" on stdout
# when the caller owns the active lease); 75 = still busy after 90 s; 76 = the caller's lease has ended.
use strict; use warnings; use Fcntl qw(:flock); use Time::HiRes qw(time sleep);
my ($dir, $call, $token) = @ARGV; $token //= '';
my ($IDLE, $MAX, $WAIT) = (45, 120, 90);
open(my $f, '>>&=9') or die "hold: no fd 9\n";
mkdir "$dir/wait";
my $me = sprintf '%s/wait/%.3f-%d', $dir, time, getppid;
my $t0 = time; my $said = 0;

sub lease {    # (token, start, last) of the active lease, or ()
    open(my $l, '<', "$dir/lease") or return ();
    my ($t, $s, $last) = split ' ', (<$l> // ''); close $l;
    return () unless $t && $s && $last;
    return () if time - $last > $IDLE || time - $s > $MAX;
    return ($t, $s, $last);
}
sub older_waiter {    # a live caller that started waiting before us
    for my $w (sort glob "$dir/wait/*") {
        last if $w ge $me;
        my ($pid) = $w =~ /-(\d+)$/;
        if ($pid && kill 0, $pid) { return $w } else { unlink $w }
    }
    return;
}
sub who { open(my $w, '<', "$dir/who") or return 'another agent'; my $x = <$w> // ''; chomp $x; $x }

while (1) {
    if (flock($f, LOCK_EX | LOCK_NB)) {
        my @l = lease();
        my $mine = @l && $token ne '' && $l[0] eq $token;
        if ($token ne '' && !$mine) {
            unlink $me;
            print STDERR "vmx: your lease has ended (45 s after its last call, or 120 s after it started). Run your steps as one \$S job, or take a new lease.\n";
            exit 76;
        }
        if ((!@l || $mine) && ($mine || !older_waiter())) {
            unlink $me;
            printf STDERR "vmx: got the guest after %d s.\n", time - $t0 if $said;
            print "lease\n" if $mine;
            exit 0;
        }
        flock($f, LOCK_UN);
    }
    if (!-e $me) { open(my $w, '>', $me); close $w; }
    if (!$said) {
        my @l = lease();
        my $why = @l ? sprintf('%s holds a lease on it (ends within %d s)', who(), ($l[2] + $IDLE < $l[1] + $MAX ? $l[2] + $IDLE : $l[1] + $MAX) - time) : who() . ' is using it';
        print STDERR "vmx: waiting for the guest: $why.\n"; $said = 1;
    }
    if (time - $t0 > $WAIT) {
        unlink $me;
        print STDERR "vmx: the guest is still busy after $WAIT s (" . who() . "). Run the same call again as a background shell call (Claude Code: run_in_background) and keep working until it ends.\n";
        exit 75;
    }
    sleep 0.2;
}
