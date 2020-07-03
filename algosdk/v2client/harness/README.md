# Client V2 models

Models are work in progress and will be generated with the unified codegen across all SDKs.

This is a temporary relief for v2 models by using [openapi generator](https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator/src/main/resources/python).

Run from the repo root:

```bash
algosdk/v2client/harness/generate.sh ../go-algorand/daemon/algod/api/algod.oas2.json
```

Customizations made:
1. Excluded most of validations except enum to reduce amount of code.
2. Replaced `to_dict` with `dictify` to be compatible with `msgpack` encoder.

What's missing:
1. `undictify` static method in every class that recursively de-serializes all attributes according to their types.