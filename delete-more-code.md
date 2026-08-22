# delete more code: cleaning up ai slop in a real codebase

> Most of it was AI-generated code that worked fine but nobody understood anymore. Why removing 40% of our codebase made everything better.

Source: https://mohammad.page/delete-more-code.html

---

November 25, 2025

last month i deleted about 40% of our codebase. not refactored. deleted.
most of it was ai-generated code that worked fine but nobody understood
anymore. it was the most productive week i've had all year.

## how we got here

when you're building fast, you accumulate stuff. features that made sense
six months ago. abstractions built "for later." modules copied from other
projects that you never fully understood.

if you use ai to write code (yes, we vibe code), this compounds fast.
ai-generated code is verbose, over-abstracted, and full of defensive
checks for things that won't happen. it works, but it's slop. and it
piles up faster than you realize.

that's the trap. it works, so you keep it. but collectively, it's friction.
every new feature navigates around old decisions. every bug could be in
twelve different places. onboarding someone means explaining why there
are two user services.

## what i actually deleted

**unused feature flags.** we had 22 feature flags. 7 of them
hadn't been touched in months. some pointed to code that no longer existed.
i deleted the flags and the dead code paths they guarded. nothing broke.

**the "flexible" config system.** we built a system that could
configure anything from anywhere: environment variables, config files,
database, remote service. in practice, we used environment variables for
everything. i ripped out the abstraction and hardcoded the one pattern we
actually use. 400 lines gone.

**defensive code for impossible states.** null checks on things
that can't be null. try/catch blocks around code that can't throw. validation
for data that's already validated upstream. years of "just to be safe"
accumulating into noise.

**tests for deleted features.** the features were gone but the
tests remained, mocking things that no longer existed, passing because they
tested nothing.

**the second way of doing things.** we had two http clients,
two logging wrappers, two date formatting utilities. i picked one of each
and migrated everything. the "worse" option was often fine. the consistency
mattered more than the choice.

## what happened after

build times dropped. not because of caching tricks or parallelization.
just less code to compile.

bugs got easier to find. fewer places to look. fewer interactions to reason
about. i fixed a bug last week by reading the entire module. that used to
be impossible.

new features got faster to ship. not because of new tooling. because i
could hold the relevant context in my head. no more "wait, which service
handles this again?"

## how to know what to delete

search for the last meaningful change. if a file hasn't been touched in
six months except for bulk reformatting or dependency updates, question
whether it needs to exist.

look for code that's "handling" things. error handlers that log and rethrow.
wrappers that add nothing. adapters between things that could talk directly.
every layer has a cost.

find the features nobody uses. check your analytics. talk to users. that
export-to-pdf feature you spent two weeks on? if nobody clicks it, delete it.
you can rebuild it if someone asks. they won't ask.

delete the abstraction before you need the variation. we had a plugin system
for exactly one plugin. i inlined it. if we ever need a second plugin, i'll
spend an hour extracting the abstraction. probably won't happen.

## especially if you vibe code

most ai-generated code is slop. it works. it passes the tests. it does
what you asked. but it's not good code. depending on which model you're
using, you get varying degrees of over-engineering, weird patterns, and
abstractions that make sense to no one.

the trap is that it works. you prompt, it generates, you run it, it runs.
so you ship and move on. but you didn't write it, so you don't fully own
it mentally. you don't know why it made that choice. you don't notice the
three extra layers it added. the slop accumulates.

this is why periodic rewrites matter. not refactors. rewrites. take a
module that ai helped you build three months ago and actually read it.
understand what it does. then rewrite the logic yourself, cleaner, with
the context you have now. you'll delete half the code and the result will
be better.

i've found that for every hour of ai-assisted coding, i need to spend
fifteen minutes actively cleaning up. not just deleting dead code, but
rewriting the logic that survived. the helper functions that are
unnecessarily generic. the error handling for impossible states. the
class hierarchies that exist because the model learned from java codebases.

ai makes you faster at generating code. it doesn't make you faster at
having good code. that part is still on you. and it requires regularly
going back and fixing what the model got wrong.

every line of code is a liability. the only way to have zero bugs in a feature is to not have that feature.

## the fear

the hardest part isn't finding code to delete. it's convincing yourself it's
okay. what if we need it later? what if there's a bug and we need to debug
the old path? what if someone asks for that feature back?

that's what version control is for. the code isn't gone. it's in git. you
can resurrect it in minutes. in two years of doing this, i've restored
deleted code exactly once.

the fear of deleting is almost always worse than the reality.

## a ritual

i've started doing this quarterly now. one week, no new features. just
deletion. i go through the codebase file by file and ask: does this need
to exist? is this the only way to do this thing? when was the last time
a human read this?

it feels unproductive. your commit count goes negative. you're not shipping
anything visible. but the next three months feel lighter. the codebase
becomes something you can understand again, not just navigate.

the best code you write might be the code you delete.

[← olderAlways Be Building](https://mohammad.page/always-be-building.html)
[newer →The AI Hangover](https://mohammad.page/the-ai-hangover.html)

[← back to blog](https://mohammad.page/blog.html)
