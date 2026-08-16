from pydantic import BaseModel, Field


class UniversityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)
    city: str | None = Field(default=None, max_length=120)


class UniversityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_en: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class FacultyCreate(BaseModel):
    university_id: str
    name: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)


class FacultyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_en: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class DepartmentCreate(BaseModel):
    university_id: str
    faculty_id: str
    name: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_en: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class LevelCreate(BaseModel):
    university_id: str
    department_id: str
    name: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)
    order_index: int = 0


class LevelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_en: str | None = Field(default=None, min_length=2, max_length=255)
    order_index: int | None = None


class SubjectCreate(BaseModel):
    university_id: str
    level_id: str
    name: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)
    code: str | None = Field(default=None, max_length=64)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    name_en: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, max_length=64)


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
