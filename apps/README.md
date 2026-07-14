# Applications

The Gradio client is deferred until the inference API exists. UI code must call
the shared normalization/inference package and must never embed a second
normalizer or load private recordings.
