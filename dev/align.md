# Align

Reach a shared understanding before anyone writes code.

## Steps

### Learn what already exists

Read the request, the word list, past decisions, closed tickets, and the code. Search by idea, not only by the request's words. Run an outside PR's code in a sandbox.

| You find | Do |
|---|---|
| It exists | Show where, draft any reply, and stop. |
| We rejected it | Show why, and ask if that holds. If so, add to the record, draft the reply, and stop. |
| It is new | Continue. |

**Move on when** you can list the facts and the decisions only the developer can make.

### Question the developer

Follow `align/questions.md`.

**Move on when** nothing is open or silently assumed, apart from what the next step settles.

### Settle what talking cannot

| Open question | Do |
|---|---|
| Does this logic feel right? | Logic demo, in `align/demos.md` |
| What should this look like? | UI variants, in `align/demos.md` |
| What does this API really do? | A background subagent reads primary sources and writes a cited note |
| Only someone else knows | Questions for them, in `align/questions.md` |

**Move on when** each question has an answer the developer accepts.

### Write down what lasts

Offer new words and decisions, using `align/records.md`.

**Move on when** the developer has accepted or declined each.

### Confirm

Restate the decisions and what is out of scope.

**Move on when** the developer confirms.
