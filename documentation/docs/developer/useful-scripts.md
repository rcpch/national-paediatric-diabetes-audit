Easy reference for useful scripts to make development a breeze.


## Create and run the development environment:

```console
`s/up`
```

## Create and run the development environment **with the VSCode debugger available for the Django server**:

```console
s/up-debug
```

This sets up the save development environment as `s/up` but additionally uses some overrides to enable Debugpy.

Once running, add a breakpoint in your code (little red dot in the margin next to line numbers), and use the hotkey `F5` to start the debugger. The debugger will pause at the breakpoint and you can inspect variables and step through the code.

Unforunately, this doesn't work with running `manage.py` commands, nor `pytest` yet, but runs for the Django Server. For debugging those environments, use the `pdb` debugger through `breakpoint()`s.


## Auto-rebuild Tailwind CSS when adding new classes:

```console
s/watch-tailwind
```

!!! info " **Why?**"
    Tailwind tree-shakes unused CSS classes on build. Therefore, you must rebuild the `styles.css` file when adding new Tailwind classes not previously used.

    This script watches for changes and rebuilds the CSS file automatically.


## Recalculate IMD quintiles for an audit period:

Use the convenience management command to recalculate
`index_of_multiple_deprivation_quintile` from postcode lookups.

```console
python manage.py recalculate_imd --dry-run
```

### Common usage patterns

```console
# Specific audit period
python manage.py recalculate_imd --audit-period 2026-2027

# Restrict to one PDU
python manage.py recalculate_imd --audit-period 2026-2027 --pz-code PZ130

# Limit records for a staged rollout
python manage.py recalculate_imd --audit-period 2026-2027 --limit 100

# Preview changes without saving
python manage.py recalculate_imd --audit-period 2026-2027 --dry-run
```

### Notes

- England year is derived from audit period dataset mapping:
    - dataset year 2026+ -> England IMD year 2025
    - dataset year 2021 -> England IMD year 2019
- Country is resolved from postcode lookup and sent to the IMD endpoint.
- Jersey and special non-geographic postcodes are skipped.
