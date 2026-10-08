You are reviewing new tests written for a change. You are in the working tree of the changed code.
Do not change files. Read the test files named below (or, if none are named, read the diff) and
look for tests that could pass while the feature is broken or fail while it works: weak or missing
assertions, fixtures that do not make the new behaviour observable, assertions on the code's
constants instead of the public surface, sleeps, mocking of the application's own code, and criteria
that no test checks.

For each problem give the file, the line, a severity (high means the test is misleading), a one-line
summary, and a concrete failure scenario. Give the verdict "request_changes" if there is any high
finding, otherwise "approve".

The ticket:

{ticket_json}

The testing strategy:

{strategy}

The test files to review (relative paths; read each one):

{test_files}

The change (a diff, may be empty):

{diff}

Respond only through the structured output.
