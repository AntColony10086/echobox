from echobox_app.domain.annotations import AnnotationDTO


def test_dto_to_dict() -> None:
    dto = AnnotationDTO(
        id=42,
        image_id=1,
        label_id=2,
        label_name="crack",
        label_color="#000",
        x1=10,
        y1=20,
        x2=30,
        y2=40,
        score=0.9,
        source="geco2_accepted",
        version=1,
    )
    d = dto.to_dict()
    assert d["id"] == 42
    assert d["bbox"] == [10, 20, 30, 40]
    assert d["score"] == 0.9
    assert d["source"] == "geco2_accepted"
    assert d["label"] == {"id": 2, "name": "crack", "color": "#000"}


def test_dto_from_db_model() -> None:
    from datetime import datetime

    from echobox_app.db.models import Annotation, Label

    label = Label(id=2, project_id=1, name="crack", color="#000", created_at=datetime.now())
    ann = Annotation(
        id=42,
        image_id=1,
        label_id=2,
        x1=10,
        y1=20,
        x2=30,
        y2=40,
        score=0.9,
        source="user",
        version=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    ann.label = label

    dto = AnnotationDTO.from_db(ann)

    assert dto.id == 42
    assert dto.label_name == "crack"
