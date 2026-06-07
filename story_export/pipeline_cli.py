"""CLI for the deterministic KidStory build pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from story_export.pipeline import BuildPipelineError, build_story, create_build_plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, generate assets, and export a KidStory archive",
    )
    parser.add_argument("story_dir", type=Path, help="Story directory, e.g. stories/name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate sources and print the asset plan without generating files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate assets even when output files already exist",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Generate and verify assets without writing the final ZIP",
    )
    args = parser.parse_args()

    try:
        if args.dry_run:
            plan = create_build_plan(args.story_dir)
            _print_plan(plan)
            if any(issue.is_error for issue in plan.issues):
                sys.exit(1)
            return

        print(f"EXPORT: {args.story_dir}")
        print("Phase 1/5: Validate sources ........ [RUN]")
        summary = build_story(
            args.story_dir,
            force=args.force,
            skip_export=args.skip_export,
        )
    except BuildPipelineError as exc:
        print("[FAIL]")
        print()
        print(exc)
        print()
        print("STOPPED. Fix the issue, then re-run:")
        print(f"  uv run python build_story.py {args.story_dir}")
        sys.exit(1)

    print("Phase 1/5: Validate sources ........ [OK]")
    print(
        "Phase 2/5: Generate covers ......... "
        f"[OK] ({summary.generated_images} generated, {summary.skipped_images} skipped)"
    )
    thumbnail_status = "generated" if summary.generated_thumbnail else "skipped"
    print(f"  Thumbnail: {thumbnail_status}")
    print(
        "Phase 3/5: Generate audio .......... "
        f"[OK] ({summary.generated_audio} generated, {summary.skipped_audio} skipped)"
    )
    print("Phase 4/5: Verify assets ........... [OK]")
    if args.skip_export:
        print("Phase 5/5: Create ZIP .............. [SKIP]")
        return
    result = summary.export_result
    if result is None:
        raise AssertionError("export result missing after build")
    print("Phase 5/5: Create ZIP .............. [OK]")
    print()
    print("EXPORT COMPLETE")
    print(f"  Archive:   {result.zip_path}")
    print(f"  Pack UUID: {result.pack_uuid}")
    print(f"  Size:      {result.archive_size:,} bytes")


def _print_plan(plan) -> None:
    print(f"DRY RUN: {plan.story_dir}")
    print(f"Title: {plan.title}")
    print()
    if plan.issues:
        print("Issues:")
        for issue in plan.issues:
            print(f"  [{issue.severity}] {issue.path}: {issue.message}")
        print()
    print(f"Images referenced: {len(plan.image_tasks)}")
    for task in plan.image_tasks:
        status = "present" if task.output_path.exists() else "missing"
        print(f"  - {task.filename}: {status}")
    print(f"Audio referenced: {len(plan.audio_tasks)}")
    for task in plan.audio_tasks:
        status = "present" if task.output_path.exists() else "missing"
        print(f"  - {task.filename}: {status} <- {task.source_path}")
    thumbnail_status = "present" if plan.thumbnail_task.output_path.exists() else "missing"
    print(f"Thumbnail: {thumbnail_status}")


if __name__ == "__main__":
    main()
