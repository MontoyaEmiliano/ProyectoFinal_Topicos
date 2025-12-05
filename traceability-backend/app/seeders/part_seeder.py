from app.models.models import Part, PartStatus
from sqlalchemy.orm import Session


def seed_parts(db: Session):
    if db.query(Part).count() > 0:
        print("Parts already seeded.")
        return

    parts = [
        Part(id="PZA-001", tipo_pieza="X1", lote="L001", status=PartStatus.IN_PROCESS),
        Part(id="PZA-002", tipo_pieza="X1", lote="L001", status=PartStatus.COMPLETED),
        Part(id="PZA-003", tipo_pieza="X2", lote="L002", status=PartStatus.SCRAPPED),
        Part(id="PZA-004",tipo_pieza="X2",lote="L002",status=PartStatus.IN_PROCESS,num_retrabajos=1,),
        Part(id="PZA-005", tipo_pieza="X3", lote="L003", status=PartStatus.IN_PROCESS),
    ]

    db.add_all(parts)
    db.commit()
    print("Parts seeded successfully!")

