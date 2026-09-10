# Third-party notices and license scope

Apache-2.0 covers eligible original project code: `src/tts_workbench`, project
test fakes/tests, scripts, and original configuration/build/CI material. The
2026-09-10 owner decision confirms authority over that code and permits its
commercial reuse. It does not grant ownership of upstream material. Original
release documentation and factual evidence accompany the authorized public
code candidate; historical and third-party text retains its existing rights
and attribution. No blanket relicense of repository history is asserted.

No upstream library source or binary is vendored in the workbench wheel.
Dependencies are installed separately under their own terms. Their exact
versions, source URLs, and license declarations are recorded in
`docs/m7_dependency_audit.md` and `uv.lock`. Dependency notices embedded in
upstream wheels, including numerical-library and NVIDIA component notices,
must be retained with those packages. A project Apache license does not
replace them or authorize redistribution of an assembled runtime environment.

Meta's MMS/VITS checkpoints are attributed to Meta and the MMS project:

- `facebook/mms-tts-eng` at
  `c71de0fe7204c83f1c10820a7d696d0b450048ba`.
- `facebook/mms-tts-vie` at
  `b58928d033932a49aa8e3d6cf11625b25fe928d2`.
- Collection license/provenance:
  <https://huggingface.co/facebook/mms-tts/blob/44cc7fb408064ef9ea6e7c59130d88cac1274671/README.md>.
- Weight license: <https://creativecommons.org/licenses/by-nc/4.0/legalcode>.

Only registry metadata is distributed. Weights, caches, and generated audio
remain external. The project permits these registered checkpoints only for
local non-commercial inference. Their incomplete itemized training-data
lineage is not commercial clearance. Outputs are not automatically Apache
licensed, public domain, or cleared for commercial use.

The built-in English synthetic smoke fixture is original project test code.
The external Vietnamese fixture is attributed to Vietnam's National Assembly
and the Government Portal's 2013 Constitution source. Its source and legal
basis are audited in `docs/license_matrix.md`; neither its raw text nor the
source PDF is bundled. Historical references to other implementations or
checkpoint candidates are citations, not included or approved software/models.
