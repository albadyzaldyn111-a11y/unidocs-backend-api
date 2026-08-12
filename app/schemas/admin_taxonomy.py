from pydantic import BaseModel


class UniversityCreate(BaseModel):
    name: str
    name_en: str
    city: str | None = None


class FacultyCreate(BaseModel):
    university_id: str
    name: str
    name_en: str


class DepartmentCreate(BaseModel):
    university_id: str
    faculty_id: str
    name: str
    name_en: str


class LevelCreate(BaseModel):
    university_id: str
    department_id: str
    name: str
    name_en: str
    order_index: int = 0


class SubjectCreate(BaseModel):
    university_id: str
    level_id: str
    name: str
    name_en: str
    code: str | None = None

class UniversityUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    city: str | None = None
    is_active: bool | None = None


class FacultyUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    is_active: bool | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    is_active: bool | None = None


class LevelUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    order_index: int | None = None


class SubjectUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    code: str | None = None
    is_active: bool | None = None
