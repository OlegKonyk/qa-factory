# Step 4 verify needs a person

Who: Oleg

Question: Approve the stub tests?

Context:

```json
{
  "tests": 0
}
```

Answer by writing $S/runs/restate-stub-1/answer.json, for example {"approved": true, "by": "Oleg", "note": ""}

Under Restate, answer over HTTP instead of writing the file:

    curl -X POST http://localhost:8080/factory/restate-stub-1/answer -H 'content-type: application/json' -d '{"approved": true, "by": "Oleg", "note": ""}'
