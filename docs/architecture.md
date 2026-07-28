# Workbench architecture — rescope milestone 1

The current vertical slice establishes a metadata control plane. It does not
implement the future local service.

```text
public repository
  configs/models/registry.yaml
             |
             v
  strict schema + policy validation
             |
             +--> models validate / models list
             |
             +--> MMS smoke adapter --> external artifact root
                                      generated WAV + future run manifest

external artifact root
  model cache / weights / generated audio / future benchmark artifacts
```

The registry, license matrix, environment report, and artifact boundary remain
separate controls:

- the registry decides which immutable artifacts are eligible for scoped use;
- the license matrix records the supporting audit and limitations;
- environment detection establishes what the local machine can execute; and
- the external boundary prevents weights and generated audio from entering Git.

Future milestones may add provider-neutral inference adapters, benchmark/QC
reports, and a bounded local API. No application layer may embed White Hmong
normalization or capability rules while NV-001 through NV-008 remain deferred
**[NV]**.
