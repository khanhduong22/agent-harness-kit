"""The ACT-IDENTITY family of stage-B gates, gathered behind one call.

`verify_all.stage_b` used to import the six modules itself; they live here so the
orchestrator stays an orchestrator. Every module is stdlib, reads the file plus its
manifest, and prints N-A when its feature is undeclared -- so cuts that never opted in
take exactly the path they took before this family existed.
"""
from verify_act_delta import stage_results as act_delta_rows
from verify_act_delta_chip import stage_results as delta_chip_rows
from verify_legend_fact import stage_results as legend_rows
from verify_retired_ghost import stage_results as ghost_rows
from verify_role_lens import stage_results as role_lens_rows
from verify_tier_identity import stage_results as identity_rows

# Order matters only for the printed table: identity first, then what changed,
# then what is drawn about the change (ghosts, chip, lens), then the legend's count.
FAMILY = (identity_rows, act_delta_rows, ghost_rows, delta_chip_rows,
          role_lens_rows, legend_rows)


def act_family_rows(html_text, manifest):
    """Run every act-family gate; returns the concatenated stage rows."""
    rows = []
    for stage in FAMILY:
        rows += stage(html_text, manifest)
    return rows
