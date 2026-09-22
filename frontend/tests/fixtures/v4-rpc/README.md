# Frozen V4 browser RPC fixture

`responses.json` is a recorded response set from the production PALINODE app
reading the frozen Studionet V4 contract at
`0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`.

It is test-only data. It is not application state, a deployment source, or a
replacement for live canonical reads. `capture-v4-rpc-fixture.mjs` records the
bounded `gen_call` responses while visiting the V4 evidence, revocation,
recovery, authority, graph, activity, proof, integrate, and documentation
routes.
