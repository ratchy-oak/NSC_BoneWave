# BoneWave contributor guidance

- Treat every signal, label, prediction, and metric in this repository as simulated.
- Never describe synthetic metrics as clinical or medical accuracy.
- Preserve group-aware splitting by `sample_id`; train/test sample overlap must remain zero.
- Run `python -m compileall .`, `pytest -q`, and `python scripts/run_pipeline.py` after material changes.
- The application is a research proof-of-concept, not a medical device and not a substitute for a doctor or X-ray.
