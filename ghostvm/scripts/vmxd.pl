#!/usr/bin/perl
# vmxd: runs vmx commands inside the guest's GUI session. vmx starts it once through GhostTools exec, so it and
# everything it runs keep GhostTools' screen recording and accessibility permissions. After that, vmx talks to
# it over ssh only: it writes <id>.cmd (a shell script) into the queue folder, and vmxd runs it and writes
# <id>.out, <id>.err and <id>.rc. This avoids GhostTools exec, which can hang 30 s per call (GhostVM issue #268).
use strict; use warnings; use POSIX ();
my $q = shift // '/tmp/.vmx-q';
mkdir $q;
open my $p, '>', "$q/pid" or die; print $p "$$\n"; close $p;
$SIG{CHLD} = 'IGNORE';
POSIX::setsid();
while (1) {
    for my $cmd (glob "$q/*.cmd") {
        (my $id = $cmd) =~ s/\.cmd$//;
        rename $cmd, "$id.run" or next;
        my $pid = fork;
        next unless defined $pid;
        if ($pid == 0) {
            open STDIN, '<', '/dev/null'; open STDOUT, '>', "$id.out"; open STDERR, '>', "$id.err";
            my $rc = system '/bin/sh', "$id.run";
            $rc = $rc == -1 ? 127 : ($rc & 127 ? 128 + ($rc & 127) : $rc >> 8);
            open my $r, '>', "$id.rc.t"; print $r "$rc\n"; close $r; rename "$id.rc.t", "$id.rc";
            POSIX::_exit(0);
        }
    }
    select undef, undef, undef, 0.005;
}
