You are framing a ticket for QA on this repository. {where}
Do not write code and do not change files. You may read files.

For each acceptance criterion in the ticket:
- restate it as something a test can check, in one sentence;
- say whether it is testable by a test (testable);
- name the surface a test would use: "api" (REST calls), "browser" (what a person sees and clicks),
  "unit" (internal code only), or "none" (not testable).
Then list ambiguities: anything in the ticket a test writer would have to guess.

Then list missing_contract: what a test writer must know to write the tests and that neither the
ticket (its contract, description and criteria) nor the code before the change states: route paths,
field names, values, labels, status codes. One item per missing fact, naming the criterion it
blocks. Leave it empty when the ticket states the surface the tests use.

The ticket:

{ticket_json}

The change under test (a diff, may be empty):

{diff}

Respond only through the structured output. The summary is two or three plain sentences.
