import pytest
from echobox_app.db.models import (
    Annotation,
    Base,
    ChatMessage,
    Image,
    Label,
    PredictionRun,
    Project,
)
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Session:
    from echobox_app.db.session import make_engine

    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_project(session: Session) -> None:
    p = Project(
        name="test-proj",
        workspace_path=".data/projects/1",
        source_folder="/orig",
        status="draft",
    )
    session.add(p)
    session.commit()

    assert p.id is not None
    assert p.train_ratio == 0.7
    assert p.val_ratio == 0.15
    assert p.test_ratio == 0.15
    assert p.split_seed == 42


def test_image_belongs_to_project(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id,
        filename="00001.jpg",
        abs_path="/abs/00001.jpg",
        width=640,
        height=480,
        split="train",
        index_in_project=0,
        source_path="/orig/img1.jpg",
    )
    session.add(img)
    session.commit()

    assert img.project_id == p.id
    assert img.project.name == "x"
    assert p.images[0].filename == "00001.jpg"


def test_label_unique_per_project(session: Session) -> None:
    from sqlalchemy.exc import IntegrityError

    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    session.add(Label(project_id=p.id, name="crack", color="#e63946"))
    session.commit()

    session.add(Label(project_id=p.id, name="crack", color="#000000"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_annotation_with_label(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id,
        filename="00001.jpg",
        abs_path="/x",
        width=10,
        height=10,
        split="train",
        index_in_project=0,
        source_path="/orig",
    )
    label = Label(project_id=p.id, name="crack", color="#000")
    session.add_all([img, label])
    session.flush()
    ann = Annotation(
        image_id=img.id,
        label_id=label.id,
        x1=10,
        y1=20,
        x2=30,
        y2=40,
        source="user",
        version=1,
    )
    session.add(ann)
    session.commit()

    assert ann.id is not None
    assert ann.score is None
    assert ann.image.filename == "00001.jpg"
    assert ann.label.name == "crack"


def test_chat_message(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    msg = ChatMessage(project_id=p.id, role="user", content="hello")
    session.add(msg)
    session.commit()

    assert msg.id is not None


def test_prediction_run(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id,
        filename="00001.jpg",
        abs_path="/x",
        width=10,
        height=10,
        split="train",
        index_in_project=0,
        source_path="/orig",
    )
    label = Label(project_id=p.id, name="crack", color="#000")
    session.add_all([img, label])
    session.flush()
    run = PredictionRun(
        project_id=p.id,
        image_id=img.id,
        label_id=label.id,
        exemplar_x1=1,
        exemplar_y1=2,
        exemplar_x2=3,
        exemplar_y2=4,
        n_predictions=5,
        elapsed_ms=123,
    )
    session.add(run)
    session.commit()

    assert run.id is not None
    assert run.error is None


def test_cascade_delete_project(session: Session) -> None:
    p = Project(name="x", workspace_path="x", source_folder="x", status="draft")
    session.add(p)
    session.flush()
    img = Image(
        project_id=p.id,
        filename="00001.jpg",
        abs_path="/x",
        width=10,
        height=10,
        split="train",
        index_in_project=0,
        source_path="/orig",
    )
    session.add(img)
    session.commit()
    session.delete(p)
    session.commit()

    assert session.query(Image).count() == 0
