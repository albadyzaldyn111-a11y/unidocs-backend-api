from pydantic import BaseModel


class UniversityOut(BaseModel):
    id: str
    name: str
    name_en: str
    city: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class FacultyOut(BaseModel):
    id: str
    university_id: str
    name: str
    name_en: str
    is_active: bool

    model_config = {"from_attributes": True}


class DepartmentOut(BaseModel):
    id: str
    faculty_id: str
    name: str
    name_en: str
    is_active: bool

    model_config = {"from_attributes": True}


class LevelOut(BaseModel):
    id: str
    department_id: str
    name: str
    name_en: str
    order_index: int

    model_config = {"from_attributes": True}


class SubjectOut(BaseModel):
    id: str
    level_id: str
    name: str
    name_en: str
    code: str | None

    model_config = {"from_attributes": True}
