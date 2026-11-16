#!/usr/bin/perl
# jobcheck.pl '<job lines>': exit 0 when every command in the job is a $S (vmx) call, so nothing else (a build, a
# sleep, a polling loop) can run while the guest is held. Commands after a pipe (| grep, | head) may filter output.
# A sleep inside $S sh is refused too: it holds the guest for a guessed time.
# Otherwise prints why, for the first command that breaks a rule, and exits 1.
use strict; use warnings;
my $s = shift // '';
my ($q, $cur, $pipe, @seg) = ('', '', 0);
for (my $i = 0; $i < length $s; $i++) {
    my $c = substr($s, $i, 1);
    if ($q eq "'") { $q = '' if $c eq "'"; $cur .= $c; next }
    if ($c eq '\\') { $cur .= substr($s, $i, 2); $i++; next }
    if ($q eq '"') { $q = '' if $c eq '"'; $cur .= $c; next }
    if ($c eq "'" || $c eq '"') { $q = $c; $cur .= $c; next }
    my $two = substr($s, $i, 2);
    if ($two eq '&&' || $two eq '||') { push @seg, [$cur, $pipe]; ($cur, $pipe) = ('', 0); $i++; next }
    if ($c eq ';' || $c eq "\n") { push @seg, [$cur, $pipe]; ($cur, $pipe) = ('', 0); next }
    if ($c eq '|') { push @seg, [$cur, $pipe]; ($cur, $pipe) = ('', 1); next }
    if ($c eq '&') {
        my $prev = $i ? substr($s, $i - 1, 1) : ''; my $next = substr($s, $i + 1, 1);
        if ($prev eq '>' || $prev eq '<' || $next eq '>') { $cur .= $c; next }
        print "vmx: a job may only run \$S commands. Not allowed: & (a background command).\n"; exit 1;
    }
    $cur .= $c;
}
push @seg, [$cur, $pipe];
for (@seg) {
    my ($t, $p) = @$_; $t =~ s/^\s+|\s+$//g;
    next if $t eq '' || $p;
    if ($t =~ /^(\$S|"\$S"|\$\{S\})(\s|$)/) {
        next unless ($t =~ /^\S+\s+sh\s/ && $t =~ /\bsleep\b/) || $t =~ /^\S+\s+\S*\/sleep(\s|$)/;
        print "vmx: a job may not sleep in the guest ($t). It holds the guest for a guessed time. To click and then look once the screen settles, use \$S film <app> <out.png> 'xy X,Y' 'xy X,Y' 'key NAME': it waits until each action settles, then takes a shot.\n";
        exit 1;
    }
    print "vmx: a job may only run \$S commands (| grep and | head may filter them). Not allowed: $t. Build, copy files, and wait on the host before the job.\n"; exit 1;
}
exit 0;
