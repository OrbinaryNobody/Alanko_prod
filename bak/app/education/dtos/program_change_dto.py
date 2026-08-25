from typing import Any


def proposal_payload(proposal) -> dict[str, Any]:
    return {
        "id": proposal.id,
        "program_id": proposal.program_id,
        "author_id": proposal.author_id,
        "status": proposal.status,
        "base_snapshot": proposal.base_snapshot,
        "proposed_snapshot": proposal.proposed_snapshot,
        "author_comment": proposal.author_comment,
        "reviewer_comment": proposal.reviewer_comment,
        "reviewed_by": proposal.reviewed_by,
        "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
        "reviewed_at": proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
    }