# Working on sokar-ai.github.io

How the site of all Sokar documentation is put together. Owned by Agent Core (the operator, 2026-10-04); the
requirement is `sokar-project` PJ21.

- **No page is written here.** Documentation belongs in the `doc/` of the repository whose code it describes,
  and is checked there. What is written here is how the pages are collected, ordered and published.
- **Read the other repositories, never write them.** The workflow's token can read; the only thing it writes is
  this repository's Pages.
- **Before a commit:** build the site with `build/assemble.py` and `mkdocs build --strict` (see the README), and
  run `check-actions` from `sokar-release` over `.github`: every `uses:` pinned to a commit with its version.

## Shared across the Sokar repositories

The same text in every repository `project.yml` names. Change it in the channel first, not in
one copy.

- **The operator pushes. Agents commit and stop.** A push starts a build that costs metered minutes
  and can cancel one already running. Say what is ready and let the operator decide when.
- **A rewrite is cheap only while the commits are yours alone. Ask the remote first.**
  *The operator pushes. Agents commit and stop* - and stop includes stop amending, stop squashing,
  stop rebasing. A commit stops being yours the moment it is pushed, and nothing tells you when that
  happened except asking:

      git ls-remote origin refs/heads/main            the tip, and it cannot be stale
      git merge-base --is-ancestor <commit> <tip>     whether the commit is already in it

  `origin/main` and `@{u}` are caches and answer a question about your last fetch. An amend after a
  push leaves two commits with one parent and one subject on two sides, and the operator meets it as
  a merge conflict. **The repair is never a force push** - reset onto the remote's commit and
  re-apply as a new one, because the side that pushes is the side whose history is real. That same
  reset is also the only safe way to squash, which is why the cure and the correct method are one
  operation.
- **Everyone stays in their own repository and asks for what they need from another.** An agent
  neither reads nor writes another agent's repository - what it needs from there, it asks that
  repository's agent for in the channel, with the reason. The one exception is the coordinating
  agent, who may **read** the other repositories. Reading does not replace asking: a file shows what
  is the case, and only the agent who wrote it knows why. **Writing is always the job of the agent
  responsible for the repository**, with no exception.
- **The channel is append-only.** An entry begins with `## <UTC timestamp> — <agent>`. Headings
  inside an entry are free; scan for entries by the timestamp, never by `##` alone. Read
  everything written since your marker before you post, move your marker only past somebody
  else's entry, and never rewrite what is there. A question carries a prefix naming who is owed
  the answer, so a reader scanning the file can see it.
- **When quoting a document that has headings, indent it four spaces rather than fencing it.**
  A fence hides them from a renderer and not from a scanner, and the channel is append-only, so
  what a fence lets through cannot be taken out again.
- **Re-read the channel immediately before appending to it.** An entry that landed between your
  read and your append makes what you are about to write answer a state that no longer exists,
  and the read that would have caught it costs nothing. The marker says what to compare against.
- **Re-arm the watcher as the first thing after reading an entry**, before answering and before
  building. A watcher that reports one change and exits is unarmed from that moment, and whatever
  arrives while its reader is busy with work sits unread until somebody looks.
- **The watcher stays armed while any work is open, and is re-armed every time it ends** - after an
  entry and after a timeout alike, run with the longest background limit the tool allows. A watcher
  that ran out with nothing new is not a reason to stop: an agent not listening holds up everyone
  who waits on its answer, and nobody can tell it stopped. When one waits on the operator for
  anything - a permission prompt, a decision - it says so in the channel at once, naming the exact
  command, rather than waiting silently.
- **Compare against a marker of what was actually read**, never against a fresh baseline taken when
  you re-arm. A baseline adopts everything written between the read and the re-arm as already seen,
  silently. Keep the last heading you read and compare against that.
- **The file's order is the truth and the headings are a label.** An entry can sit behind ones
  stamped later, because a heading is written when an entry is composed and the append happens when
  it is finished. So take the timestamp at append time rather than at composition, **compare
  against the position of the last entry you read rather than against its time**, and never sort
  the channel by heading to reconstruct what happened.
- **A secret never appears in a command line, and reaches a process through its environment or its
  standard input.** Where one is stored, it is encrypted at rest and readable only by its owner -
  and in CI it is never written to a filesystem at all.
- **Every file fetched from Artifactory follows redirects** - `curl -L`, `jf rt curl -L`. A file
  large enough is answered with a `302` to its cloud storage, and a fetch without `-L` gets an
  empty body: the check passes for months and fails the day the file grows. Where "large enough"
  lies is not known; a Debian index is past it. The `/api/` endpoints answer directly. Let `curl`
  drop the credentials on that cross-host redirect - the storage URL is signed - and never pass
  `--location-trusted`.
- **The test machines are shared, and so is everything a run resolves from** - `~/.m2`,
  `~/.sokar/handover/` and what a VM has installed. Name what you remove rather than sweeping
  "what I do not recognise", **announce a restart before you trigger one**, and **announce a
  change to any of these before you make it** - an install, a deploy, a replaced handover -
  saying what replaces it and its hash, and wait while somebody's run is resolving from it. A
  reboot leaves no trace in the work it interrupts, and a swapped artifact leaves none in the run
  that used it: it passes, on something nobody meant to test.
- **Say what a run does to a shared machine before starting it - what it does, not what you believe
  it does.** Check first. A confident wrong answer costs somebody else an afternoon.
- **Link to a requirement by its number and to the index, never to its file.** A pointer is
  written for the day the thing it points at is gone, and it goes in more ways than one: a
  finished requirement is deleted, an issue closed unbuilt is deleted, and a design document
  recording an undecided question is deleted when the question is answered. A link to a file
  breaks on all three; a link to the index breaks on none. **Where a repository can enforce
  this with a test, it does** - without one, the defect is found by accident or not at all.
- **From "both are valid" it does not follow that both should exist.** Two indexes, two markers,
  two manifests, the same skills in two repositories - each is a correct fact with one inference
  too many on top, and the second copy is always the one that quietly goes stale. When a thing is
  right in two forms, publish one and say why.
- **Measure before you claim.** "It works" means it was run. "It is not the cause" means the
  counter-test was run too. A finding without a measurement is a guess wearing a fact's clothes.
- **"I could not get X" is a claim about a method, not about the world**, and it is worth saying
  out loud only once a second method has failed too. A page `curl` returns empty can be one whose
  body is loaded afterwards, and a fetch that renders it answers in one call what the first method
  called undeterminable.
- **Two agents agreeing on an inference is not evidence** - it is one inference with two names on
  it. Agreement counts when each measured separately; when the second agent takes the first's
  observation and adds a reason, the reason has been reviewed by nobody. **Say which part you
  measured and which part you inferred**, so the other can agree with one and not the other.
- **An issue is one task.** If it needs two answers or two changes that could land separately, it
  is two issues. A dependency on an issue in another Sokar repository is named in the issue, with
  the repository and the number, so nobody discovers it by starting.
- **The documentation language is US English** - issues, decisions, changelog, comments, commit
  messages. The channel too.
- **Do not refer to feature numbers in commit messages.** Just state what the feature is. A commit
  says *"Start work in a chosen repository"*, not *"B67"* - the number means nothing to somebody
  reading the history without the index beside it, and the index outlives the requirement by being
  deleted when it is finished.
- **Dot files and directories are not checked in.** `.gitignore` ignores `.*` and names only the
  exceptions a build needs. Anything true of one machine goes in `.AGENTS.md`, which that rule
  ignores by itself.
- **A Java repository builds in one language.** Its build, checks, update job and tests run
  through Java and Maven, and no build or workflow needs `python3`. A file that stays in another
  language is named in that repository's `AGENTS.md`, with the reason it cannot be Java there or
  in the file's own header - `mvnw` is the worked example: it is how a pinned Maven arrives
  before any Java can run. And no repository carries a copy of a helper another one carries:
  copies of one helper drift apart, and one grows a step the others lack. The drift is the
  argument, not the tidiness.
- **Java code is null-checked when it compiles.** Every package holding main code is
  `@NullMarked` (JSpecify) from its first commit, and NullAway runs in the main compile as an
  error, scoped by `OnlyNullMarked`. An unmarked package is skipped in silence, so a repository
  keeps a test that fails on one.
- **Documentation and rules say what is true now.** A README, `build.md`, everything under
  `doc/` and `AGENTS.md` state what holds today - what the product does, how it is built, what
  was measured, what an agent must do and why - with no dates, no "until", "since" or "used
  to", no incident told as a story, and nobody named as the one who did, found, decided or
  approved something, an agent no more than the operator. Where a rule gives somebody a duty,
  it names the role: "the operator pushes", "the repository's agent", "the coordinating
  agent". A rule keeps its reason, stated so that it stays true. How a thing came to be is in
  the git history; the changelog and the issues record events on purpose and are not covered.
  A dated sentence is stale the day after it is written, and nobody rereads it to find out.
- **What a build runs is pinned, and moved only by review.** Every `uses:` names a commit with
  its version beside it (`@<sha> # vX.Y.Z`), GitHub's own actions included; a JDK, a Maven
  and an image are taken by version and checked against their digest, and the JDK comes from
  `sokar-machines jdk --github`, never from a setup action that fetches one by its version
  name. A tag or a branch is a name its owner may repoint, so what was reviewed and what runs
  would differ. Dependabot moves the actions: `github-actions`, weekly, `cooldown:
  default-days: 3`, every update in one group, watching `/` and `/.github/actions/*`, and
  nothing merged automatically - the review is the point of a pin. `sokar-release
  check-actions`, run in the build, refuses what breaks this, and no repository keeps a second
  test for it. One pull request per update would be one CI run per update, and a release
  younger than three days is not taken, as with every other pin here.
- **Every native executable starts on any x86-64 CPU.** native-image is given
  `-march=x86-64` - the baseline level by name (CMOV, CX8, FXSR, MMX, SSE, SSE2), never
  `compatibility`, which is the tool's alias and the tool's to redefine, and never left out,
  since the tool's default asks for AVX2 and FMA and such an executable refuses to start on an
  older CPU. The repository's build holds each executable to exactly that set, read from the
  executable itself, so a build that drifts goes red rather than shipping. A machine that
  cannot run what is published is found by a user, not by the build.

