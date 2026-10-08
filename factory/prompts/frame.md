You are framing a ticket for QA on this repository. You are in the working tree of the changed code.
Do not write code and do not change files. You may read files to understand the application.

For each acceptance criterion in the ticket:
- restate it as something a test can check, in one sentence;
- say whether it is testable by a test (testable);
- name the surface a test would use: "api" (REST calls), "browser" (what a person sees and clicks),
  "unit" (internal code only), or "none" (not testable).
Then list ambiguities: anything in the ticket a test writer would have to guess.

The ticket:

{ticket_json}

The change under test (a diff, may be empty):

{diff}

Respond only through the structured output. The summary is two or three plain sentences.
