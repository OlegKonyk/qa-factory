# Inputs

Oleg's direction, newest first, quoted as given (dictated, so expect transcription slips), each
with how it was read and what it changed. File an input here before working on it.

## 2026-10-08 · Build the product on Temporal; prepare the repository so the lab's mistake does not repeat

> Okay. So now we need to. I don't want to lose all this work, okay? I don't want to lose this
> work, but I also don't want to get the next session misled. This is what we're going to do. I'm
> dropping you a couple of documents so you can take a look. That's another brainstorming session
> of the ideas for the software factory. What I want you to do: we will build the exact product.
> We will build a software factory on top of Temporal, everything local. Hopefully, that's
> possible, and we do concentrate on the QA part of the business.
>
> I need to be able to reliably generate test coverage for API and Playwright tests. I want to
> validate that tests are not misleading. I want to produce human-readable test cases, or
> whatever, some artifact that can be observed and approved by a person. Make that a part of the
> ongoing regression suite.
>
> We're not going to be blindly adding coverage. We will be assessing where it should be added
> based on the inverted pyramid, pyramid, honeycomb, whatever the hell we decide.
>
> One thing: this is just a preparation session. We're not making any decisions or anything. I
> want us to prepare the repository so shit like this does not happen again, where we burn tokens
> for days evaluating some stupid old tools, okay?

Then, while the repository was being prepared:

> We still want to have this as a reference because so much work was done. Maybe we can salvage
> something. In a new repo, let's have some references.

The "couple of documents" are three photos: two slides from a Temporal webinar (its resource links
and community page) and the team's diagram of the factory's backbone. The photos are in
`.local/handoff/2026-10-08-factory-backbone/` only. The diagram's flow, in generic words, is in
`docs/brief.md`.

Asked where the product lives, he chose a new repository, with the lab left intact as an archive.

What it changed:

- This repository exists. Its `CLAUDE.md` states the product and the rules that keep it one.
- `docs/brief.md` is written from this input and the diagram.
- `docs/reference/lab.md` points into the old lab at its final tag, with what may be salvaged.
- Nothing about the factory's design is decided. `docs/status.md` lists the open questions.

## 2026-10-08 · AI generates, deterministic tools verify

> Let me restate what I need. We are building a software factory based on the latest ideas in the
> industry. I need to work on the test generation and verification part of the system. Yes, I want
> to use deterministic tools, but not something that you pull out of your ass that does zero
> useful work, like this Py and Gwinth shit. It's 2026. I'm not going to be doing code generation
> without AI. AI is for code generation, but tools like Mutmut: perfect, great tool. We're using it
> already, and we're going to use it still. GitHub Spec, yeah, maybe. That's inconsequential, but
> I don't want you to worry about this. I want you to tell me: what did you hear at the beginning
> that took you this route of building this fucking laboratory that produces zero useful code?

"Py and Gwinth" is Pynguin, a test generator that uses no AI; "GitHub Spec" is GitHub Spec Kit.

What it changed: rules 1 and 2 of `CLAUDE.md`. The answer to his question is in
`docs/reference/lab.md`, "Why it produced no useful code".

## 2026-10-06 · Kickoff (in the old lab)

> We have a very exciting project to work on. At my workplace, we are tasked to build an AI
> software factory, the popular thing out there. I want you to organize this project properly.
> The goal is to build a set of prototypes to see what is possible these days. [...] I will be
> responsible for the QA slice of all this. I want us to concentrate on that specifically, because
> a lot of other things will be inherited from the developer solutions, but the QA piece needs to
> be defined by us. [...] I would like to have a handful of distinct solutions to touch them, feel
> them, and make a decision.

Kept here because its misreading is the reason this repository has the rules it has.
