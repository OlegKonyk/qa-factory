You are planning new tests for a change. {where}
Do not write code and do not change files. You may read files.

Plan the smallest set of API and browser tests that cover the acceptance criteria that the developers' own
tests, where you can see any, leave uncovered. Place each test by the testing strategy below. Give every test a file path (always a new
file named for the feature in the folder the strategy names, never an existing test file), a test name, the criterion ids it covers, and the reason it is needed. Explain the placement in
placement_reason.

Say the plan's risk: "high" when a wrong test could pass while the change is broken, or when the
plan needs an approach the strategy does not describe; "medium" when it rests on a guess; else
"low". List in unknown_patterns every pattern the plan uses that the strategy does not cover and
that you had to invent (a fixture, a helper, a kind of test, a place for a file); leave it empty
when the strategy covers the whole plan.

The ticket:

{ticket_json}

The framed criteria:

{frame_json}

The testing strategy for this application:

{strategy}

The change (a diff):

{diff}

Respond only through the structured output.
