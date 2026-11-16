# settle.pl TICK START T0: after an action that started at epoch START (s), wait until the picture changes and then
# stays still for 0.3 s. film.swift touches TICK on every real pixel change. Prints the result in film time (ms from T0).
use Time::HiRes qw(time sleep stat);
my ($tick, $start, $t0) = @ARGV;
my $m = sub { (stat $tick)[9] };
while ($m->() < $start) {
    if (time - $start > 2) { print "NO CHANGE in 2 s"; exit }
    sleep 0.01;
}
my $first = $m->();
while (1) {
    my $last = $m->();
    if (time - $last >= 0.3) { printf "first change %d ms, last change %d ms", $first * 1000 - $t0, $last * 1000 - $t0; exit }
    if (time - $start > 30) { printf "first change %d ms, STILL CHANGING 30 s later", $first * 1000 - $t0; exit }
    sleep 0.01;
}
