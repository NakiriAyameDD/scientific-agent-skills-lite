#!/usr/bin/env python3
"""
Sync script for scientific-agent-skills-lite.
Fetches updates from upstream (K-Dense-AI/scientific-agent-skills),
updates the 53 curated scientific skills, and excludes all Life Sciences,
Physics/Astronomy/Quantum, Materials/Geoscience, and Productivity/Hardware skills.
"""

import os
import sys
import stat
import shutil
import subprocess
import json
import argparse
from pathlib import Path

UPSTREAM_REPO = "https://github.com/K-Dense-AI/scientific-agent-skills.git"

# The 53 curated skills to maintain and keep updated
CURATED_SKILLS = {
    # 1. Statistics, Experimental Design & Data Analysis (8)
    "statistical-analysis", "statistical-power", "statsmodels", "pymc",
    "scikit-survival", "pymoo", "experimental-design", "exploratory-data-analysis",

    # 2. Machine Learning, AI & Scientific Computing (19)
    "scikit-learn", "pytorch-lightning", "transformers", "torch-geometric",
    "networkx", "aeon", "timesfm-forecasting", "shap", "stable-baselines3",
    "pufferlib", "umap-learn", "simpy", "dask", "polars", "vaex",
    "zarr-python", "matlab", "sympy", "optimize-for-gpu",

    # 3. Scientific Visualization & Schematics (6)
    "scientific-visualization", "scientific-schematics", "matplotlib",
    "seaborn", "infographics", "generate-image",

    # 4. Scholarly Writing, Literature & Research Ops (20)
    "scientific-writing", "literature-review", "paper-lookup", "paperzilla",
    "citation-management", "pyzotero", "peer-review", "scholar-evaluation",
    "research-grants", "research-lookup", "venue-templates", "latex-posters",
    "scientific-slides", "scientific-brainstorming", "scientific-critical-thinking",
    "hypothesis-generation", "hypogenic", "what-if-oracle", "consciousness-council",
    "dhdna-profiler"
}

# Explicit blacklist of excluded skills
EXCLUDED_SKILLS = {
    # Life Sciences & Bio (81 items + new upstream bio/structural skills)
    "13c-metabolic-flux", "adaptyv", "alphagenome", "analytical-method-validation",
    "anndata", "arboreto", "benchling-integration", "bgpt-paper-search", "bids",
    "biopython", "bioservices", "bulk-rnaseq", "cellxgene-census",
    "clinical-decision-support", "clinical-reports", "cobrapy", "datamol",
    "deepchem", "deepspot-m", "deeptools", "depmap", "diffdock",
    "dnanexus-integration", "esm", "etetoolkit", "flowio", "folklore-variant-evidence",
    "geniml", "genomic-coordinates", "genomic-intelligence", "gget",
    "ginkgo-cloud-lab", "glycoengineering", "gtars", "histolab",
    "imaging-data-commons", "iso-standards-readiness", "labarchive-integration",
    "lamindb", "latchbio-integration", "matchms", "medchem",
    "molecular-dynamics", "molfeat", "ncats-arax", "neurokit2",
    "neuropixels-analysis", "nextflow", "omero-integration", "onekgpd",
    "ontology-term-resolution", "opentrons-integration", "pacsomatic",
    "paperclip", "pathml", "pathogen-variant-surveillance", "pathway-enrichment",
    "phylogenetics", "pkpd-modeling", "polars-bio", "primekg",
    "protocolsio-integration", "pydeseq2", "pydicom", "pyhealth",
    "pylabrobot", "pyopenms", "pysam", "pytdc", "rdkit",
    "relsa-severity-assessment", "rowan", "scanpy", "scikit-bio",
    "scvelo", "scvi-tools", "tamarind", "tiledbvcf", "torchdrug",
    "treatment-plans", "waypoint-bio", "flowkit", "nwb-conversion", "relion",

    # Physics, Astronomy & Quantum (8 items)
    "astropy", "qiskit", "cirq", "qutip", "pennylane", "fluidsim", "openpiv", "uncertainty-and-units",

    # Materials & Geoscience (3 items + new materials skills)
    "pymatgen", "geomaster", "geopandas", "pycalphad",

    # Productivity & Hardware (23 items)
    "pdf", "docx", "pptx", "pptx-posters", "xlsx", "markitdown", "liteparse",
    "markdown-mermaid-writing", "open-notebook", "datalad", "database-lookup",
    "exa-search", "parallel-web", "hugging-science", "modal", "get-available-resources",
    "lab-hardware-cad", "fictiv", "arbor", "autoskill", "pi-agent", "usfiscaldata",
    "market-research-reports"
}


def safe_rmtree(path: Path):
    """Safely remove directories on Windows/Linux, handling git read-only files."""
    if not path.exists():
        return

    def _handle_readonly(func, fpath, exc_info):
        try:
            os.chmod(fpath, stat.S_IWRITE)
            func(fpath)
        except Exception:
            pass

    try:
        shutil.rmtree(path, onerror=_handle_readonly)
    except Exception:
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "rd", "/s", "/q", str(path)], capture_output=True)


def clone_upstream(temp_dir: Path) -> bool:
    print(f"[*] Cloning upstream from {UPSTREAM_REPO}...")
    safe_rmtree(temp_dir)
    res = subprocess.run(
        ["git", "clone", "--depth", "1", UPSTREAM_REPO, str(temp_dir)],
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        print(f"[!] Git clone failed: {res.stderr}", file=sys.stderr)
        return False
    print("[+] Upstream cloned successfully.")
    return True


def sync(dry_run: bool = False):
    repo_root = Path(__file__).resolve().parents[1]
    temp_dir = repo_root / "temp_upstream"
    local_skills_dir = repo_root / "skills"

    try:
        if not clone_upstream(temp_dir):
            sys.exit(1)

        upstream_skills_dir = temp_dir / "skills"
        if not upstream_skills_dir.exists():
            print("[!] Upstream skills directory not found!", file=sys.stderr)
            sys.exit(1)

        upstream_skills = {
            d.name: d for d in upstream_skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        }

        print(f"[*] Found {len(upstream_skills)} skills in upstream repository.")

        synced_count = 0
        missing_count = 0
        new_candidates = []

        # 1. Update all curated skills
        for sname in sorted(CURATED_SKILLS):
            if sname in upstream_skills:
                target_skill_dir = local_skills_dir / sname
                if not dry_run:
                    safe_rmtree(target_skill_dir)
                    shutil.copytree(upstream_skills[sname], target_skill_dir)
                synced_count += 1
            else:
                print(f"[!] Warning: Curated skill '{sname}' was not found in upstream!")
                missing_count += 1

        # 2. Check for newly introduced upstream skills
        for sname, sdir in upstream_skills.items():
            if sname not in CURATED_SKILLS and sname not in EXCLUDED_SKILLS:
                new_candidates.append(sname)

        print("\n=== Sync Summary ===")
        print(f"Total upstream skills:     {len(upstream_skills)}")
        print(f"Curated skills updated:    {synced_count}")
        print(f"Curated skills missing:    {missing_count}")
        print(f"Total active local skills: {len(CURATED_SKILLS)}")

        if new_candidates:
            print(f"\n[*] Newly added upstream skills (pending review): {len(new_candidates)}")
            for c in sorted(new_candidates):
                print(f"  - {c}")
        else:
            print("\n[*] No new uncategorized upstream skills found.")

        # 3. Sync upstream version to plugin.json
        upstream_plugin_json = temp_dir / "plugin.json"
        local_plugin_json = repo_root / "plugin.json"
        if upstream_plugin_json.exists() and local_plugin_json.exists() and not dry_run:
            try:
                up_data = json.loads(upstream_plugin_json.read_text(encoding="utf-8"))
                loc_data = json.loads(local_plugin_json.read_text(encoding="utf-8"))
                if "version" in up_data:
                    old_ver = loc_data.get("version")
                    loc_data["version"] = up_data["version"]
                    local_plugin_json.write_text(json.dumps(loc_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    print(f"[+] Version aligned with upstream: {old_ver} -> {up_data['version']}")
            except Exception as e:
                print(f"[!] Notice: Could not sync version in plugin.json: {e}")

        if dry_run:
            print("\n[!] Dry run complete. No local files were modified.")
        else:
            print("\n[+] Sync completed successfully.")

    finally:
        if temp_dir.exists():
            print("[*] Cleaning up temporary upstream clone...")
            safe_rmtree(temp_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync updates from upstream scientific-agent-skills")
    parser.add_argument("--dry-run", action="store_true", help="Simulate sync without modifying files")
    args = parser.parse_args()
    sync(dry_run=args.dry_run)
