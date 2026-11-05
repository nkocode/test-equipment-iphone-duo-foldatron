# Working agreements

- Use Pipenv for dependency management and running Python commands.
- Follow PEP 8 for Python source, with 79-character lines.
- Ask for confirmation before adding new production dependencies.
- Keep the installable Python package under `src/foldbench/`.
- Run `pipenv run lint`, `pipenv run test`, and `pipenv run schema` after
  code changes. Keep `openapi.json` synchronized with the application.
- Simulation is the default. Preserve commissioning lockouts and distinguish
  software checks from physical validation.
