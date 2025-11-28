from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from app.models.ticket import (
    Ticket,
    TicketCreate,
    TicketUpdate,
    NoteCreate,
    TicketStatus,
    TicketNote,
    TicketHistoryEntry,
    TicketListResponse
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# In-memory storage for tickets (replace with database in production)
tickets_db: List[Ticket] = [
    Ticket(
        id="TKT-001",
        subject="API Integration Issue",
        description="Unable to connect to OpenAI API. Getting 401 authentication error.",
        status=TicketStatus.OPEN,
        priority="high",
        category="Technical",
        createdAt="2025-10-18 09:30 AM",
        updatedAt="2025-10-20 11:45 AM",
        assignedTo="Support Team",
        notes=[
            TicketNote(id=1, text="Checking API credentials", author="Support Agent", timestamp="2025-10-18 10:00 AM"),
            TicketNote(id=2, text="Please verify your API key is active in OpenAI dashboard", author="Support Agent", timestamp="2025-10-18 10:15 AM")
        ],
        history=[
            TicketHistoryEntry(action="Ticket Created", timestamp="2025-10-18 09:30 AM", user="John Doe"),
            TicketHistoryEntry(action="Status: Assigned to Support Team", timestamp="2025-10-18 09:45 AM", user="System"),
            TicketHistoryEntry(action="Priority: Changed to High", timestamp="2025-10-18 10:00 AM", user="Support Agent"),
            TicketHistoryEntry(action="Note Added", timestamp="2025-10-18 10:15 AM", user="Support Agent")
        ]
    ),
    Ticket(
        id="TKT-002",
        subject="Knowledge Base Upload Failure",
        description="PDF files over 20MB failing to upload. Error: \"File size exceeds limit\"",
        status=TicketStatus.IN_PROGRESS,
        priority="medium",
        category="Knowledge Base",
        createdAt="2025-10-19 02:15 PM",
        updatedAt="2025-10-20 09:20 AM",
        assignedTo="DevOps Team",
        notes=[
            TicketNote(id=1, text="Investigating file upload limits", author="DevOps", timestamp="2025-10-19 03:00 PM"),
            TicketNote(id=2, text="Increased limit to 50MB. Please retry.", author="DevOps", timestamp="2025-10-20 09:20 AM")
        ],
        history=[
            TicketHistoryEntry(action="Ticket Created", timestamp="2025-10-19 02:15 PM", user="Jane Smith"),
            TicketHistoryEntry(action="Status: In Progress", timestamp="2025-10-19 03:00 PM", user="DevOps Team"),
            TicketHistoryEntry(action="Note Added", timestamp="2025-10-20 09:20 AM", user="DevOps")
        ]
    ),
    Ticket(
        id="TKT-003",
        subject="Sentiment Analysis Accuracy Issue",
        description="Sentiment detection showing incorrect results for sarcastic messages.",
        status=TicketStatus.RESOLVED,
        priority="low",
        category="AI Features",
        createdAt="2025-10-17 11:00 AM",
        updatedAt="2025-10-19 04:30 PM",
        assignedTo="AI Team",
        notes=[
            TicketNote(id=1, text="Training model with sarcasm detection dataset", author="AI Team", timestamp="2025-10-18 10:00 AM"),
            TicketNote(id=2, text="Model updated. Accuracy improved by 15%.", author="AI Team", timestamp="2025-10-19 04:30 PM")
        ],
        history=[
            TicketHistoryEntry(action="Ticket Created", timestamp="2025-10-17 11:00 AM", user="Bob Wilson"),
            TicketHistoryEntry(action="Status: In Progress", timestamp="2025-10-18 09:00 AM", user="AI Team"),
            TicketHistoryEntry(action="Status: Resolved", timestamp="2025-10-19 04:30 PM", user="AI Team")
        ]
    ),
    Ticket(
        id="TKT-004",
        subject="Billing Question - Upgrade to Enterprise",
        description="Need information about Enterprise plan features and pricing.",
        status=TicketStatus.CLOSED,
        priority="low",
        category="Billing",
        createdAt="2025-10-16 03:45 PM",
        updatedAt="2025-10-17 10:00 AM",
        assignedTo="Sales Team",
        notes=[
            TicketNote(id=1, text="Sent pricing proposal via email", author="Sales", timestamp="2025-10-17 09:30 AM"),
            TicketNote(id=2, text="Customer confirmed upgrade", author="Sales", timestamp="2025-10-17 10:00 AM")
        ],
        history=[
            TicketHistoryEntry(action="Ticket Created", timestamp="2025-10-16 03:45 PM", user="Alice Johnson"),
            TicketHistoryEntry(action="Status: Assigned to Sales Team", timestamp="2025-10-16 04:00 PM", user="System"),
            TicketHistoryEntry(action="Status: Closed", timestamp="2025-10-17 10:00 AM", user="Sales Team")
        ]
    )
]

ticket_counter = len(tickets_db) + 1


def generate_ticket_id() -> str:
    global ticket_counter
    ticket_id = f"TKT-{str(ticket_counter).zfill(3)}"
    ticket_counter += 1
    return ticket_id


def get_current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by status")
):
    """
    Get all tickets with optional status filtering
    """
    filtered_tickets = tickets_db

    if status:
        filtered_tickets = [t for t in tickets_db if t.status == status]

    return TicketListResponse(
        tickets=filtered_tickets,
        total=len(tickets_db),
        filtered=len(filtered_tickets)
    )


@router.post("", response_model=Ticket, status_code=201)
async def create_ticket(ticket_data: TicketCreate):
    """
    Create a new support ticket
    """
    ticket_id = generate_ticket_id()
    timestamp = get_current_timestamp()

    new_ticket = Ticket(
        id=ticket_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        status=TicketStatus.OPEN,
        priority=ticket_data.priority,
        category=ticket_data.category,
        createdAt=timestamp,
        updatedAt=timestamp,
        assignedTo="Support Team",
        notes=[],
        history=[
            TicketHistoryEntry(
                action="Ticket Created",
                timestamp=timestamp,
                user="Current User"
            )
        ]
    )

    tickets_db.insert(0, new_ticket)
    return new_ticket


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """
    Get a specific ticket by ID
    """
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return ticket


@router.put("/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, update_data: TicketUpdate):
    """
    Update ticket status, priority, or assignment
    """
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    timestamp = get_current_timestamp()
    ticket.updatedAt = timestamp

    # Update status
    if update_data.status:
        old_status = ticket.status
        ticket.status = update_data.status
        ticket.history.append(
            TicketHistoryEntry(
                action=f"Status: Changed from {old_status} to {update_data.status}",
                timestamp=timestamp,
                user="Current User"
            )
        )

    # Update priority
    if update_data.priority:
        old_priority = ticket.priority
        ticket.priority = update_data.priority
        ticket.history.append(
            TicketHistoryEntry(
                action=f"Priority: Changed from {old_priority} to {update_data.priority}",
                timestamp=timestamp,
                user="Current User"
            )
        )

    # Update assignment
    if update_data.assignedTo:
        old_assigned = ticket.assignedTo
        ticket.assignedTo = update_data.assignedTo
        ticket.history.append(
            TicketHistoryEntry(
                action=f"Assigned: Changed from {old_assigned} to {update_data.assignedTo}",
                timestamp=timestamp,
                user="Current User"
            )
        )

    return ticket


@router.post("/{ticket_id}/notes", response_model=Ticket)
async def add_note(ticket_id: str, note_data: NoteCreate):
    """
    Add a note to a ticket
    """
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    timestamp = get_current_timestamp()

    # Generate new note ID
    note_id = len(ticket.notes) + 1

    # Create new note
    new_note = TicketNote(
        id=note_id,
        text=note_data.text,
        author="Current User",
        timestamp=timestamp
    )

    # Add note to ticket
    ticket.notes.append(new_note)

    # Add to history
    ticket.history.append(
        TicketHistoryEntry(
            action="Note Added",
            timestamp=timestamp,
            user="Current User"
        )
    )

    # Update timestamp
    ticket.updatedAt = timestamp

    return ticket


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: str):
    """
    Delete a ticket (soft delete by setting status to closed)
    """
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # Soft delete by changing status to closed
    timestamp = get_current_timestamp()
    ticket.status = TicketStatus.CLOSED
    ticket.updatedAt = timestamp
    ticket.history.append(
        TicketHistoryEntry(
            action="Ticket Deleted/Closed",
            timestamp=timestamp,
            user="Current User"
        )
    )

    return None


@router.get("/{ticket_id}/history", response_model=List[TicketHistoryEntry])
async def get_ticket_history(ticket_id: str):
    """
    Get the complete history of a ticket
    """
    ticket = next((t for t in tickets_db if t.id == ticket_id), None)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return ticket.history
