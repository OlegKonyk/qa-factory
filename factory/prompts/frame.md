You are framing a ticket for QA on this repository. {where}
Do not write code and do not change files. You may read files.

For each acceptance criterion in the ticket:
- restate it as something a test can check, in one sentence;
- say whether it is testable by a test (testable);
- name the surface a test would use: "api" (REST calls), "browser" (what a person sees and clicks),
  "unit" (internal code only), or "none" (not testable).
Then list ambiguities: anything in the ticket a test writer would have to guess.

Then list missing_contract: the public contract the change introduces that the ticket does not
state and that a test would have to guess: a new route path, a new parameter or field name, the
values it accepts, a new label, a status code. One item per missing fact, naming the criterion it
blocks. It is a readiness check on the ticket, not a list of what the tests need: do not list how
a test would find an element, set up its data, or read a response, nor anything the code before
the change already defines (existing routes, fields, templates and behaviour a writer can read).
Leave it empty when the ticket's contract, description or criteria name the new surface, even if
details remain ambiguous; those go under ambiguities.

The ticket:

{ticket_json}

The change under test (a diff, may be empty):

{diff}

Respond only through the structured output. The summary is two or three plain sentences.
