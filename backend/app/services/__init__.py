"""Service layer: modular, replaceable components of the PlantMind pipeline.

Each service exposes a small interface so demo implementations can be swapped
for real ones (trained CV model, Neo4j, vector DB, hosted LLM) without
rewriting the application.
"""
