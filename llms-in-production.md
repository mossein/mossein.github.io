# llms in production: lessons from shipping rag at nasdaq

> Hard-won lessons from shipping LLM features to real users. The stuff that isn't in the tutorials.

Source: https://mohammad.page/llms-in-production.html

---

November 11, 2025

i've spent the last few years building llm features at two companies. first
at nasdaq on an entity research copilot, then at retellio where i built
the entire ai pipeline from scratch. here's what i wish someone had told
me before i started.

the hard part isn't getting the llm to work. it's getting it to work reliably, every time, at 3am, when you're asleep.

## the demo trap

every llm demo looks magical. you paste some text, it generates something
impressive, everyone claps. then you try to ship it.

suddenly you're dealing with prompts that work 90% of the time (which means
they fail for 1 in 10 users), latency spikes that make your ui feel broken,
and costs that scale faster than your runway. the gap between "working demo"
and "production feature" is where most projects die.

## what actually matters

after shipping llm features to thousands of users, here's what i actually
spend my time on:

**structured outputs.** don't let the model free-write. force
json. validate schemas. if the model returns malformed data, retry with
the error message in context. this alone fixed 80% of our reliability issues.

**prompt versioning.** treat prompts like code. version them.
a/b test them. never edit a prompt in production without knowing you can
roll back in 30 seconds.

**graceful degradation.** what happens when openai is down?
when you hit rate limits? when the response takes 45 seconds? your feature
should still work, even if it's worse. fallbacks aren't optional.

**cost controls.** set hard limits. alert on anomalies. one
infinite loop with gpt-4 can burn through your monthly budget in hours.
ask me how i know.

## the rag trap

everyone wants to build rag (retrieval-augmented generation). shove your
docs into a vector db, retrieve relevant chunks, feed them to the llm.
sounds simple.

it's not. retrieval quality is everything, and it's hard to measure. your
embeddings might find "semantically similar" content that's actually useless
for the question. chunking strategy matters more than you think. and when
retrieval fails silently, the llm just hallucinates confidently.

what helped us: treat retrieval as a separate system with its own metrics.
log what you retrieve. sample and review. build evaluation sets. don't just
trust the vibes.

## observability is non-negotiable

you need to see every request: the input, the prompt, the retrieval results,
the model output, the latency, the cost. not aggregates. individual requests.
when something goes wrong (and it will), you need to replay exactly what
happened.

we log everything to a structured store. every llm call has a trace id that
links back to the user action that triggered it. when someone reports a bad
output, i can pull up the exact prompt and context in seconds.

## start smaller than you think

your first llm feature shouldn't be an autonomous agent that handles complex
multi-step workflows. ship something constrained. a summarizer. a classifier.
something where wrong outputs are annoying but not catastrophic.

once you've built the infrastructure (the observability, the fallbacks, the
cost controls) then you can get ambitious. but don't skip the boring stuff
to build the cool stuff. the boring stuff is what lets the cool stuff work.

## the actual competitive advantage

here's the thing: everyone has access to the same models. gpt-5.1, claude 4.5,
gemini 3. they're commodities. the advantage isn't the model.

it's the data you have, the ux you build around it, and the reliability of
your system. a mediocre model with great retrieval, smart fallbacks, and
sub-second latency will beat a frontier model wrapped in a fragile demo
every time.

that's what nobody tells you: the llm is the easy part.

[← olderFrom Calls to Clarity: Shipping Insight Podcasts at Retellio](https://mohammad.page/retellio-insight-podcasts.html)
[newer →Always Be Building](https://mohammad.page/always-be-building.html)

[← back to blog](https://mohammad.page/blog.html)
