import uuid
from datetime import datetime
from typing import Literal
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from danswer.auth.users import current_user
from danswer.db.chat import create_new_chat_message
from danswer.db.chat import get_chat_message
from danswer.db.chat import get_chat_messages_by_session
from danswer.db.chat import get_chat_session_by_id
from danswer.db.chat import get_or_create_root_message
from danswer.db.engine import get_session
from danswer.db.models import User

router = APIRouter(prefix="/messages")


Role = Literal["user", "assistant"]


class MessageContent(BaseModel):
    type: Literal["text"]
    text: str


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4()}")
    object: Literal["thread.message"] = "thread.message"
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    thread_id: str
    role: Role
    content: list[MessageContent]
    file_ids: list[str] = []
    assistant_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[dict] = None


class CreateMessageRequest(BaseModel):
    role: Role
    content: str
    file_ids: list[str] = []
    metadata: Optional[dict] = None


class ListMessagesResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[Message]
    first_id: str
    last_id: str
    has_more: bool


@router.post("/{thread_id}/messages")
def create_message(
    thread_id: str,
    message: CreateMessageRequest,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> Message:
    user_id = user.id if user else None

    try:
        chat_session = get_chat_session_by_id(
            chat_session_id=uuid.UUID(thread_id),
            user_id=user_id,
            db_session=db_session,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat session not found")

    root_message = get_or_create_root_message(
        chat_session_id=chat_session.id, db_session=db_session
    )

    new_message = create_new_chat_message(
        chat_session_id=chat_session.id,
        parent_message=root_message,
        message=message.content,
        # TODO: fix
        token_count=len(message.content.split()),  # Simple token count estimation
        message_type=message.role,
        db_session=db_session,
        prompt_id=None,
    )

    return Message(
        id=str(new_message.id),
        thread_id=thread_id,
        role="user",
        content=[MessageContent(type="text", text=message.content)],
        file_ids=message.file_ids,
        metadata=message.metadata,
    )


@router.get("/{thread_id}/messages")
def list_messages(
    thread_id: str,
    limit: int = 20,
    order: Literal["asc", "desc"] = "desc",
    after: Optional[str] = None,
    before: Optional[str] = None,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> ListMessagesResponse:
    user_id = user.id if user else None

    try:
        chat_session = get_chat_session_by_id(
            chat_session_id=uuid.UUID(thread_id),
            user_id=user_id,
            db_session=db_session,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = get_chat_messages_by_session(
        chat_session_id=chat_session.id,
        user_id=user_id,
        db_session=db_session,
    )

    # Apply filtering based on after and before
    if after:
        messages = [m for m in messages if str(m.id) > after]
    if before:
        messages = [m for m in messages if str(m.id) < before]

    # Apply ordering
    messages = sorted(messages, key=lambda m: m.id, reverse=(order == "desc"))

    # Apply limit
    messages = messages[:limit]

    data = [
        Message(
            id=str(m.id),
            thread_id=thread_id,
            role="user" if m.message_type == "user" else "assistant",
            content=[MessageContent(type="text", text=m.message)],
            created_at=int(m.time_sent.timestamp()),
        )
        for m in messages
    ]

    return ListMessagesResponse(
        data=data,
        first_id=str(data[0].id) if data else "",
        last_id=str(data[-1].id) if data else "",
        has_more=len(messages) == limit,
    )


@router.get("/{thread_id}/messages/{message_id}")
def retrieve_message(
    thread_id: str,
    message_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> Message:
    user_id = user.id if user else None

    try:
        chat_message = get_chat_message(
            chat_message_id=message_id,
            user_id=user_id,
            db_session=db_session,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Message not found")

    return Message(
        id=str(chat_message.id),
        thread_id=thread_id,
        role="user" if chat_message.message_type == "user" else "assistant",
        content=[MessageContent(type="text", text=chat_message.message)],
        created_at=int(chat_message.time_sent.timestamp()),
    )


class ModifyMessageRequest(BaseModel):
    metadata: dict


@router.post("/{thread_id}/messages/{message_id}")
def modify_message(
    thread_id: str,
    message_id: int,
    request: ModifyMessageRequest,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> Message:
    user_id = user.id if user else None

    try:
        chat_message = get_chat_message(
            chat_message_id=message_id,
            user_id=user_id,
            db_session=db_session,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Message not found")

    # Update metadata
    chat_message.metadata = request.metadata
    db_session.commit()

    return Message(
        id=str(chat_message.id),
        thread_id=thread_id,
        role="user" if chat_message.message_type == "user" else "assistant",
        content=[MessageContent(type="text", text=chat_message.message)],
        created_at=int(chat_message.time_sent.timestamp()),
        metadata=request.metadata,
    )
