"""SQLAlchemy 2.0 ORM models for all 6 tables (per spec section 6.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


ProjectStatus = Literal["draft", "ready", "annotating", "exported"]
ExportFormat = Literal["coco", "yolo", "voc", "ls_json"]
SplitName = Literal["train", "val", "test"]
AnnotationSource = Literal["user", "geco2_pending", "geco2_accepted", "user_edited"]
ChatRole = Literal["user", "assistant", "tool", "system"]


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workspace_path: Mapped[str] = mapped_column(String, nullable=False)
    source_folder: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(String, nullable=False)
    export_format: Mapped[ExportFormat | None] = mapped_column(String, nullable=True)
    train_ratio: Mapped[float] = mapped_column(default=0.7)
    val_ratio: Mapped[float] = mapped_column(default=0.15)
    test_ratio: Mapped[float] = mapped_column(default=0.15)
    split_seed: Mapped[int] = mapped_column(Integer, default=42)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    images: Mapped[list[Image]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    labels: Mapped[list[Label]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','ready','annotating','exported')",
            name="ck_project_status",
        ),
    )


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    abs_path: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    split: Mapped[SplitName] = mapped_column(String, nullable=False)
    index_in_project: Mapped[int] = mapped_column(Integer, nullable=False)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="images")
    annotations: Mapped[list[Annotation]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("split IN ('train','val','test')", name="ck_image_split"),
        Index("ix_image_project_index", "project_id", "index_in_project"),
        Index("ix_image_project_split", "project_id", "split"),
    )


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="labels")
    annotations: Mapped[list[Annotation]] = relationship(back_populates="label")

    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_label_project_name"),)


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    label_id: Mapped[int] = mapped_column(
        ForeignKey("labels.id", ondelete="RESTRICT"), nullable=False
    )
    x1: Mapped[int] = mapped_column(Integer, nullable=False)
    y1: Mapped[int] = mapped_column(Integer, nullable=False)
    x2: Mapped[int] = mapped_column(Integer, nullable=False)
    y2: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    source: Mapped[AnnotationSource] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    image: Mapped[Image] = relationship(back_populates="annotations")
    label: Mapped[Label] = relationship(back_populates="annotations")

    __table_args__ = (
        CheckConstraint(
            "source IN ('user','geco2_pending','geco2_accepted','user_edited')",
            name="ck_annotation_source",
        ),
        Index("ix_annotation_image", "image_id"),
        Index("ix_annotation_label", "label_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChatRole] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tool_call_id: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint(
            "role IN ('user','assistant','tool','system')",
            name="ck_chat_role",
        ),
        Index("ix_chat_project_created", "project_id", "created_at"),
    )


class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    label_id: Mapped[int] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"), nullable=False
    )
    exemplar_x1: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_y1: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_x2: Mapped[int] = mapped_column(Integer, nullable=False)
    exemplar_y2: Mapped[int] = mapped_column(Integer, nullable=False)
    n_predictions: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_pred_project_created", "project_id", "created_at"),)
