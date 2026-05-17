import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state_manager import StateManager, JobStatus, Stage


def test_state_manager():
    sm = StateManager("data/test.db")

    # Create job
    job_id = sm.create_job("chocolate chip cookies")
    print(f"Created job: {job_id}")
    assert job_id > 0

    # Verify initial state
    job = sm.get_job_status(job_id)
    assert job["status"] == "pending"
    assert job["stage"] == "init"
    print(f"Initial status: {job['status']} / {job['stage']}")

    # Update status and stage
    sm.update_job(job_id, status=JobStatus.PROCESSING, stage=Stage.RESEARCH)
    job = sm.get_job_status(job_id)
    assert job["status"] == "processing"
    assert job["stage"] == "research"
    print(f"Updated status: {job['status']} / {job['stage']}")

    # Save and retrieve artifact
    sm.save_artifact(job_id, "article_title", "Best Chocolate Chip Cookies")
    sm.save_artifact(job_id, "recipe_data", {"servings": 24, "prep_time": 15})

    title = sm.get_artifact(job_id, "article_title")
    recipe = sm.get_artifact(job_id, "recipe_data")
    assert title == "Best Chocolate Chip Cookies"
    assert recipe["servings"] == 24
    print(f"Artifacts saved: title='{title}', recipe servings={recipe['servings']}")

    # Update metadata
    sm.update_job(job_id, metadata={"wp_post_id": 42, "slug": "chocolate-chip-cookies"})
    meta = sm.get_job_metadata(job_id)
    assert meta["wp_post_id"] == 42
    print(f"Metadata: {meta}")

    # Log error
    sm.log_error(job_id, "content_generation", "APIError", "Rate limit exceeded", retry_count=1)
    print("Error logged")

    # List jobs
    jobs = sm.list_jobs()
    assert any(j["id"] == job_id for j in jobs)
    print(f"Total jobs in DB: {len(jobs)}")

    # Complete the job
    sm.update_job(job_id, status=JobStatus.COMPLETED, stage=Stage.COMPLETE)
    job = sm.get_job_status(job_id)
    assert job["status"] == "completed"
    print(f"Final status: {job['status']} / {job['stage']}")

    sm.close()
    print("\n✅ StateManager all checks passed!")


if __name__ == "__main__":
    test_state_manager()
