from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Content(BaseModel):
    model_config = ConfigDict(extra='forbid')

    @field_validator('*', mode='before')
    @classmethod
    def safe_strings(cls, value, info):
        if isinstance(value, str):
            value = value.strip()
            if info.field_name in {'url', 'github', 'demo', 'scholar', 'orcid', 'linkedin'} and value:
                parsed = urlsplit(value)
                if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
                    raise ValueError('Links must be full HTTPS URLs without credentials.')
            if info.field_name == 'email' and value:
                if '@' not in value or any(c in value for c in '\r\n <>?&'):
                    raise ValueError('Enter a valid contact email.')
        return value


class Profile(Content):
    name: str = Field(min_length=2, max_length=100)
    role: str = Field(max_length=150)
    headline: str = Field(max_length=180)
    summary: str = Field(max_length=600)
    about: str = Field(max_length=4000)
    location: str = Field(max_length=100)
    email: str = Field(max_length=150)
    availability: str = Field(max_length=200)
    github: str = Field(max_length=500)
    scholar: str = Field(max_length=500)
    orcid: str = Field(max_length=500)
    linkedin: str = Field(max_length=500)
    education: str = Field(max_length=200)
    institution: str = Field(max_length=200)
    education_dates: str = Field(max_length=100)
    education_status: str = Field(max_length=300)
    thesis: str = Field(max_length=500)
    skills: str = Field(max_length=3000)
    problem_solving: str = Field(max_length=600)


class Project(Content):
    title: str = Field(min_length=2, max_length=200)
    category: Literal['Research', 'Engineering']
    role: str = Field(max_length=200)
    summary: str = Field(max_length=700)
    problem: str = Field(max_length=2000)
    approach: str = Field(max_length=4000)
    outcome: str = Field(max_length=2000)
    tags: str = Field(max_length=500)
    github: str = Field(default='', max_length=500)
    demo: str = Field(default='', max_length=500)
    featured: bool = False


class Publication(Content):
    title: str = Field(min_length=2, max_length=400)
    authors: str = Field(max_length=1200)
    venue: str = Field(max_length=400)
    year: int = Field(ge=2000, le=2100)
    status: Literal['Published', 'Submitted', 'In preparation']
    first_author: bool = False
    doi: str = Field(default='', max_length=250)
    url: str = Field(default='', max_length=600)
    summary: str = Field(default='', max_length=1200)

    @field_validator('doi')
    @classmethod
    def valid_doi(cls, value):
        if value and (not value.startswith('10.') or '/' not in value or any(c.isspace() for c in value)):
            raise ValueError('Use the DOI identifier, for example 10.1109/CONF.2026.12345.')
        return value


class Post(Content):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(max_length=500)
    tags: str = Field(max_length=400)
    date: str
    body: str = Field(min_length=1, max_length=100000)

    @field_validator('date')
    @classmethod
    def valid_date(cls, value):
        from datetime import date
        date.fromisoformat(value)
        return value


class Experience(Content):
    title: str = Field(min_length=2, max_length=200)
    organization: str = Field(max_length=200)
    dates: str = Field(max_length=100)
    summary: str = Field(max_length=2500)


class Award(Content):
    title: str = Field(min_length=2, max_length=250)
    year: int = Field(ge=2000, le=2100)
    summary: str = Field(max_length=1500)


SCHEMAS = {'project': Project, 'publication': Publication, 'post': Post,
           'experience': Experience, 'award': Award}

# The admin forms are derived from the same validation schema as stored content.
LONG_FIELDS = {'summary', 'about', 'skills', 'problem_solving', 'thesis', 'authors',
               'problem', 'approach', 'outcome', 'body', 'education_status'}


def form_fields(schema):
    result = []
    for name, field in schema.model_fields.items():
        choices = list(field.annotation.__args__) if getattr(field.annotation, '__origin__', None) is Literal else []
        result.append({'name': name, 'label': name.replace('_', ' ').title(),
                       'choices': choices, 'boolean': field.annotation is bool,
                       'number': field.annotation is int, 'long': name in LONG_FIELDS,
                       'required': field.is_required() and field.annotation is not bool})
    return result
